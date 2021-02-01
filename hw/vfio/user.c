

/*
 * vfio protocol over a UNIX socket.
 *
 * This work is licensed under the terms of the GNU GPL, version 2.  See
 * the COPYING file in the top-level directory.
 *
 */

#include "qemu/osdep.h"
#include <linux/vfio.h>
#include <sys/ioctl.h>

#include "hw/hw.h"
#include "hw/vfio/vfio-common.h"
#include "hw/vfio/vfio.h"
#include "hw/qdev-properties.h"
#include "migration/vmstate.h"
#include "qemu/error-report.h"
#include "qemu/main-loop.h"
#include "qemu/module.h"
#include "qemu/option.h"
#include "qemu/range.h"
#include "qemu/sockets.h"
#include "qemu/units.h"
#include "qemu/qemu-print.h"
#include "io/channel.h"
#include "io/channel-util.h"
#include "qapi/qmp/qdict.h"
#include "qapi/qmp/qjson.h"
#include "qapi/qmp/qnull.h"
#include "qapi/qmp/qstring.h"
#include "qapi/qmp/qnum.h"
#include "sysemu/kvm.h"
#include "sysemu/runstate.h"
#include "sysemu/sysemu.h"
#include "sysemu/iothread.h"
#include "user.h"
#include "trace.h"
#include "qapi/error.h"
#include "migration/blocker.h"


static void vfio_user_request_msg(vfio_user_hdr_t *hdr, uint16_t cmd, uint32_t size,
                                  uint32_t flags);

static void vfio_user_send_locked(VFIOProxy *proxy, vfio_user_hdr_t *msg, VFIOUserFDs *fds);
static void vfio_user_send(VFIOProxy *proxy, vfio_user_hdr_t *msg, VFIOUserFDs *fds);
static void vfio_user_send_recv(VFIOProxy *proxy, vfio_user_hdr_t *msg, VFIOUserFDs *fds,
                               int rsize);


static uint64_t max_send_fds = VFIO_USER_DEF_MAX_FDS;
static uint64_t max_msg_size = VFIO_USER_DEF_MAX_MSG;


static void vfio_user_request_msg(vfio_user_hdr_t *hdr, uint16_t cmd, uint32_t size,
                                  uint32_t flags)
{
    static uint16_t next_id = 0;

    hdr->id = next_id++;
    hdr->command = cmd;
    hdr->size = size;
    hdr->flags = (flags & ~VFIO_USER_TYPE) | VFIO_USER_REQUEST;
    hdr->error_reply = 0;
}

void vfio_user_send_reply(VFIOProxy *proxy, char *buf, int ret)
{
    vfio_user_hdr_t *hdr = (vfio_user_hdr_t *)buf;

    /*
     * convert header to associated reply
     * positive ret is reply size, negative is error code
     */
    hdr->flags = VFIO_USER_REPLY;
    if (ret > 0) {
        hdr->size = ret;
    } else if (ret < 0) {
        hdr->flags |= VFIO_USER_ERROR;
        hdr->error_reply = -ret;
        hdr->size = sizeof(*hdr);
    }
    vfio_user_send(proxy, hdr, NULL);
}

void vfio_user_recv(void *opaque)
{
    VFIODevice *vbasedev = opaque;
    VFIOProxy *proxy = vbasedev->proxy;
    VFIOUserReply *reply = NULL;
    int *fdp = NULL;
    VFIOUserFDs reqfds = { 0, 0, fdp };
    vfio_user_hdr_t msg;
    struct iovec iov = {
        .iov_base = &msg,
        .iov_len = sizeof(msg),
    };
    int isreply, i, ret;
    size_t msgleft, numfds = 0;
    char *data, *buf = NULL;
    Error *local_err = NULL;

    qemu_mutex_lock(&proxy->lock);

    ret = qio_channel_readv_full(proxy->ioc, &iov, 1, &fdp, &numfds, &local_err);
    if (ret < 0) {
        goto err;
    }
    if (ret < sizeof(msg)) {
        error_setg(&local_err, "vfio_user_recv short read of header");
        goto err;
    }

    /*
     * For replies, find the matching pending request
     */
    isreply = (msg.flags & VFIO_USER_TYPE) == VFIO_USER_REPLY;
    if (isreply) {
         QTAILQ_FOREACH(reply, &proxy->pending, next) {
            if (msg.id == reply->id) {
                break;
            }
        }
        if (reply == NULL) {
            error_setg(&local_err, "vfio_user_recv unexpected reply");
            goto err;
        }
        QTAILQ_REMOVE(&proxy->pending, reply, next);

        /*
         * Process any received FDs
         */
        if (numfds != 0) {
            if (reply->fds == NULL || reply->fds->recv_fds < numfds) {
                error_setg(&local_err, "vfio_user_recv unexpected FDs");
                goto err;
            }
            reply->fds->recv_fds = numfds;
            memcpy(reply->fds->fds, fdp, numfds * sizeof(int));
        }

    } else {
        /* 
         * The client doesn't expect any FDs in requests, but
         * they will be expected on the server
         */
        if (numfds != 0 && (proxy->flags & VFIO_PROXY_CLIENT)) {
            error_setg(&local_err, "vfio_user_recv fd in client reply");
            goto err;
        }
        reqfds.recv_fds = numfds;
    }

    /*
     * put the whole message into a single buffer
     */
    msgleft = msg.size - sizeof(msg);
    if (isreply) {
        if (msg.size > reply->rsize) {
            error_setg(&local_err, "vfio_user_recv reply larger than recv buffer");
            goto err;
        }
        *reply->msg = msg;
        data = (char *)reply->msg + sizeof(msg);
    } else {
        buf = g_malloc0(msg.size);
        memcpy(buf, &msg, sizeof(msg));
        data = buf + sizeof(msg);
    }

    if (msgleft != 0) {
        ret = qio_channel_read(proxy->ioc, data, msgleft, &local_err);
        if (ret < 0) {
            goto err;
        }
        if (ret != msgleft) {
            error_setg(&local_err, "vfio_user_recv short read of msg body");
            goto err;
        }
    }

    /*
     * Replies signal a waiter, requests get processed by vfio code
     * that may assume the iothread lock is held.
     */
    qemu_mutex_unlock(&proxy->lock);
    if (isreply) {
        reply->complete = 1;
        qemu_cond_signal(&reply->cv);
    } else {
        qemu_mutex_lock_iothread();
        ret = proxy->request(proxy->reqarg, buf, &reqfds);
        if (ret < 0) {
            vfio_user_send_reply(proxy, buf, ret);
        }
        qemu_mutex_unlock_iothread();
        g_free(buf);
    }

    if (fdp != NULL) {
        g_free(fdp);
    }
    return;

err:
    qemu_mutex_unlock(&proxy->lock);
    for (i = 0; i < numfds; i++) {
        close(fdp[i]);
    }
    if (fdp != NULL) {
        g_free(fdp);
    }
    if (buf != NULL) {
        g_free(buf);
    }
    if (reply != NULL) {
        /* force an error to keep sending thread from hanging */
        reply->msg->flags |= VFIO_USER_ERROR;
        reply->msg->error_reply = EINVAL;
        reply->complete = 1;
        qemu_cond_signal(&reply->cv);
    }
    error_report_err(local_err);
}
    
            
static void vfio_user_send_locked(VFIOProxy *proxy, vfio_user_hdr_t *msg, VFIOUserFDs *fds)
{
    struct iovec iov = {
        .iov_base = msg,
        .iov_len = msg->size,
    };
    size_t numfds = 0;
    int msgleft, ret, *fdp = NULL;
    char *buf;
    Error *local_err = NULL;

    if (fds != NULL && fds->send_fds != 0) {
        numfds = fds->send_fds;
        fdp = fds->fds;
    }
    ret = qio_channel_writev_full(proxy->ioc, &iov, 1, fdp, numfds, &local_err);
    if (ret < 0) {
        goto err;
    }
    if (ret == msg->size) {
        return;
    }

    buf = iov.iov_base + ret;
    msgleft = iov.iov_len - ret;
    do {
        ret = qio_channel_write(proxy->ioc, buf, msgleft, &local_err);
        if (ret < 0) {
            goto err;
        }
        buf += ret, msgleft -= ret;
    } while (msgleft != 0);
    return;

err:
    error_report_err(local_err);
}

static void vfio_user_send(VFIOProxy *proxy, vfio_user_hdr_t *msg, VFIOUserFDs *fds)
{
    /* Use the same locking protocol as vfio_user_send_recv() below */
    qemu_mutex_unlock_iothread();
    qemu_mutex_lock(&proxy->lock);
    vfio_user_send_locked(proxy, msg, fds);
    qemu_mutex_unlock(&proxy->lock);
    qemu_mutex_lock_iothread();
}

static void vfio_user_send_recv(VFIOProxy *proxy, vfio_user_hdr_t *msg, VFIOUserFDs *fds,
                               int rsize)
{
    VFIOUserReply *reply;

    if (msg->flags & VFIO_USER_NO_REPLY) {
        error_printf("vfio_user_send_recv on async message\n");
        return;
    }

    /*
     * We will block later, so use a per-proxy lock and let
     * the iothreads run while we sleep.
     */
    qemu_mutex_unlock_iothread();
    qemu_mutex_lock(&proxy->lock);

    reply = QTAILQ_FIRST(&proxy->free);
    if (reply != NULL) {
        QTAILQ_REMOVE(&proxy->free, reply, next);
        reply->complete = 0;
    } else {
        reply = g_malloc0(sizeof(*reply));
        qemu_cond_init(&reply->cv);
    }
    reply->msg = msg;
    reply->fds = fds;
    reply->id = msg->id;
    reply->rsize = rsize ? rsize : msg->size;
    QTAILQ_INSERT_TAIL(&proxy->pending, reply, next);

    vfio_user_send_locked(proxy, msg, fds);
    while (reply->complete == 0) {
        qemu_cond_wait(&reply->cv, &proxy->lock);
    }

    QTAILQ_INSERT_HEAD(&proxy->free, reply, next);
    qemu_mutex_unlock(&proxy->lock);
    qemu_mutex_lock_iothread();
}

static IOThread *vfio_user_iothread;

static QLIST_HEAD(, VFIOProxy) vfio_user_sockets =
    QLIST_HEAD_INITIALIZER(vfio_user_sockets);

VFIOProxy *vfio_user_connect_dev(char *sockname, Error **errp)
{
    VFIOProxy *proxy;
    int sockfd;

    sockfd = unix_connect(sockname, errp);
    if (sockfd == -1) {
        return NULL;
    }

    proxy = g_malloc0(sizeof(VFIOProxy));
    proxy->sockname = sockname;
    proxy->flags = VFIO_PROXY_CLIENT;

    proxy->ioc = qio_channel_new_fd(sockfd, errp);
    qio_channel_set_blocking(proxy->ioc, true, NULL);

    if (vfio_user_iothread == NULL) {
        vfio_user_iothread = iothread_create("VFIO user", errp);
    }

    qemu_mutex_init(&proxy->lock);
    QTAILQ_INIT(&proxy->free);
    QTAILQ_INIT(&proxy->pending);
    QLIST_INSERT_HEAD(&vfio_user_sockets, proxy, next);

    return proxy;
}

void vfio_user_set_reqhandler(VFIODevice *vbasedev,
                              int (*handler)(void *opaque, char *buf, VFIOUserFDs *fds),
                              void *reqarg)
{
    VFIOProxy *proxy = vbasedev->proxy;

    proxy->request = handler;
    proxy->reqarg = reqarg;
    qio_channel_set_aio_fd_handler(proxy->ioc,
                                   iothread_get_aio_context(vfio_user_iothread),
                                   vfio_user_recv, NULL, vbasedev);
}

void vfio_user_disconnect(VFIOProxy *proxy)
{
    VFIOUserReply *r1, *r2;

    qio_channel_shutdown(proxy->ioc, QIO_CHANNEL_SHUTDOWN_READ, NULL);
    qio_channel_set_aio_fd_handler(proxy->ioc,
                                   iothread_get_aio_context(vfio_user_iothread),
                                   NULL, NULL, NULL);

    qemu_mutex_lock(&proxy->lock);
    QTAILQ_FOREACH_SAFE(r1, &proxy->free, next, r2) {
        qemu_cond_destroy(&r1->cv);
        QTAILQ_REMOVE(&proxy->free, r1, next);
        g_free(r1);
    }
    QTAILQ_FOREACH_SAFE(r1, &proxy->pending, next, r2) {
        qemu_cond_destroy(&r1->cv);
        QTAILQ_REMOVE(&proxy->pending, r1, next);
        g_free(r1);
    }
    qemu_mutex_unlock(&proxy->lock);
    qemu_mutex_destroy(&proxy->lock);

    QLIST_REMOVE(proxy, next);
    if (QLIST_EMPTY(&vfio_user_sockets)) {
        iothread_destroy(vfio_user_iothread);
        vfio_user_iothread = NULL;
    }

    qio_channel_close(proxy->ioc, NULL);
    g_free(proxy);
}


struct cap_entry {
    const char *name;
    int (*check)(QObject *qobj, Error **errp);
};

static int caps_parse(QDict *qdict, struct cap_entry caps[], Error **errp)
{
    QObject *qobj;
    struct cap_entry *p;

    for (p = caps; p->name != NULL; p++) {
        qobj = qdict_get(qdict, p->name);
        if (qobj != NULL) {
            if (p->check(qobj, errp)) {
                 return -1;
            }
            qdict_del(qdict, p->name);
        }
    }

    /* warning, for now */
    if (qdict_size(qdict) != 0) {
        error_printf("spurious capabilities\n");
    }
    return 0;
}

static int check_pgsize(QObject *qobj, Error **errp)
{
    QNum *qn = qobject_to(QNum, qobj);
    uint64_t pgsize;

    if (qn == NULL || !qnum_get_try_uint(qn, &pgsize)) {
        error_setg(errp, "malformed %s", VFIO_USER_CAP_PGSIZE);
        return -1;
    }
    return pgsize == 4096 ? 0 : -1;
}

static struct cap_entry caps_migr[] = {
    { VFIO_USER_CAP_PGSIZE, check_pgsize },
    { NULL }
};

static int check_max_fds(QObject *qobj, Error **errp)
{
    QNum *qn = qobject_to(QNum, qobj);

    if (qn == NULL || !qnum_get_try_uint(qn, &max_send_fds) ||
        max_send_fds > VFIO_USER_MAX_MAX_FDS) {
        error_setg(errp, "malformed %s", VFIO_USER_CAP_MAX_FDS);
        return -1;
    }
    return 0;
}

static int check_max_msg(QObject *qobj, Error **errp)
{
    QNum *qn = qobject_to(QNum, qobj);

    if (qn == NULL || !qnum_get_try_uint(qn, &max_msg_size) ||
        max_msg_size > VFIO_USER_MAX_MAX_MSG) {
        error_setg(errp, "malformed %s", VFIO_USER_CAP_MAX_MSG);
        return -1;
    }
    return 0;
}

static int check_migr(QObject *qobj, Error **errp)
{
    QDict *qdict = qobject_to(QDict, qobj);

    if (qdict == NULL || caps_parse(qdict, caps_migr, errp)) {
        error_setg(errp, "malformed %s", VFIO_USER_CAP_MAX_FDS);
        return -1;
    }
    return 0;
}

static struct cap_entry caps_cap[] = {
    { VFIO_USER_CAP_MAX_FDS, check_max_fds },
    { VFIO_USER_CAP_MAX_MSG, check_max_msg },
    { VFIO_USER_CAP_MIGR, check_migr },
    { NULL }
};

static int check_cap(QObject *qobj, Error **errp)
{
   QDict *qdict = qobject_to(QDict, qobj);

    if (qdict == NULL || caps_parse(qdict, caps_cap, errp)) {
        error_setg(errp, "malformed %s", VFIO_USER_CAP);
        return -1;
    }
    return 0;
}

static struct cap_entry ver_0_0[] = {
    { VFIO_USER_CAP, check_cap },
    { NULL }
};

static int caps_check(int minor, const char *caps, Error **errp)
{
    QObject *qobj;
    QDict *qdict;
    int ret;

    qobj = qobject_from_json(caps, NULL);
    if (qobj == NULL) {
        error_setg(errp, "malformed capabilities %s", caps);
        return -1;
    }
    qdict = qobject_to(QDict, qobj);
    if (qdict == NULL) {
        error_setg(errp, "capabilities %s not an object", caps);
        qobject_unref(qobj);
        return -1;
    }
    ret = caps_parse(qdict, ver_0_0, errp);

    qobject_unref(qobj);
    return ret;
}

static GString *caps_json(void)
{
    QDict *dict = qdict_new();
    QDict *capdict = qdict_new();
    QDict *migdict = qdict_new();
    GString *str;

    qdict_put_int(migdict, VFIO_USER_CAP_PGSIZE, 4096);

    qdict_put_obj(capdict, VFIO_USER_CAP_MIGR, QOBJECT(migdict));
    qdict_put_int(capdict, VFIO_USER_CAP_MAX_FDS, VFIO_USER_MAX_MAX_FDS);
    qdict_put_int(capdict, VFIO_USER_CAP_MAX_MSG, VFIO_USER_DEF_MAX_MSG);

    qdict_put_obj(dict, VFIO_USER_CAP, QOBJECT(capdict));

    str = qobject_to_json(QOBJECT(dict));
    qobject_unref(dict);
    return str;
}

int vfio_user_validate_version(VFIODevice *vbasedev, Error **errp)
{
    struct vfio_user_version *msgp;
    GString *caps;
    int size, caplen;

    caps = caps_json();
    caplen = caps->len + 1;
    size = sizeof (*msgp) + caplen;
    msgp = g_malloc0(size);

    vfio_user_request_msg(&msgp->hdr, VFIO_USER_VERSION, size, 0);
    msgp->major = VFIO_USER_MAJOR_VER;
    msgp->minor = VFIO_USER_MINOR_VER;
    memcpy(&msgp->capabilities, caps->str, caplen);
    g_string_free(caps, true);

    vfio_user_send_recv(vbasedev->proxy, &msgp->hdr, NULL, 0);
    if (msgp->hdr.flags & VFIO_USER_ERROR) {
        error_setg_errno(errp, msgp->hdr.error_reply, "version reply");
        goto err;
    }

    if (msgp->major != VFIO_USER_MAJOR_VER || msgp->minor > VFIO_USER_MINOR_VER) {
        error_setg(errp, "incompatible server version");
        goto err;
    }
    if (caps_check(msgp->minor, (char *)msgp + sizeof(*msgp), errp) != 0) {
        goto err;
    }

    g_free(msgp);
    return 0;

err:
    g_free(msgp);
    return -1;
}

int vfio_user_dma_map(VFIOProxy *proxy, struct vfio_user_map *map, VFIOUserFDs *fds,
                      uint64_t nelem)
{
    struct vfio_user_dma_map *msgp;
    int ret, size, sent_elem, send_elem;

    /*
     * Handle simple case
     */
    if (fds == NULL) {
        size = sizeof(*msgp) + (nelem * sizeof(struct vfio_user_map));

        msgp = g_malloc0(size);
        vfio_user_request_msg(&msgp->hdr, VFIO_USER_DMA_MAP, size, 0);
        memcpy(&msgp->table, map, nelem * sizeof(*map));

        vfio_user_send_recv(proxy, &msgp->hdr, NULL, 0);
        ret = (msgp->hdr.flags & VFIO_USER_ERROR) ? -msgp->hdr.error_reply : 0;

        g_free(msgp);
        return ret;
    }

    if (fds->send_fds != nelem) {
        error_printf("vfio_user_dma_map mismatch of FDs and table elements\n");
        return -EINVAL;
    }
    if (fds->recv_fds != 0) {
        error_printf("vfio_user_dma_map can't receive FDs\n");
        return -EINVAL;
    }

    /*
     * Send in chunks if over max_send_fds
     */
    for (sent_elem = 0; nelem > sent_elem; sent_elem += send_elem) {
        VFIOUserFDs loop_fds;

        send_elem = MIN(nelem - sent_elem, max_send_fds);
        size = sizeof(*msgp) + (send_elem * sizeof(struct vfio_user_map));

        msgp = g_malloc0(size);
        vfio_user_request_msg(&msgp->hdr, VFIO_USER_DMA_MAP, size, 0);
        memcpy(&msgp->table, map + sent_elem, send_elem * sizeof(*map));

        loop_fds.send_fds = send_elem;
        loop_fds.recv_fds = 0;
        loop_fds.fds = fds->fds + sent_elem;

        vfio_user_send_recv(proxy, &msgp->hdr, &loop_fds, 0);
        ret = (msgp->hdr.flags & VFIO_USER_ERROR) ? -msgp->hdr.error_reply : 0;

        g_free(msgp);
        if (ret < 0 ) {
            return ret;
        }
    }
    return 0;
}

int vfio_user_dma_unmap(VFIOProxy *proxy, struct vfio_user_map *map,
                               uint64_t nelem)
{
    struct vfio_user_dma_map *msgp;
    int size = sizeof(*msgp) + (nelem * sizeof(struct vfio_user_map));
    int ret;

    msgp = g_malloc0(size);
    vfio_user_request_msg(&msgp->hdr, VFIO_USER_DMA_UNMAP, size, 0);
    memcpy(&msgp->table, map, nelem * sizeof(*map));

    vfio_user_send_recv(proxy, &msgp->hdr, NULL, 0);
    ret = (msgp->hdr.flags & VFIO_USER_ERROR) ? -msgp->hdr.error_reply : 0;

    g_free(msgp);
    return ret;
}

int vfio_user_get_info(VFIODevice *vbasedev)
{
    struct vfio_user_device_info msg;
    struct vfio_device_info *info;

    memset(&msg, 0, sizeof(msg));
    vfio_user_request_msg(&msg.hdr, VFIO_USER_DEVICE_GET_INFO, sizeof(msg), 0);

    vfio_user_send_recv(vbasedev->proxy, &msg.hdr, NULL, 0);
    if (msg.hdr.flags & VFIO_USER_ERROR) {
        return -msg.hdr.error_reply;
    }

    info = &msg.dev_info;
    vbasedev->num_irqs = info->num_irqs;
    vbasedev->num_regions = info->num_regions;
    vbasedev->flags = info->flags;
    vbasedev->reset_works = !!(info->flags & VFIO_DEVICE_FLAGS_RESET);
    return 0;
}

int vfio_user_get_region_info(VFIODevice *vbasedev, int index,
                              struct vfio_region_info *info, VFIOUserFDs *fds)
{
    struct vfio_user_region_info *msgp;
    int size;

    /* data returned can be larger than vfio_region_info */
    if (info->argsz < sizeof(*info)) {
        error_printf("vfio_user_get_region_info argsz too small\n");
        return -EINVAL;
    }
    if (fds != NULL && fds->send_fds != 0) {
        error_printf("vfio_user_get_region_info can't send FDs\n");
        return -EINVAL;
    }

    size = info->argsz + sizeof(vfio_user_hdr_t);
    msgp = g_malloc0(size);

    vfio_user_request_msg(&msgp->hdr, VFIO_USER_DEVICE_GET_REGION_INFO, sizeof(*msgp), 0);
    msgp->reg_info = *info;

    vfio_user_send_recv(vbasedev->proxy, &msgp->hdr, fds, size);
    if (msgp->hdr.flags & VFIO_USER_ERROR) {
        g_free(msgp);
        return -msgp->hdr.error_reply;
    }

    memcpy(info, &msgp->reg_info, info->argsz);
    g_free(msgp);
    return 0;
}

int vfio_user_get_irq_info(VFIODevice *vbasedev, struct vfio_irq_info *info)
{
    struct vfio_user_irq_info msg;

    memset(&msg, 0, sizeof(msg));
    vfio_user_request_msg(&msg.hdr, VFIO_USER_DEVICE_GET_IRQ_INFO, sizeof(msg), 0);

    vfio_user_send_recv(vbasedev->proxy, &msg.hdr, NULL, 0);
    if (msg.hdr.flags & VFIO_USER_ERROR) {
        return -msg.hdr.error_reply;
    }

    *info = msg.irq_info;
    return 0;
}

int vfio_user_set_irqs(VFIODevice *vbasedev, struct vfio_irq_set *irq)
{
    struct vfio_user_irq_set *msgp;
    uint32_t size, nfds, send_fds, sent_fds;

    if (irq->argsz < sizeof(*irq)) {
        error_printf("vfio_user_set_irqs argsz too small\n");
        return -EINVAL;
    }

    /*
     * Handle simple case
     */
    if ((irq->flags & VFIO_IRQ_SET_DATA_EVENTFD) == 0) {
        size = sizeof(vfio_user_hdr_t) + irq->argsz;
        msgp = g_malloc0(size);

        vfio_user_request_msg(&msgp->hdr, VFIO_USER_DEVICE_SET_IRQS, size, 0);
        memcpy(&msgp->irq_set, irq, irq->argsz);

        vfio_user_send_recv(vbasedev->proxy, &msgp->hdr, NULL, 0);
        if (msgp->hdr.flags & VFIO_USER_ERROR) {
            g_free(msgp);
            return -msgp->hdr.error_reply;
        }

        g_free(msgp);
        return 0;
    }

    /*
     * Calculate the number of FDs to send
     * and adjust argsz
     */
    nfds = (irq->argsz - sizeof(*irq)) / sizeof (int);
    irq->argsz = sizeof(*irq);
    msgp = g_malloc0(sizeof(*msgp));

    /*
     * Send in chunks if over max_send_fds
     */
    for (sent_fds = 0; nfds > sent_fds; sent_fds += send_fds) {
        VFIOUserFDs loop_fds;

        send_fds = MIN(nfds - sent_fds, max_send_fds);

        vfio_user_request_msg(&msgp->hdr, VFIO_USER_DEVICE_SET_IRQS, sizeof(*msgp), 0);
        memcpy(&msgp->irq_set, irq, irq->argsz);
        msgp->irq_set.start += sent_fds;
        msgp->irq_set.count = send_fds;

        loop_fds.send_fds = send_fds;
        loop_fds.recv_fds = 0;
        loop_fds.fds = (int *)irq->data + sent_fds;

        vfio_user_send_recv(vbasedev->proxy, &msgp->hdr, &loop_fds, 0);
        if (msgp->hdr.flags & VFIO_USER_ERROR) {
            g_free(msgp);
            return -msgp->hdr.error_reply;
        }
    }

    g_free(msgp);
    return 0;
}

int vfio_user_region_read(VFIODevice *vbasedev, uint32_t index, uint64_t offset,
                                 uint32_t count, void *data)
{
    struct {
        struct vfio_user_region_rw msg;
        char buf[8];
    } smallmsg;
    struct vfio_user_region_rw *msgp;
    int ret, size = sizeof(*msgp) + count;

    /* most reads are just registers, only allocate for larger ones */
    msgp = count > 8 ? g_malloc0(size) : &smallmsg.msg;
    vfio_user_request_msg(&msgp->hdr, VFIO_USER_REGION_READ, sizeof(*msgp), 0);
    msgp->offset = offset;
    msgp->region = index;
    msgp->count = count;

    vfio_user_send_recv(vbasedev->proxy, &msgp->hdr, NULL, size);
    if (msgp->hdr.flags & VFIO_USER_ERROR) {
        ret = -msgp->hdr.error_reply;
    } else if (msgp->count > count) {
        ret = -E2BIG;
    } else {
        ret = 0;
        memcpy(data, &msgp->data, msgp->count);
    }

    if (msgp != &smallmsg.msg) {
        g_free(msgp);
    }
    return ret < 0 ? ret : msgp->count;
}

int vfio_user_region_write(VFIODevice *vbasedev, uint32_t index, uint64_t offset,
                                  uint32_t count, void *data)
{
     struct {
        struct vfio_user_region_rw msg;
        char buf[8];
    } smallmsg;
    struct vfio_user_region_rw *msgp;
    int size = sizeof(*msgp) + count;

    /* most writes are just registers, only allocate for larger ones */
    msgp = count > 8 ? g_malloc0(size) : &smallmsg.msg;
    vfio_user_request_msg(&msgp->hdr, VFIO_USER_REGION_WRITE, size, VFIO_USER_NO_REPLY);
    msgp->offset = offset;
    msgp->region = index;
    msgp->count = count;
    memcpy(&msgp->data, data, count);

    vfio_user_send(vbasedev->proxy, &msgp->hdr, NULL);

    if (msgp != &smallmsg.msg) {
        g_free(msgp);
    }
    return count;
}

void vfio_user_reset(VFIODevice *vbasedev)
{
    vfio_user_hdr_t msg;

    vfio_user_request_msg(&msg, VFIO_USER_DEVICE_RESET, sizeof(msg), 0);

    vfio_user_send_recv(vbasedev->proxy, &msg, NULL, 0);
    if (msg.flags & VFIO_USER_ERROR) {
        error_printf("reset reply error %d\n", msg.error_reply);
    }
}

int vfio_user_dirty_bitmap(VFIOProxy *proxy,
                           struct vfio_iommu_type1_dirty_bitmap *cmd,
                           struct vfio_iommu_type1_dirty_bitmap_get *dbitmap)
{
    struct {
        struct vfio_user_dirty_pages msg;
        struct vfio_user_bitmap_range range;
    } *msgp;
    int msize, rsize;

    /*
     * If just the command is sent, the returned bitmap isn't needed.
     * The bitmap structs are different from the ioctl() versions,
     * ioctl() returns the bitmap in a local VA
     */
    if (dbitmap != NULL) {
        msize = sizeof(*msgp);
        rsize = msize + dbitmap->bitmap.size;
        msgp = g_malloc0(rsize);
        msgp->range.iova = dbitmap->iova;
        msgp->range.size = dbitmap->size;
        msgp->range.bitmap.pgsize = dbitmap->bitmap.pgsize;
        msgp->range.bitmap.size = dbitmap->bitmap.size;
    } else {
        msize = rsize = sizeof(struct vfio_user_dirty_pages);
        msgp = g_malloc0(rsize);
    }

    vfio_user_request_msg(&msgp->msg.hdr, VFIO_USER_DIRTY_PAGES, msize, 0);
    msgp->msg.command = *cmd;

    vfio_user_send_recv(proxy, &msgp->msg.hdr, NULL, rsize);
    if (msgp->msg.hdr.flags & VFIO_USER_ERROR) {
        g_free(msgp);
        return -msgp->msg.hdr.error_reply;
    }

    if (dbitmap != NULL) {
        memcpy(dbitmap->bitmap.data, &msgp->range.bitmap.data, dbitmap->bitmap.size);
    }

    g_free(msgp);
    return 0;
}

int vfio_user_unmap_dirty(VFIOProxy *proxy,
                          struct vfio_iommu_type1_dma_unmap *unmap,
                          struct vfio_bitmap *bitmap)
{
    struct vfio_user_unmap_dirty *msgp;
    int size;

    size = unmap->argsz + bitmap->size;
    msgp = g_malloc0(size);
    msgp->unmap = *unmap;
    msgp->bitmap.pgsize = bitmap->pgsize;
    msgp->bitmap.size = bitmap->size;

    vfio_user_request_msg(&msgp->hdr, VFIO_USER_UNMAP_DIRTY, unmap->size, 0);
    
    vfio_user_send_recv(proxy, &msgp->hdr, NULL, size);
    if (msgp->hdr.flags & VFIO_USER_ERROR) {
        g_free(msgp);
        return -msgp->hdr.error_reply;
    }

    memcpy(bitmap->data, &msgp->bitmap.data, bitmap->size);

    g_free(msgp);
    return 0;
}
