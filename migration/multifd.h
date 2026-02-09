/*
 * Multifd common functions
 *
 * Copyright (c) 2019-2020 Red Hat Inc
 *
 * Authors:
 *  Juan Quintela <quintela@redhat.com>
 *
 * This work is licensed under the terms of the GNU GPL, version 2 or later.
 * See the COPYING file in the top-level directory.
 */

#ifndef QEMU_MIGRATION_MULTIFD_H
#define QEMU_MIGRATION_MULTIFD_H

#include "exec/target_page.h"

typedef struct MultiFDSendData MultiFDSendData;

bool multifd_send_setup(void);
void multifd_send_shutdown(void);
int multifd_recv_setup(Error **errp);
void multifd_recv_cleanup(void);
void multifd_recv_shutdown(void);
bool multifd_recv_all_channels_created(void);
void multifd_recv_new_channel(QIOChannel *ioc, Error **errp);
void multifd_recv_sync_main(void);
int multifd_send_sync_main(QEMUFile *f);
bool multifd_queue_page(QEMUFile *f, RAMBlock *block, ram_addr_t offset);

/* Multifd Compression flags */
#define MULTIFD_FLAG_SYNC (1 << 0)

/* We reserve 3 bits for compression methods */
#define MULTIFD_FLAG_COMPRESSION_MASK (7 << 1)
/* we need to be compatible. Before compression value was 0 */
#define MULTIFD_FLAG_NOCOMP (0 << 1)
#define MULTIFD_FLAG_ZLIB (1 << 1)
#define MULTIFD_FLAG_ZSTD (2 << 1)

/*
 * If set it means that this packet contains device state
 * (MultiFDPacketDeviceState_t), not RAM data (MultiFDPacket_t).
 */
#define MULTIFD_FLAG_DEVICE_STATE (32 << 1)

/* This value needs to be a multiple of qemu_target_page_size() */
#define MULTIFD_PACKET_SIZE (512 * 1024)

typedef struct {
    uint32_t magic;
    uint32_t version;
    uint32_t flags;
} __attribute__((packed)) MultiFDPacketHdr_t;

typedef struct {
    MultiFDPacketHdr_t hdr;

    /* maximum number of allocated pages */
    uint32_t pages_alloc;
    /* non zero pages */
    uint32_t normal_pages;
    /* size of the next packet that contains pages */
    uint32_t next_packet_size;
    uint64_t packet_num;
    /* zero pages */
    uint32_t zero_pages;
    /* skipped pages */
    uint32_t skipped_pages;
    uint64_t unused64[3];    /* Reserved for future use */
    char ramblock[256];
    /*
     * This array contains the pointers to:
     *  - normal pages (initial normal_pages entries)
     *  - zero pages (following zero_pages entries)
     */
    uint64_t offset[];
} __attribute__((packed)) MultiFDPacket_t;

typedef struct {
    MultiFDPacketHdr_t hdr;

    char idstr[256];
    uint32_t instance_id;

    /* size of the next packet that contains the actual data */
    uint32_t next_packet_size;
} __attribute__((packed)) MultiFDPacketDeviceState_t;

typedef struct {
    /* number of used pages */
    uint32_t num;
    /* number of skipped pages */
    uint32_t skipped_num;
    /* number of normal pages */
    uint32_t normal_num;
    /*
     * Pointer to the ramblock.  NOTE: it's caller's responsibility to make
     * sure the pointer is always valid!
     */
    RAMBlock *block;
    /* offset array of each page, managed by multifd */
    ram_addr_t *offset;
    /* buffer array of each cached page, managed by multifd */
    void **cached;
    /* temporary buffer for digest computation */
    void *digest;
    /* temporary context for digest computation */
    void *batch_context;
    /* buffer array of each matched digest status, managed by multifd */
    bool *matched;
} MultiFDPages_t;

typedef struct {
    char *idstr;
    uint32_t instance_id;
    char *buf;
    size_t buf_len;
} MultiFDDeviceState_t;

typedef enum {
    MULTIFD_PAYLOAD_NONE,
    MULTIFD_PAYLOAD_RAM,
    MULTIFD_PAYLOAD_DEVICE_STATE,
} MultiFDPayloadType;

typedef struct MultiFDPayload {
    MultiFDPages_t ram;
    MultiFDDeviceState_t device_state;
} MultiFDPayload;

struct MultiFDSendData {
    MultiFDPayloadType type;
    MultiFDPayload u;
};

static inline bool multifd_payload_empty(MultiFDSendData *data)
{
    return data->type == MULTIFD_PAYLOAD_NONE;
}

static inline bool multifd_payload_device_state(MultiFDSendData *data)
{
    return data->type == MULTIFD_PAYLOAD_DEVICE_STATE;
}

static inline void multifd_set_payload_type(MultiFDSendData *data,
                                            MultiFDPayloadType type)
{
    assert(multifd_payload_empty(data));
    assert(type != MULTIFD_PAYLOAD_NONE);

    data->type = type;
}

typedef struct {
    /* Fields are only written at creating/deletion time */
    /* No lock required for them, they are read only */

    /* channel number */
    uint8_t id;
    /* channel thread name */
    char *name;
    /* channel thread id */
    QemuThread thread;
    bool thread_created;
    QemuThread tls_thread;
    bool tls_thread_created;
    /* communication channel */
    QIOChannel *c;
    /* is the yank function registered */
    bool registered_yank;
    /* packet allocated len */
    uint32_t packet_len;
    /* multifd flags for sending ram */
    int write_flags;

    /* sem where to wait for more work */
    QemuSemaphore sem;
    /* syncs main thread and channels */
    QemuSemaphore sem_sync;

    /* multifd flags for each packet */
    uint32_t flags;
    /*
     * The sender thread has work to do if either of below boolean is set.
     *
     * @pending_job:  a job is pending
     * @pending_sync: a sync request is pending
     *
     * For both of these fields, they're only set by the requesters, and
     * cleared by the multifd sender threads.
     */
    bool pending_job;
    bool pending_sync;
    MultiFDSendData *data;

    /* thread local variables. No locking required */

    /* pointers to the possible packet types */
    MultiFDPacket_t *packet;
    MultiFDPacketDeviceState_t *packet_device_state;
    /* size of the next packet that contains pages */
    uint32_t next_packet_size;
    /* packets sent through this channel */
    uint64_t packets_sent;
    /* buffers to send */
    struct iovec *iov;
    /* number of iovs used */
    uint32_t iovs_num;
    /* used for compression methods */
    void *compress_data;
    bool setup_done;
}  MultiFDSendParams;

typedef struct {
    /* Fields are only written at creating/deletion time */
    /* No lock required for them, they are read only */

    /* channel number */
    uint8_t id;
    /* channel thread name */
    char *name;
    /* channel thread id */
    QemuThread thread;
    bool thread_created;
    /* communication channel */
    QIOChannel *c;
    /* packet allocated len */
    uint32_t packet_len;

    /* syncs main thread and channels */
    QemuSemaphore sem_sync;

    /* this mutex protects the following parameters */
    QemuMutex mutex;
    /* should this thread finish */
    bool quit;
    /* multifd flags for each packet */
    uint32_t flags;
    /* global number of generated multifd packets */
    uint64_t packet_num;

    /* thread local variables. No locking required */

    /* pointers to the possible packet types */
    MultiFDPacket_t *packet;
    MultiFDPacketDeviceState_t *packet_dev_state;
    /* size of the next packet that contains pages */
    uint32_t next_packet_size;
    /* packets received through this channel */
    uint64_t packets_recved;
    /* ramblock */
    RAMBlock *block;
    /* ramblock host address */
    uint8_t *host;
    /* buffers to recv */
    struct iovec *iov;
    /* Pages that are not zero */
    ram_addr_t *normal;
    /* num of non zero pages */
    uint32_t normal_num;
    /* Pages that are zero */
    ram_addr_t *zero;
    /* num of zero pages */
    uint32_t zero_num;
    /* num of non zero skipped pages */
    uint32_t skipped_num;
    /* used for de-compression methods */
    void *compress_data;
    /* Flags for the QIOChannel */
    int read_flags;
} MultiFDRecvParams;

typedef struct {
    /* Setup for sending side */
    int (*send_setup)(MultiFDSendParams *p, Error **errp);
    /* Cleanup for sending side */
    void (*send_cleanup)(MultiFDSendParams *p, Error **errp);
    /* Prepare the send packet */
    int (*send_prepare)(MultiFDSendParams *p, Error **errp);
    /* Setup for receiving side */
    int (*recv_setup)(MultiFDRecvParams *p, Error **errp);
    /* Cleanup for receiving side */
    void (*recv_cleanup)(MultiFDRecvParams *p);
    /* Read all data */
    int (*recv)(MultiFDRecvParams *p, Error **errp);
} MultiFDMethods;

void multifd_register_ops(int method, MultiFDMethods *ops);
int multifd_send_fill_packet(MultiFDSendParams *p, Error **errp);
bool multifd_send_prepare_common(MultiFDSendParams *p);
int multifd_send_zero_page_detect(MultiFDSendParams *p, Error **errp);
void multifd_recv_zero_page_process(MultiFDRecvParams *p);

bool multifd_send(MultiFDSendData **send_data);
MultiFDSendData *multifd_send_data_alloc(Error **errp);
void multifd_send_data_clear(MultiFDSendData *data);
void multifd_send_data_free(MultiFDSendData *data);

static inline uint32_t multifd_ram_page_size(void)
{
    return qemu_target_page_size();
}

int multifd_ram_save_setup(Error **errp);
void multifd_ram_save_cleanup(void);

void multifd_send_data_clear_device_state(MultiFDDeviceState_t *device_state);

int multifd_device_state_send_setup(Error **errp);
void multifd_device_state_send_cleanup(void);

void multifd_device_state_send_prepare(MultiFDSendParams *p);

static inline uint32_t multifd_ram_page_count(void)
{
    return MULTIFD_PACKET_SIZE / qemu_target_page_size();
}

/*
 * For compatibility, use multifd_ram_page_count() if hashing is not used.
 */
static inline uint32_t multifd_ram_iovs_per_packet_count(void)
{
    if (migrate_use_hash()) {
        return IOV_MAX;
    }
    /* One iov[0] is used for header packet. */
    return multifd_ram_page_count() + 1;
}

static inline uint32_t multifd_ram_pages_per_packet_count(void)
{
    if (migrate_use_hash()) {
        return multifd_ram_iovs_per_packet_count() - 1;
    }
    return multifd_ram_page_count();
}

static inline uint32_t multifd_ram_pages_per_work_count(void)
{
    if (migrate_use_hash()) {
        return QEMU_ALIGN_UP(MAX(migrate_scan_pages(),
                             multifd_ram_pages_per_packet_count()), 512);
    }
    return multifd_ram_page_count();
}

#endif
