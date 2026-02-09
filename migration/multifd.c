/*
 * Multifd common code
 *
 * Copyright (c) 2019-2020 Red Hat Inc
 *
 * Authors:
 *  Juan Quintela <quintela@redhat.com>
 *
 * This work is licensed under the terms of the GNU GPL, version 2 or later.
 * See the COPYING file in the top-level directory.
 */

#include "qemu/osdep.h"
#include "qemu/cutils.h"
#include "qemu/iov.h"
#include "qemu/rcu.h"
#include "exec/target_page.h"
#include "sysemu/sysemu.h"
#include "exec/ramblock.h"
#include "qemu/error-report.h"
#include "qapi/error.h"
#include "ram.h"
#include "migration.h"
#include "migration/misc.h"
#include "migration-stats.h"
#include "savevm.h"
#include "socket.h"
#include "tls.h"
#include "qemu-file.h"
#include "trace.h"
#include "multifd.h"

#include "qemu/yank.h"
#include "io/channel-socket.h"
#include "yank_functions.h"

/* Multiple fd's */

#define MULTIFD_MAGIC 0x11223344U
#define MULTIFD_VERSION 1

typedef struct {
    uint32_t magic;
    uint32_t version;
    unsigned char uuid[16]; /* QemuUUID */
    uint8_t id;
    uint8_t unused1[7];     /* Reserved for future use */
    uint64_t unused2[4];    /* Reserved for future use */
} __attribute__((packed)) MultiFDInit_t;

struct {
    MultiFDSendParams *params;

    /* multifd_send() body is not thread safe, needs serialization */
    QemuMutex multifd_send_mutex;

    /*
     * Global number of generated multifd packets.
     *
     * Note that we used 'uintptr_t' because it'll naturally support atomic
     * operations on both 32bit / 64 bits hosts.  It means on 32bit systems
     * multifd will overflow the packet_num easier, but that should be
     * fine.
     *
     * Another option is to use QEMU's Stat64 then it'll be 64 bits on all
     * hosts, however so far it does not support atomic fetch_add() yet.
     * Make it easy for now.
     */
    uintptr_t packet_num;
    /*
     * Synchronization point past which no more channels will be
     * created.
     */
    QemuSemaphore channels_created;
    /* send channels ready */
    QemuSemaphore channels_ready;
    /*
     * Have we already run terminate threads.  There is a race when it
     * happens that we got one error while we are exiting.
     * We will use atomic operations.  Only valid values are 0 and 1.
     */
    int exiting;
    /* multifd ops */
    MultiFDMethods *ops;
} *multifd_send_state;

static MultiFDSendData *multifd_ram_send;

static int multifd_ram_payload_alloc(MultiFDPages_t *pages, Error **errp)
{
    ERRP_GUARD();

    /*
     * This will change when we stop exchanging the "offset" pointer
     * with main thread.
     */
    uint32_t page_count = multifd_ram_pages_per_work_count();
    uint32_t page_size = multifd_ram_page_size();

    pages->offset = g_try_new0(ram_addr_t, page_count);
    if (!pages->offset) {
        error_setg(errp, "Could not allocate pages->offset");
        return -1;
    }

    if (!migrate_use_hash()) {
        return 0;
    }

    if (cache_hash_is_batch(hash_cache)) {
        cache_hash_pool_init(hash_cache, page_count,
                             &pages->batch_context);
        pages->matched = g_try_new0(bool, page_count);
        if (!pages->matched) {
            error_setg(errp, "Could not allocate pages->matched");
            goto payload_fail;
        }
    }
    pages->digest = g_try_malloc0(cache_hash_item_size(hash_cache));
    if (!pages->digest) {
        error_setg(errp, "Could not allocate pages->digest");
        goto payload_fail;
    }

    pages->cached = g_try_new0(void*, page_count);
    if (!pages->cached) {
        error_setg(errp, "Could not allocate pages->cached");
        goto payload_fail;
    }
    for (int i = 0; i < page_count; i++) {
         pages->cached[i] = g_try_malloc0(page_size);
         if (!pages->cached[i]) {
             error_setg(errp, "Could not allocate one of pages->cached");
             goto payload_fail;
         }
    }

    return 0;

 payload_fail:
    if (pages->cached) {
        for (int i = 0; i < page_count; i++) {
            g_clear_pointer(&pages->cached[i], g_free);
        }
        g_clear_pointer(&pages->cached, g_free);
    }

    g_clear_pointer(&pages->digest, g_free);
    g_clear_pointer(&pages->matched, g_free);
    g_clear_pointer(&pages->offset, g_free);

    return -1;
}

static void multifd_ram_payload_free(MultiFDPages_t *pages)
{
    /*
     * This will change when we stop exchanging the "offset" pointer
     * with main thread.
     */
    uint32_t page_count = multifd_ram_pages_per_work_count();

    g_clear_pointer(&pages->offset, g_free);
    if (migrate_use_hash()) {
        if (pages->batch_context) {
            cache_hash_pool_fini(hash_cache, page_count,
                                 &pages->batch_context);
            g_clear_pointer(&pages->matched, g_free);
        }
        g_clear_pointer(&pages->digest, g_free);
        if (pages->cached) {
            for (int i = 0; i < page_count; i++) {
                 g_clear_pointer(&pages->cached[i], g_free);
            }
        }
        g_clear_pointer(&pages->cached, g_free);
    }
}

MultiFDSendData *multifd_send_data_alloc(Error **errp)
{
    ERRP_GUARD();

    MultiFDSendData *new = g_try_new0(MultiFDSendData, 1);

    if (!new) {
        error_setg(errp, "Failed to allocate MultiFDSendData");
        return NULL;
    }

    if (multifd_ram_payload_alloc(&new->u.ram, errp) != 0) {
        g_free(new);
        return NULL;
    }
    /* Device state allocates its payload on-demand */

    return new;
}

void multifd_send_data_clear(MultiFDSendData *data)
{
    if (multifd_payload_empty(data)) {
        return;
    }

    switch (data->type) {
    case MULTIFD_PAYLOAD_DEVICE_STATE:
        multifd_send_data_clear_device_state(&data->u.device_state);
        break;
    default:
        /* Nothing to do */
        break;
    }

    data->type = MULTIFD_PAYLOAD_NONE;
}

void multifd_send_data_free(MultiFDSendData *data)
{
    if (!data) {
        return;
    }

    /* This also free's device state payload */
    multifd_send_data_clear(data);

    multifd_ram_payload_free(&data->u.ram);

    g_free(data);
}

int multifd_ram_save_setup(Error **errp)
{
    ERRP_GUARD();

    multifd_ram_send = multifd_send_data_alloc(errp);
    if (!multifd_ram_send) {
        return -1;
    }

    return 0;
}

void multifd_ram_save_cleanup(void)
{
    g_clear_pointer(&multifd_ram_send, multifd_send_data_free);
}

/* Multifd without compression */

/**
 * nocomp_send_setup: setup send side
 *
 * @p: Params for the channel that we are using
 * @errp: pointer to an error
 */
static int nocomp_send_setup(MultiFDSendParams *p, Error **errp)
{
    if (migrate_use_zero_copy_send()) {
        p->write_flags |= QIO_CHANNEL_WRITE_FLAG_ZERO_COPY;
    }

    return 0;
}

/**
 * nocomp_send_cleanup: cleanup send side
 *
 * For no compression this function does nothing.
 *
 * @p: Params for the channel that we are using
 * @errp: pointer to an error
 */
static void nocomp_send_cleanup(MultiFDSendParams *p, Error **errp)
{
    return;
}

static void multifd_ram_prepare_header(MultiFDSendParams *p)
{
    p->iov[0].iov_len = p->packet_len;
    p->iov[0].iov_base = p->packet;
    p->iovs_num++;
}

/**
 * nocomp_send_prepare: prepare date to be able to send
 *
 * For no compression we just have to calculate the size of the
 * packet.
 *
 * Returns 0 for success or -1 for error
 *
 * @p: Params for the channel that we are using
 * @errp: pointer to an error
 */
static int nocomp_send_prepare(MultiFDSendParams *p, Error **errp)
{
    ERRP_GUARD();
    bool use_zero_copy_send = migrate_use_zero_copy_send();
    MultiFDPages_t *pages = &p->data->u.ram;
    uint32_t page_size = multifd_ram_page_size();
    int ret;

    ret = multifd_send_zero_page_detect(p, errp);
    if (ret) {
        return -1;
    }

    if (!use_zero_copy_send) {
        /*
         * Only !zerocopy needs the header in IOV; zerocopy will
         * send it separately.
         */
        multifd_ram_prepare_header(p);
    }

    for (int i = 0; i < pages->normal_num; i++) {
        if (migrate_use_hash()) {
            p->iov[p->iovs_num].iov_base = pages->cached[i];
        } else {
            p->iov[p->iovs_num].iov_base = pages->block->host + pages->offset[i];
        }
        p->iov[p->iovs_num].iov_len = page_size;
        p->iovs_num++;
    }

    p->next_packet_size = pages->normal_num * page_size;
    p->flags |= MULTIFD_FLAG_NOCOMP;

    if (multifd_send_fill_packet(p, errp)) {
        return -1;
    }

    if (use_zero_copy_send) {
        /* Send header first, without zerocopy */
        ret = qio_channel_write_all(p->c, (void *)p->packet,
                                    p->packet_len, errp);
        if (ret != 0) {
            return -1;
        }

        stat64_add(&ram_counters.multifd_bytes, p->packet_len);
    }

    return 0;
}

/**
 * nocomp_recv_setup: setup receive side
 *
 * For no compression this function does nothing.
 *
 * Returns 0 for success or -1 for error
 *
 * @p: Params for the channel that we are using
 * @errp: pointer to an error
 */
static int nocomp_recv_setup(MultiFDRecvParams *p, Error **errp)
{
    return 0;
}

/**
 * nocomp_recv_cleanup: setup receive side
 *
 * For no compression this function does nothing.
 *
 * @p: Params for the channel that we are using
 */
static void nocomp_recv_cleanup(MultiFDRecvParams *p)
{
}

/**
 * nocomp_recv: read the data from the channel
 *
 * For no compression we just need to read things into the correct place.
 *
 * Returns 0 for success or -1 for error
 *
 * @p: Params for the channel that we are using
 * @errp: pointer to an error
 */
static int nocomp_recv(MultiFDRecvParams *p, Error **errp)
{
    uint32_t flags = p->flags & MULTIFD_FLAG_COMPRESSION_MASK;

    if (flags != MULTIFD_FLAG_NOCOMP) {
        error_setg(errp, "multifd %u: flags received %x flags expected %x",
                   p->id, flags, MULTIFD_FLAG_NOCOMP);
        return -1;
    }

    multifd_recv_zero_page_process(p);

    if (!p->normal_num) {
        return 0;
    }

    for (int i = 0; i < p->normal_num; i++) {
        p->iov[i].iov_base = p->host + p->normal[i];
        p->iov[i].iov_len = multifd_ram_page_size();
        ramblock_recv_bitmap_set_offset(p->block, p->normal[i]);
    }
    return qio_channel_readv_all(p->c, p->iov, p->normal_num, errp);
}

static MultiFDMethods multifd_nocomp_ops = {
    .send_setup = nocomp_send_setup,
    .send_cleanup = nocomp_send_cleanup,
    .send_prepare = nocomp_send_prepare,
    .recv_setup = nocomp_recv_setup,
    .recv_cleanup = nocomp_recv_cleanup,
    .recv = nocomp_recv
};

static MultiFDMethods *multifd_ops[MULTIFD_COMPRESSION__MAX] = {
    [MULTIFD_COMPRESSION_NONE] = &multifd_nocomp_ops,
};

void multifd_register_ops(int method, MultiFDMethods *ops)
{
    assert(0 < method && method < MULTIFD_COMPRESSION__MAX);
    multifd_ops[method] = ops;
}

/* Reset a MultiFDPages_t* object for the next use */
static void multifd_pages_reset(MultiFDPages_t *pages)
{
    /*
     * We don't need to touch offset[] array, because it will be
     * overwritten later when reused.
     */
    pages->num = 0;
    pages->normal_num = 0;
    pages->skipped_num = 0;
    pages->block = NULL;
}

static int multifd_send_initial_packet(MultiFDSendParams *p, Error **errp)
{
    MultiFDInit_t msg = {};
    size_t size = sizeof(msg);
    int ret;

    msg.magic = cpu_to_be32(MULTIFD_MAGIC);
    msg.version = cpu_to_be32(MULTIFD_VERSION);
    msg.id = p->id;
    memcpy(msg.uuid, &qemu_uuid.data, sizeof(msg.uuid));

    ret = qio_channel_write_all(p->c, (char *)&msg, size, errp);
    if (ret != 0) {
        return -1;
    }
    stat64_add(&ram_counters.multifd_bytes, size);
    return 0;
}

static int multifd_recv_initial_packet(QIOChannel *c, Error **errp)
{
    MultiFDInit_t msg;
    int ret;

    ret = qio_channel_read_all(c, (char *)&msg, sizeof(msg), errp);
    if (ret != 0) {
        return -1;
    }

    msg.magic = be32_to_cpu(msg.magic);
    msg.version = be32_to_cpu(msg.version);

    if (msg.magic != MULTIFD_MAGIC) {
        error_setg(errp, "multifd: received packet magic %x "
                   "expected %x", msg.magic, MULTIFD_MAGIC);
        return -1;
    }

    if (msg.version != MULTIFD_VERSION) {
        error_setg(errp, "multifd: received packet version %u "
                   "expected %u", msg.version, MULTIFD_VERSION);
        return -1;
    }

    if (memcmp(msg.uuid, &qemu_uuid, sizeof(qemu_uuid))) {
        char *uuid = qemu_uuid_unparse_strdup(&qemu_uuid);
        char *msg_uuid = qemu_uuid_unparse_strdup((const QemuUUID *)msg.uuid);

        error_setg(errp, "multifd: received uuid '%s' and expected "
                   "uuid '%s' for channel %hhd", msg_uuid, uuid, msg.id);
        g_free(uuid);
        g_free(msg_uuid);
        return -1;
    }

    if (msg.id > migrate_multifd_channels()) {
        error_setg(errp, "multifd: received channel version %u "
                   "expected %u", msg.version, MULTIFD_VERSION);
        return -1;
    }

    return msg.id;
}

static int multifd_ram_fill_packet(MultiFDSendParams *p, Error **errp)
{
    ERRP_GUARD();

    MultiFDPacket_t *packet = p->packet;
    MultiFDPages_t *pages = &p->data->u.ram;
    uint32_t zero_num = (pages->num - pages->normal_num) - pages->skipped_num;

    packet->pages_alloc = cpu_to_be32(multifd_ram_pages_per_packet_count());
    packet->normal_pages = cpu_to_be32(pages->normal_num);
    packet->zero_pages = cpu_to_be32(zero_num);
    packet->skipped_pages = cpu_to_be32(pages->skipped_num);

    if (pages->block) {
        strncpy(packet->ramblock, pages->block->idstr, 256);
    }

    for (int i = 0; i < pages->num; i++) {
        /* there are architectures where ram_addr_t is 32 bit */
        uint64_t temp = pages->offset[i];

        packet->offset[i] = cpu_to_be64(temp);

        /* TODO: Workaround spurious zero pages ghosting in the pages->offset array */
        if (migrate_use_hash() &&
            i >= (pages->normal_num + pages->skipped_num)) {
            cache_hash_invalidate(hash_cache, pages->block->offset + temp);
        }
    }

    trace_multifd_send_ram_fill(p->id, pages->normal_num, zero_num);

    return 0;
}

/* Fills a RAM multifd packet */
int multifd_send_fill_packet(MultiFDSendParams *p, Error **errp)
{
    ERRP_GUARD();

    MultiFDPacket_t *packet = p->packet;
    uint64_t packet_num;
    bool sync_packet = p->flags & MULTIFD_FLAG_SYNC;

    memset(packet, 0, p->packet_len);

    packet->hdr.magic = cpu_to_be32(MULTIFD_MAGIC);
    packet->hdr.version = cpu_to_be32(MULTIFD_VERSION);

    packet->hdr.flags = cpu_to_be32(p->flags);
    packet->next_packet_size = cpu_to_be32(p->next_packet_size);

    packet_num = qatomic_fetch_inc(&multifd_send_state->packet_num);
    packet->packet_num = cpu_to_be64(packet_num);

    p->packets_sent++;

    if (!sync_packet) {
        if (multifd_ram_fill_packet(p, errp)) {
            return -1;
        }
    }

    trace_multifd_send_fill(p->id, packet_num,
                            p->flags, p->next_packet_size);

    return 0;
}

static int multifd_ram_unfill_packet(MultiFDRecvParams *p, Error **errp)
{
    MultiFDPacket_t *packet = p->packet;
    uint32_t page_count = multifd_ram_pages_per_packet_count();
    uint32_t page_size = multifd_ram_page_size();
    uint32_t pages_per_packet = be32_to_cpu(packet->pages_alloc);
    int i;

    if (pages_per_packet > page_count) {
        error_setg(errp, "multifd: received packet with %u pages, expected %u",
                   pages_per_packet, page_count);
        return -1;
    }

    p->normal_num = be32_to_cpu(packet->normal_pages);
    if (p->normal_num > pages_per_packet) {
        error_setg(errp, "multifd: received packet with %u non-zero pages, "
                   "which exceeds maximum expected pages %u",
                   p->normal_num, pages_per_packet);
        return -1;
    }

    p->zero_num = be32_to_cpu(packet->zero_pages);
    if (p->zero_num > pages_per_packet - p->normal_num) {
        error_setg(errp,
                   "multifd: received packet with %u zero pages, expected maximum %u",
                   p->zero_num, pages_per_packet - p->normal_num);
        return -1;
    }

    p->skipped_num = be32_to_cpu(packet->skipped_pages);
    if (p->skipped_num > pages_per_packet) {
        error_setg(errp, "multifd: received packet with %u non-zero pages, "
                   "which exceeds maximum expected pages %u",
                   p->skipped_num, pages_per_packet);
        return -1;
    }

    if (p->normal_num == 0 && p->skipped_num == 0 && p->zero_num == 0) {
        return 0;
    }

    /* make sure that ramblock is 0 terminated */
    packet->ramblock[255] = 0;
    p->block = qemu_ram_block_by_name(packet->ramblock);
    if (!p->block) {
        error_setg(errp, "multifd: unknown ram block %s",
                   packet->ramblock);
        return -1;
    }

    p->host = p->block->host;
    for (i = 0; i < p->normal_num; i++) {
        uint64_t offset = be64_to_cpu(packet->offset[i]);

        if (offset > (p->block->used_length - page_size)) {
            error_setg(errp, "multifd: offset too long %" PRIu64
                       " (max " RAM_ADDR_FMT ")",
                       offset, p->block->used_length);
            return -1;
        }
        p->normal[i] = offset;
    }

    for (i = 0; i < p->zero_num; i++) {
        uint64_t offset = be64_to_cpu(packet->offset[p->normal_num + p->skipped_num + i]);

        if (offset > (p->block->used_length - page_size)) {
            error_setg(errp, "multifd: offset too long %" PRIu64
                       " (max " RAM_ADDR_FMT ")",
                       offset, p->block->used_length);
            return -1;
        }
        p->zero[i] = offset;
    }

    return 0;
}

static int multifd_recv_unfill_packet_header(MultiFDRecvParams *p,
                                             const MultiFDPacketHdr_t *hdr,
                                             Error **errp)
{
    uint32_t magic = be32_to_cpu(hdr->magic);
    uint32_t version = be32_to_cpu(hdr->version);

    if (magic != MULTIFD_MAGIC) {
        error_setg(errp, "multifd: received packet magic %x, expected %x",
                   magic, MULTIFD_MAGIC);
        return -1;
    }

    if (version != MULTIFD_VERSION) {
        error_setg(errp, "multifd: received packet version %u, expected %u",
                   version, MULTIFD_VERSION);
        return -1;
    }

    p->flags = be32_to_cpu(hdr->flags);

    return 0;
}

static int multifd_recv_unfill_packet_device_state(MultiFDRecvParams *p,
                                                   Error **errp)
{
    MultiFDPacketDeviceState_t *packet = p->packet_dev_state;

    packet->instance_id = be32_to_cpu(packet->instance_id);
    p->next_packet_size = be32_to_cpu(packet->next_packet_size);

    return 0;
}

static int multifd_recv_unfill_packet_ram(MultiFDRecvParams *p, Error **errp)
{
    const MultiFDPacket_t *packet = p->packet;
    int ret = 0;

    p->next_packet_size = be32_to_cpu(packet->next_packet_size);
    p->packet_num = be64_to_cpu(packet->packet_num);

    /* Always unfill, old upstream QEMUs (<9.0) send data along with SYNC */
    ret = multifd_ram_unfill_packet(p, errp);

    trace_multifd_recv_unfill(p->id, p->packet_num, p->flags,
                              p->next_packet_size);

    return ret;
}

static int multifd_recv_unfill_packet(MultiFDRecvParams *p, Error **errp)
{
    p->packets_recved++;

    if (p->flags & MULTIFD_FLAG_DEVICE_STATE) {
        return multifd_recv_unfill_packet_device_state(p, errp);
    }

    return multifd_recv_unfill_packet_ram(p, errp);
}

static bool multifd_send_should_exit(void)
{
    return qatomic_read(&multifd_send_state->exiting);
}

/*
 * The migration thread can wait on either of the two semaphores.  This
 * function can be used to kick the main thread out of waiting on either of
 * them.  Should mostly only be called when something wrong happened with
 * the current multifd send thread.
 */
static void multifd_send_kick_main(MultiFDSendParams *p)
{
    qemu_sem_post(&p->sem_sync);
    qemu_sem_post(&multifd_send_state->channels_ready);
}

/*
 * multifd_send() works by exchanging the MultiFDSendData object
 * provided by the caller with an unused MultiFDSendData object from
 * the next channel that is found to be idle.
 *
 * The channel owns the data until it finishes transmitting and the
 * caller owns the empty object until it fills it with data and calls
 * this function again. No locking necessary.
 *
 * Switching is safe because both the migration thread and the channel
 * thread have barriers in place to serialize access.
 *
 * Returns true if succeed, false otherwise.
 */
bool multifd_send(MultiFDSendData **send_data)
{
    int i;
    static int next_channel;
    MultiFDSendParams *p = NULL; /* make happy gcc */
    MultiFDSendData *tmp;

    if (multifd_send_should_exit()) {
        return false;
    }

    QEMU_LOCK_GUARD(&multifd_send_state->multifd_send_mutex);

    /* We wait here, until at least one channel is ready */
    qemu_sem_wait(&multifd_send_state->channels_ready);

    /*
     * next_channel can remain from a previous migration that was
     * using more channels, so ensure it doesn't overflow if the
     * limit is lower now.
     */
    next_channel %= migrate_multifd_channels();
    for (i = next_channel;; i = (i + 1) % migrate_multifd_channels()) {
        if (multifd_send_should_exit()) {
            return false;
        }
        p = &multifd_send_state->params[i];
        /*
         * Lockless read to p->pending_job is safe, because only multifd
         * sender thread can clear it.
         */
        if (qatomic_read(&p->pending_job) == false) {
            next_channel = (i + 1) % migrate_multifd_channels();
            break;
        }
    }

    /*
     * Make sure we read p->pending_job before all the rest.  Pairs with
     * qatomic_store_release() in multifd_send_thread().
     */
    smp_mb_acquire();

    assert(multifd_payload_empty(p->data));

    /*
     * Swap the pointers. The channel gets the client data for
     * transferring and the client gets back an unused data slot.
     */
    tmp = *send_data;
    *send_data = p->data;
    p->data = tmp;

    /*
     * Making sure p->data is setup before marking pending_job=true. Pairs
     * with the qatomic_load_acquire() in multifd_send_thread().
     */
    qatomic_store_release(&p->pending_job, true);
    qemu_sem_post(&p->sem);

    return true;
}

static inline bool multifd_queue_empty(MultiFDPages_t *pages)
{
    return pages->num == 0;
}

static inline bool multifd_queue_full(MultiFDPages_t *pages)
{
    return pages->num == multifd_ram_pages_per_work_count();
}

static inline void multifd_enqueue(MultiFDPages_t *pages, ram_addr_t offset)
{
    pages->offset[pages->num++] = offset;
}

/* Returns true if enqueue successful, false otherwise */
bool multifd_queue_page(QEMUFile *f, RAMBlock *block, ram_addr_t offset)
{
    MultiFDPages_t *pages;

retry:
    pages = &multifd_ram_send->u.ram;

    if (multifd_payload_empty(multifd_ram_send)) {
        multifd_pages_reset(pages);
        multifd_set_payload_type(multifd_ram_send, MULTIFD_PAYLOAD_RAM);
    }

    /* If the queue is empty, we can already enqueue now */
    if (multifd_queue_empty(pages)) {
        pages->block = block;
        multifd_enqueue(pages, offset);
        return true;
    }

    /*
     * Not empty, meanwhile we need a flush.  It can because of either:
     *
     * (1) The page is not on the same ramblock of previous ones, or,
     * (2) The queue is full.
     *
     * After flush, always retry.
     */
    if (pages->block != block || multifd_queue_full(pages)) {
        if (!multifd_send(&multifd_ram_send)) {
            return false;
        }
        goto retry;
    }

    /* Not empty, and we still have space, do it! */
    multifd_enqueue(pages, offset);
    return true;
}

/* Multifd send side hit an error; remember it and prepare to quit */
static void multifd_send_set_error(Error *err)
{
    /*
     * We don't want to exit each threads twice.  Depending on where
     * we get the error, or if there are two independent errors in two
     * threads at the same time, we can end calling this function
     * twice.
     */
    if (qatomic_xchg(&multifd_send_state->exiting, 1)) {
        return;
    }

    if (err) {
        MigrationState *s = migrate_get_current();
        migrate_set_error(s, err);
        if (s->state == MIGRATION_STATUS_SETUP ||
            s->state == MIGRATION_STATUS_PRE_SWITCHOVER ||
            s->state == MIGRATION_STATUS_DEVICE ||
            s->state == MIGRATION_STATUS_ACTIVE) {
            migrate_set_state(&s->state, s->state,
                              MIGRATION_STATUS_FAILED);
        }
    }
}

static void multifd_send_terminate_threads(void)
{
    int i;

    trace_multifd_send_terminate_threads();

    /*
     * Tell everyone we're quitting.  No xchg() needed here; we simply
     * always set it.
     */
    qatomic_set(&multifd_send_state->exiting, 1);

    /*
     * Firstly, kick all threads out; no matter whether they are just idle,
     * or blocked in an IO system call.
     */
    for (i = 0; i < migrate_multifd_channels(); i++) {
        MultiFDSendParams *p = &multifd_send_state->params[i];
        if (p->setup_done) {
            qemu_sem_post(&p->sem);
        }
        if (p->c) {
            qio_channel_shutdown(p->c, QIO_CHANNEL_SHUTDOWN_BOTH, NULL);
        }
    }

    /*
     * Finally recycle all the threads.
     */
    for (i = 0; i < migrate_multifd_channels(); i++) {
        MultiFDSendParams *p = &multifd_send_state->params[i];

        if (p->tls_thread_created) {
            qemu_thread_join(&p->tls_thread);
        }

        if (p->thread_created) {
            qemu_thread_join(&p->thread);
        }
    }
}

static bool multifd_send_cleanup_channel(MultiFDSendParams *p, Error **errp)
{
    if (p->registered_yank) {
        migration_ioc_unregister_yank(p->c);
    }
    socket_send_channel_destroy(p->c);
    p->c = NULL;
    if (p->setup_done) {
        qemu_sem_destroy(&p->sem);
        qemu_sem_destroy(&p->sem_sync);
        p->setup_done = false;
    }
    g_free(p->name);
    p->name = NULL;
    g_clear_pointer(&p->data, multifd_send_data_free);
    p->packet_len = 0;
    g_clear_pointer(&p->packet_device_state, g_free);
    g_free(p->packet);
    p->packet = NULL;
    g_free(p->iov);
    p->iov = NULL;
    multifd_send_state->ops->send_cleanup(p, errp);

    return *errp == NULL;
}

static void multifd_send_cleanup_state(void)
{
    multifd_device_state_send_cleanup();
    qemu_sem_destroy(&multifd_send_state->channels_created);
    qemu_sem_destroy(&multifd_send_state->channels_ready);
    qemu_mutex_destroy(&multifd_send_state->multifd_send_mutex);
    g_free(multifd_send_state->params);
    multifd_send_state->params = NULL;
    g_free(multifd_send_state);
    multifd_send_state = NULL;
}

void multifd_send_shutdown(void)
{
    int i;

    if (!migrate_use_multifd() || !migrate_multi_channels_is_allowed() ||
        !multifd_send_state) {
        return;
    }

    for (i = 0; i < migrate_multifd_channels(); i++) {
        MultiFDSendParams *p = &multifd_send_state->params[i];

        /* thread_created implies the TLS handshake has succeeded */
        if (p->tls_thread_created && p->thread_created) {
            Error *local_err = NULL;
            /*
             * The destination expects the TLS session to always be
             * properly terminated. This helps to detect a premature
             * termination in the middle of the stream.  Note that
             * older QEMUs always break the connection on the source
             * and the destination always sees
             * GNUTLS_E_PREMATURE_TERMINATION.
             */
            migration_tls_channel_end(p->c, &local_err);

            /*
             * The above can return an error in case the migration has
             * already failed. If the migration succeeded, errors are
             * not expected but there's no need to kill the source.
             */
            if (local_err && !migration_has_failed(migrate_get_current())) {
                warn_report(
                    "multifd_send_%d: Failed to terminate TLS connection: %s",
                    p->id, error_get_pretty(local_err));
                break;
            }
        }
    }

    multifd_send_terminate_threads();

    for (i = 0; i < migrate_multifd_channels(); i++) {
        MultiFDSendParams *p = &multifd_send_state->params[i];
        Error *local_err = NULL;

        if (!multifd_send_cleanup_channel(p, &local_err)) {
            migrate_set_error(migrate_get_current(), local_err);
            error_free(local_err);
        }
    }

    multifd_send_cleanup_state();
}

static int multifd_zero_copy_flush(QIOChannel *c)
{
    int ret;
    Error *err = NULL;

    ret = qio_channel_flush(c, &err);
    if (ret < 0) {
        error_report_err(err);
        return -1;
    }
    if (ret == 1) {
        stat64_add(&ram_counters.dirty_sync_missed_zero_copy, 1);
    }

    return ret;
}

int multifd_send_sync_main(QEMUFile *f)
{
    int i;
    bool flush_zero_copy;

    if (!migrate_use_multifd()) {
        return 0;
    }

    if (!multifd_payload_empty(multifd_ram_send)) {
        if (!multifd_send(&multifd_ram_send)) {
            error_report("%s: multifd_send fail", __func__);
            return -1;
        }
    }

    /*
     * When using zero-copy, it's necessary to flush the pages before any of
     * the pages can be sent again, so we'll make sure the new version of the
     * pages will always arrive _later_ than the old pages.
     *
     * Currently we achieve this by flushing the zero-page requested writes
     * per ram iteration, but in the future we could potentially optimize it
     * to be less frequent, e.g. only after we finished one whole scanning of
     * all the dirty bitmaps.
     */

    flush_zero_copy = migrate_use_zero_copy_send();

    for (i = 0; i < migrate_multifd_channels(); i++) {
        MultiFDSendParams *p = &multifd_send_state->params[i];

        if (multifd_send_should_exit()) {
            return -1;
        }

        trace_multifd_send_sync_main_signal(p->id);

        /*
         * We should be the only user so far, so not possible to be set by
         * others concurrently.
         */
        assert(qatomic_read(&p->pending_sync) == false);
        qatomic_set(&p->pending_sync, true);
        qemu_sem_post(&p->sem);

        if (flush_zero_copy && p->c && (multifd_zero_copy_flush(p->c) < 0)) {
            return -1;
        }
    }
    for (i = 0; i < migrate_multifd_channels(); i++) {
        MultiFDSendParams *p = &multifd_send_state->params[i];

        if (multifd_send_should_exit()) {
            return -1;
        }

        qemu_sem_wait(&multifd_send_state->channels_ready);
        trace_multifd_send_sync_main_wait(p->id);
        qemu_sem_wait(&p->sem_sync);
    }
    trace_multifd_send_sync_main(multifd_send_state->packet_num);

    return 0;
}

static int multifd_send_pkt(MultiFDSendParams *p, uint32_t flags,
                               uint32_t pages_pkt, Error **errp)
{
    int write_flags_masked = 0;
    p->flags = flags;
    p->iovs_num = 0;
    bool is_device_state = multifd_payload_device_state(p->data);
    size_t total_size = 0;
    Error *local_err = NULL;
    int ret = 0;

    if (is_device_state) {
        multifd_device_state_send_prepare(p);

        /* Device state packets cannot be sent via zerocopy */
        write_flags_masked |= QIO_CHANNEL_WRITE_FLAG_ZERO_COPY;
    } else {
        p->data->u.ram.num = pages_pkt;
        ret = multifd_send_state->ops->send_prepare(p, &local_err);
        if (ret != 0) {
            if (local_err) {
                error_propagate(errp, local_err);
            }
            return ret;
        }

        /* Hash cache packets cannot be sent via zerocopy */
        if (migrate_use_hash()) {
            write_flags_masked |= QIO_CHANNEL_WRITE_FLAG_ZERO_COPY;
        }
    }

    /*
     * The packet header in the zerocopy RAM case is accounted for
     * in nocomp_send_prepare() - where it is actually
     * being sent.
     */
    total_size = iov_size(p->iov, p->iovs_num);
    stat64_add(&ram_counters.multifd_bytes, total_size);

    ret = qio_channel_writev_full_all(p->c, p->iov, p->iovs_num,
                                      NULL, 0,
                                      p->write_flags & ~write_flags_masked,
                                      &local_err);
    if (ret != 0) {
        if (local_err) {
            error_propagate(errp, local_err);
        }
        return ret;
    }

    p->next_packet_size = 0;
    return ret;
}

static void *multifd_send_thread(void *opaque)
{
    MultiFDSendParams *p = opaque;
    Error *local_err = NULL;
    int ret = 0;

    trace_multifd_send_thread_start(p->id);
    rcu_register_thread();

    if (multifd_send_initial_packet(p, &local_err) < 0) {
        ret = -1;
        goto out;
    }
    uint32_t max_pages_per_pkt = multifd_ram_pages_per_packet_count();

    while (true) {
        qemu_sem_post(&multifd_send_state->channels_ready);
        qemu_sem_wait(&p->sem);

        if (multifd_send_should_exit()) {
            break;
        }

        /*
         * Read pending_job flag before p->data.  Pairs with the
         * qatomic_store_release() in multifd_send().
         */
        if (qatomic_load_acquire(&p->pending_job)) {
            uint32_t pages_total = p->data->u.ram.num;
            uint32_t pages_processed = 0;
            uint64_t *pages_offset = p->data->u.ram.offset;
            /* Preserve flags for each packet in the loop below. */
            uint32_t flags = p->flags;
            /* Pages in current packet. */
            uint32_t pages_pkt = 0;

            assert(!multifd_payload_empty(p->data));

            while (pages_total > pages_processed) {
                pages_pkt = MIN(max_pages_per_pkt, pages_total - pages_processed);
                ret = multifd_send_pkt(p, flags, pages_pkt, &local_err);
                if (ret < 0) {
                    p->data->u.ram.offset = pages_offset;
                    qatomic_store_release(&p->pending_job, false);
                    break;
                }
                pages_processed += pages_pkt;
                p->data->u.ram.offset += pages_pkt;
            }

            p->data->u.ram.offset = pages_offset;
            multifd_send_data_clear(p->data);

            /*
             * Making sure p->data is published before saying "we're
             * free".  Pairs with the smp_mb_acquire() in
             * multifd_send().
             */
            qatomic_store_release(&p->pending_job, false);
        } else {
            /*
             * If not a normal job, must be a sync request.  Note that
             * pending_sync is a standalone flag (unlike pending_job), so
             * it doesn't require explicit memory barriers.
             */
            assert(qatomic_read(&p->pending_sync));
            p->flags = MULTIFD_FLAG_SYNC;
            ret = multifd_send_fill_packet(p, &local_err);
            if (ret) {
                break;
            }
            ret = qio_channel_write_all(p->c, (void *)p->packet,
                                        p->packet_len, &local_err);
            if (ret != 0) {
                break;
            }
            /* p->next_packet_size will always be zero for a SYNC packet */
            stat64_add(&ram_counters.multifd_bytes, p->packet_len);
            qatomic_set(&p->pending_sync, false);
            p->flags = 0;
            qemu_sem_post(&p->sem_sync);
        }
    }

out:
    if (ret) {
        assert(local_err);
        trace_multifd_send_error(p->id);
        multifd_send_set_error(local_err);
        multifd_send_kick_main(p);
        error_free(local_err);
    }

    rcu_unregister_thread();
    trace_multifd_send_thread_end(p->id, p->packets_sent);

    return NULL;
}

static void multifd_new_send_channel_async(QIOTask *task, gpointer opaque);

static void *multifd_tls_handshake_thread(void *opaque)
{
    MultiFDSendParams *p = opaque;
    QIOChannelTLS *tioc = QIO_CHANNEL_TLS(p->c);

    qio_channel_tls_handshake(tioc,
                              multifd_new_send_channel_async,
                              p,
                              NULL,
                              NULL);
    return NULL;
}

static bool multifd_tls_channel_connect(MultiFDSendParams *p,
                                        QIOChannel *ioc,
                                        Error **errp)
{
    MigrationState *s = migrate_get_current();
    const char *hostname = s->hostname;
    QIOChannelTLS *tioc;

    tioc = migration_tls_client_create(s, ioc, hostname, errp);
    if (!tioc) {
        return false;
    }

    /*
     * Ownership of the socket channel now transfers to the newly
     * created TLS channel, which has already taken a reference.
     */
    object_unref(OBJECT(ioc));
    trace_multifd_tls_outgoing_handshake_start(ioc, tioc, hostname);
    qio_channel_set_name(QIO_CHANNEL(tioc), "multifd-tls-outgoing");
    p->c = QIO_CHANNEL(tioc);

    p->tls_thread_created = true;
    qemu_thread_create(&p->tls_thread, "multifd-tls-handshake-worker",
                       multifd_tls_handshake_thread, p,
                       QEMU_THREAD_JOINABLE);
    return true;
}

static bool multifd_channel_connect(MultiFDSendParams *p,
                                    QIOChannel *ioc,
                                    Error **errp)
{
    qio_channel_set_delay(ioc, false);

    migration_ioc_register_yank(ioc);
    p->registered_yank = true;
    p->c = ioc;

    p->thread_created = true;
    qemu_thread_create(&p->thread, p->name, multifd_send_thread, p,
                       QEMU_THREAD_JOINABLE);
    return true;
}

/*
 * When TLS is enabled this function is called once to establish the
 * TLS connection and a second time after the TLS handshake to create
 * the multifd channel. Without TLS it goes straight into the channel
 * creation.
 */
static void multifd_new_send_channel_async(QIOTask *task, gpointer opaque)
{
    MultiFDSendParams *p = opaque;
    QIOChannel *sioc = QIO_CHANNEL(qio_task_get_source(task));
    Error *local_err = NULL;
    bool ret;

    trace_multifd_new_send_channel_async(p->id);
    if (qio_task_propagate_error(task, &local_err)) {
        ret = false;
        goto cleanup;
    } else {
        trace_multifd_set_outgoing_channel(sioc, object_get_typename(OBJECT(sioc)),
                                       migrate_get_current()->hostname);

        if (migrate_channel_requires_tls_upgrade(sioc)) {
            ret = multifd_tls_channel_connect(p, sioc, &local_err);
            if (ret) {
                return;
            }
        } else {
            ret = multifd_channel_connect(p, sioc, &local_err);
        }
    }
cleanup:
    /*
     * Here we're not interested whether creation succeeded, only that
     * it happened at all.
     */
    qemu_sem_post(&multifd_send_state->channels_created);

    if (ret) {
        return;
    }
    trace_multifd_new_send_channel_async_error(p->id, local_err);
    multifd_send_set_error(local_err);
    if (!p->c) {
        /*
         * If no channel has been created, drop the initial
         * reference. Otherwise cleanup happens at
         * multifd_send_channel_destroy()
         */
        object_unref(OBJECT(sioc));
    }
    error_free(local_err);
}

bool multifd_send_setup(void)
{
    MigrationState *s = migrate_get_current();
    Error *local_err = NULL;
    int thread_count, ret = 0;
    uint32_t pages_per_pkt = multifd_ram_pages_per_packet_count();
    uint8_t i;

    if (!migrate_use_multifd()) {
        return true;
    }
    if (!migrate_multi_channels_is_allowed()) {
        return true;
    }

    thread_count = migrate_multifd_channels();
    multifd_send_state = g_try_malloc0(sizeof(*multifd_send_state));
    if (!multifd_send_state) {
        error_setg(&local_err, "%s: allocation failed for multifd_send_state",
                   __func__);
        goto err_out;
    }

    multifd_send_state->params = g_try_new0(MultiFDSendParams, thread_count);
    if (!multifd_send_state->params) {
        error_setg(&local_err, "%s: allocation failed for multifd_send_state->params",
                   __func__);
        goto err_out;
    }

    qemu_mutex_init(&multifd_send_state->multifd_send_mutex);
    qemu_sem_init(&multifd_send_state->channels_created, 0);
    qemu_sem_init(&multifd_send_state->channels_ready, 0);
    qatomic_set(&multifd_send_state->exiting, 0);
    multifd_send_state->ops = multifd_ops[migrate_multifd_compression()];

    for (i = 0; i < thread_count; i++) {
        MultiFDSendParams *p = &multifd_send_state->params[i];

        p->id = i;
        p->data = multifd_send_data_alloc(&local_err);
        if (!p->data) {
            ret = -1;
            goto err_out;
        }

        p->packet_len = sizeof(MultiFDPacket_t)
                      + sizeof(uint64_t) * pages_per_pkt;
        p->packet = g_try_malloc0(p->packet_len);
        if (!p->packet) {
            error_setg(&local_err, "%s: allocation failed for p->packet",
                   __func__);
            ret = -1;
            goto err_out;
        }

        p->packet_device_state = g_try_malloc0(sizeof(*p->packet_device_state));
        if (!p->packet_device_state) {
            error_setg(&local_err, "%s: allocation failed for p->packet_device_state",
                   __func__);
            ret = -1;
            goto err_out;
        }

        p->packet_device_state->hdr.magic = cpu_to_be32(MULTIFD_MAGIC);
        p->packet_device_state->hdr.version = cpu_to_be32(MULTIFD_VERSION);
        p->name = g_strdup_printf("multifdsend_%d", i);
        /* We need one extra place for the packet header */
        p->iov = g_try_new0(struct iovec, multifd_ram_iovs_per_packet_count());
        if (!p->iov) {
            error_setg(&local_err, "%s: allocation failed for p->iov",
                   __func__);
            ret = -1;
            goto err_out;
        }
        
        p->write_flags = 0;
        qemu_sem_init(&p->sem, 0);
        qemu_sem_init(&p->sem_sync, 0);
        p->setup_done = true;
        socket_send_channel_create(multifd_new_send_channel_async, p);
    }

    /*
     * Wait until channel creation has started for all channels. The
     * creation can still fail, but no more channels will be created
     * past this point.
     */
    for (i = 0; i < thread_count; i++) {
        qemu_sem_wait(&multifd_send_state->channels_created);
    }

    for (i = 0; i < thread_count; i++) {
        MultiFDSendParams *p = &multifd_send_state->params[i];

        ret = multifd_send_state->ops->send_setup(p, &local_err);
        if (ret) {
            goto err_out;
        }
    }

    ret = multifd_device_state_send_setup(&local_err);
 err_out:
    /*
     * Memory allocated during the setup phase will be
     * freed by calling migrate_fd_cleanup().
     * migrate_fd_cleanup() calls qemu_savevm_state_cleanup()
     * and after multifd_send_shutdown().
     */
    if (ret) {
        migrate_set_error(s, local_err);
        error_report_err(local_err);
        migrate_set_state(&s->state, MIGRATION_STATUS_SETUP,
                          MIGRATION_STATUS_FAILED);
        return false;
    }


    return true;
}

struct {
    MultiFDRecvParams *params;
    /* number of created threads */
    int count;
    /* syncs main thread and channels */
    QemuSemaphore sem_sync;
    /* global number of generated multifd packets */
    uint64_t packet_num;
    /* multifd ops */
    MultiFDMethods *ops;
} *multifd_recv_state;

static void multifd_recv_terminate_threads(Error *err)
{
    int i;

    trace_multifd_recv_terminate_threads(err != NULL);

    if (err) {
        MigrationState *s = migrate_get_current();
        migrate_set_error(s, err);
        if (s->state == MIGRATION_STATUS_SETUP ||
            s->state == MIGRATION_STATUS_ACTIVE) {
            migrate_set_state(&s->state, s->state,
                              MIGRATION_STATUS_FAILED);
        }
    }

    for (i = 0; i < migrate_multifd_channels(); i++) {
        MultiFDRecvParams *p = &multifd_recv_state->params[i];

        qemu_mutex_lock(&p->mutex);
        p->quit = true;
        /*
         * We could arrive here for two reasons:
         *  - normal quit, i.e. everything went fine, just finished
         *  - error quit: We close the channels so the channel threads
         *    finish the qio_channel_read_all_eof()
         */
        if (p->c) {
            qio_channel_shutdown(p->c, QIO_CHANNEL_SHUTDOWN_BOTH, NULL);
        }
        qemu_mutex_unlock(&p->mutex);
    }
}

void multifd_recv_shutdown(void)
{
    if (migrate_use_multifd()) {
        multifd_recv_terminate_threads(NULL);
    }
}

static void multifd_recv_cleanup_channel(MultiFDRecvParams *p)
{
    migration_ioc_unregister_yank(p->c);
    object_unref(OBJECT(p->c));
    p->c = NULL;
    qemu_mutex_destroy(&p->mutex);
    qemu_sem_destroy(&p->sem_sync);
    g_free(p->name);
    p->name = NULL;
    p->packet_len = 0;
    g_free(p->packet);
    p->packet = NULL;
    g_clear_pointer(&p->packet_dev_state, g_free);
    g_free(p->iov);
    p->iov = NULL;
    g_free(p->normal);
    p->normal = NULL;
    g_free(p->zero);
    p->zero = NULL;
    multifd_recv_state->ops->recv_cleanup(p);
}

static void multifd_recv_cleanup_state(void)
{
    qemu_sem_destroy(&multifd_recv_state->sem_sync);
    g_free(multifd_recv_state->params);
    multifd_recv_state->params = NULL;
    g_free(multifd_recv_state);
    multifd_recv_state = NULL;
}

void multifd_recv_cleanup(void)
{
    int i;

    if (!migrate_use_multifd() || !migrate_multi_channels_is_allowed()) {
        return;
    }
    multifd_recv_terminate_threads(NULL);
    for (i = 0; i < migrate_multifd_channels(); i++) {
        MultiFDRecvParams *p = &multifd_recv_state->params[i];

        /*
         * multifd_recv_thread may hung at MULTIFD_FLAG_SYNC handle code,
         * however try to wakeup it without harm in cleanup phase.
         */
        qemu_sem_post(&p->sem_sync);

        if (p->thread_created) {
            qemu_thread_join(&p->thread);
        }
    }
    for (i = 0; i < migrate_multifd_channels(); i++) {
        multifd_recv_cleanup_channel(&multifd_recv_state->params[i]);
    }
    multifd_recv_cleanup_state();
}

void multifd_recv_sync_main(void)
{
    int i;

    if (!migrate_use_multifd()) {
        return;
    }
    for (i = 0; i < migrate_multifd_channels(); i++) {
        MultiFDRecvParams *p = &multifd_recv_state->params[i];

        trace_multifd_recv_sync_main_wait(p->id);
        qemu_sem_wait(&multifd_recv_state->sem_sync);
    }
    for (i = 0; i < migrate_multifd_channels(); i++) {
        MultiFDRecvParams *p = &multifd_recv_state->params[i];

        WITH_QEMU_LOCK_GUARD(&p->mutex) {
            if (multifd_recv_state->packet_num < p->packet_num) {
                multifd_recv_state->packet_num = p->packet_num;
            }
        }
        trace_multifd_recv_sync_main_signal(p->id);
        qemu_sem_post(&p->sem_sync);
    }
    trace_multifd_recv_sync_main(multifd_recv_state->packet_num);
}

static int multifd_device_state_recv(MultiFDRecvParams *p, Error **errp)
{
    g_autofree char *dev_state_buf = NULL;
    int ret;

    dev_state_buf = g_malloc(p->next_packet_size);

    ret = qio_channel_read_all(p->c, dev_state_buf, p->next_packet_size, errp);
    if (ret != 0) {
        return ret;
    }

    if (p->packet_dev_state->idstr[sizeof(p->packet_dev_state->idstr) - 1]
        != 0) {
        error_setg(errp, "unterminated multifd device state idstr");
        return -1;
    }

    if (!qemu_loadvm_load_state_buffer(p->packet_dev_state->idstr,
                                       p->packet_dev_state->instance_id,
                                       dev_state_buf, p->next_packet_size,
                                       errp)) {
        ret = -1;
    }

    return ret;
}

static void *multifd_recv_thread(void *opaque)
{
    MigrationState *s = migrate_get_current();
    MultiFDRecvParams *p = opaque;
    Error *local_err = NULL;
    int ret;

    trace_multifd_recv_thread_start(p->id);
    rcu_register_thread();

    if (!s->multifd_clean_tls_termination) {
        p->read_flags = QIO_CHANNEL_READ_FLAG_RELAXED_EOF;
    }

    while (true) {
        MultiFDPacketHdr_t hdr;
        uint32_t flags;
        bool is_device_state = false;
        bool has_data = false;
        struct iovec iov = {
            .iov_base = (void *)&hdr,
            .iov_len = sizeof(hdr)
        };
        uint8_t *pkt_buf;
        size_t pkt_len;

        p->normal_num = 0;
        p->skipped_num = 0;

        if (p->quit) {
            break;
        }

        ret = qio_channel_readv_full_all_eof(p->c, &iov, 1, NULL, NULL,
                                             p->read_flags, &local_err);
        if (!ret) {
            /* EOF */
            assert(!local_err);
            break;
        }

        if (ret == -1) {
            break;
        }

        ret = multifd_recv_unfill_packet_header(p, &hdr, &local_err);
        if (ret) {
            break;
        }

        is_device_state = p->flags & MULTIFD_FLAG_DEVICE_STATE;
        if (is_device_state) {
            pkt_buf = (uint8_t *)p->packet_dev_state + sizeof(hdr);
            pkt_len = sizeof(*p->packet_dev_state) - sizeof(hdr);
        } else {
            pkt_buf = (uint8_t *)p->packet + sizeof(hdr);
            pkt_len = p->packet_len - sizeof(hdr);
        }

        ret = qio_channel_read_all_eof(p->c, (char *)pkt_buf, pkt_len,
                                       &local_err);
        if (!ret) {
            /* EOF */
            error_setg(&local_err, "multifd: unexpected EOF after packet header");
            break;
        }

        if (ret == -1) {
            break;
        }

        qemu_mutex_lock(&p->mutex);
        ret = multifd_recv_unfill_packet(p, &local_err);
        if (ret) {
            qemu_mutex_unlock(&p->mutex);
            break;
        }

        flags = p->flags;
        /* recv methods don't know how to handle the SYNC flag */
        p->flags &= ~MULTIFD_FLAG_SYNC;

        if (is_device_state) {
            has_data = p->next_packet_size > 0;
        } else {
            /*
             * Even if it's a SYNC packet, this needs to be set
             * because older upstream QEMUs (<9.0) still send data along with
             * the SYNC packet.
             */
            has_data = p->normal_num || p->zero_num || p->skipped_num;
        }

        qemu_mutex_unlock(&p->mutex);

        if (has_data) {
            if (is_device_state) {
                ret = multifd_device_state_recv(p, &local_err);
            } else {
                ret = multifd_recv_state->ops->recv(p, &local_err);
            }
            if (ret != 0) {
                break;
            }
        } else if (is_device_state) {
            error_setg(&local_err,
                       "multifd: received empty device state packet");
            break;
        }

        if (flags & MULTIFD_FLAG_SYNC) {
            if (is_device_state) {
                error_setg(&local_err,
                           "multifd: received SYNC device state packet");
                break;
            }

            qemu_sem_post(&multifd_recv_state->sem_sync);
            qemu_sem_wait(&p->sem_sync);
        }
    }

    if (local_err) {
        multifd_recv_terminate_threads(local_err);
        error_free(local_err);
    }

    rcu_unregister_thread();
    trace_multifd_recv_thread_end(p->id, p->packets_recved);

    return NULL;
}

int multifd_recv_setup(Error **errp)
{
    int thread_count;
    uint32_t pages_per_pkt = multifd_ram_pages_per_packet_count();
    uint8_t i;

    /*
     * Return successfully if multiFD recv state is already initialised
     * or multiFD is not enabled.
     */
    if (multifd_recv_state || !migrate_use_multifd()) {
        return 0;
    }

    if (!migrate_multi_channels_is_allowed()) {
        error_setg(errp, "multifd is not supported by current protocol");
        return -1;
    }
    thread_count = migrate_multifd_channels();
    multifd_recv_state = g_malloc0(sizeof(*multifd_recv_state));
    multifd_recv_state->params = g_new0(MultiFDRecvParams, thread_count);
    qatomic_set(&multifd_recv_state->count, 0);
    qemu_sem_init(&multifd_recv_state->sem_sync, 0);
    multifd_recv_state->ops = multifd_ops[migrate_multifd_compression()];

    for (i = 0; i < thread_count; i++) {
        MultiFDRecvParams *p = &multifd_recv_state->params[i];

        qemu_mutex_init(&p->mutex);
        qemu_sem_init(&p->sem_sync, 0);
        p->quit = false;
        p->id = i;
        p->packet_len = sizeof(MultiFDPacket_t)
                      + sizeof(uint64_t) * pages_per_pkt;
        p->packet = g_malloc0(p->packet_len);
        p->packet_dev_state = g_malloc0(sizeof(*p->packet_dev_state));
        p->name = g_strdup_printf("multifdrecv_%d", i);
        p->iov = g_new0(struct iovec, multifd_ram_iovs_per_packet_count());
        p->normal = g_new0(ram_addr_t, pages_per_pkt);
        p->zero = g_new0(ram_addr_t, pages_per_pkt);
    }

    for (i = 0; i < thread_count; i++) {
        MultiFDRecvParams *p = &multifd_recv_state->params[i];
        Error *local_err = NULL;
        int ret;

        ret = multifd_recv_state->ops->recv_setup(p, &local_err);
        if (ret) {
            error_propagate(errp, local_err);
            return ret;
        }
    }
    return 0;
}

bool multifd_recv_all_channels_created(void)
{
    int thread_count = migrate_multifd_channels();

    if (!migrate_use_multifd()) {
        return true;
    }

    if (!multifd_recv_state) {
        /* Called before any connections created */
        return false;
    }

    return thread_count == qatomic_read(&multifd_recv_state->count);
}

/*
 * Try to receive all multifd channels to get ready for the migration.
 * Sets @errp when failing to receive the current channel.
 */
void multifd_recv_new_channel(QIOChannel *ioc, Error **errp)
{
    MultiFDRecvParams *p;
    Error *local_err = NULL;
    int id;

    id = multifd_recv_initial_packet(ioc, &local_err);
    if (id < 0) {
        multifd_recv_terminate_threads(local_err);
        error_propagate_prepend(errp, local_err,
                                "failed to receive packet"
                                " via multifd channel %d: ",
                                qatomic_read(&multifd_recv_state->count));
        return;
    }
    trace_multifd_recv_new_channel(id);

    p = &multifd_recv_state->params[id];
    if (p->c != NULL) {
        error_setg(&local_err, "multifd: received id '%d' already setup'",
                   id);
        multifd_recv_terminate_threads(local_err);
        error_propagate(errp, local_err);
        return;
    }
    p->c = ioc;
    object_ref(OBJECT(ioc));

    p->thread_created = true;
    qemu_thread_create(&p->thread, p->name, multifd_recv_thread, p,
                       QEMU_THREAD_JOINABLE);
    qatomic_inc(&multifd_recv_state->count);
}

bool multifd_send_prepare_common(MultiFDSendParams *p)
{
    MultiFDPages_t *pages = &p->data->u.ram;
    multifd_send_zero_page_detect(p, NULL);

    if (!pages->normal_num) {
        p->next_packet_size = 0;
        return false;
    }

    multifd_ram_prepare_header(p);

    return true;
}
