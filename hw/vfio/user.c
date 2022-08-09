/*
 * vfio protocol over a UNIX socket.
 *
 * Copyright © 2018, 2021 Oracle and/or its affiliates.
 *
 * This work is licensed under the terms of the GNU GPL, version 2 or later.
 * See the COPYING file in the top-level directory.
 *
 */

#include "qemu/osdep.h"
#include <linux/vfio.h>
#include <sys/ioctl.h>

#include "qemu/error-report.h"
#include "qapi/error.h"
#include "qemu/main-loop.h"
#include "qemu/lockable.h"
#include "hw/hw.h"
#include "hw/vfio/vfio-common.h"
#include "hw/vfio/vfio.h"
#include "exec/address-spaces.h"
#include "exec/memory.h"
#include "exec/ram_addr.h"
#include "qemu/sockets.h"
#include "io/channel.h"
#include "io/channel-socket.h"
#include "io/channel-util.h"
#include "sysemu/reset.h"
#include "sysemu/iothread.h"
#include "qapi/qmp/qdict.h"
#include "qapi/qmp/qjson.h"
#include "qapi/qmp/qnull.h"
#include "qapi/qmp/qstring.h"
#include "qapi/qmp/qnum.h"
#include "qapi/qmp/qbool.h"
#include "user.h"
#include "trace.h"


/*
 * These are to defend against a malign server trying
 * to force us to run out of memory.
 */
#define VFIO_USER_MAX_REGIONS   100
#define VFIO_USER_MAX_IRQS      50

static IOThread *vfio_user_iothread;

static void vfio_user_shutdown(VFIOUserProxy *proxy);
static int vfio_user_send_qio(VFIOUserProxy *proxy, VFIOUserMsg *msg);
static VFIOUserMsg *vfio_user_getmsg(VFIOUserProxy *proxy, VFIOUserHdr *hdr,
                                     VFIOUserFDs *fds);
static VFIOUserFDs *vfio_user_getfds(int numfds);
static void vfio_user_recycle(VFIOUserProxy *proxy, VFIOUserMsg *msg);

static void vfio_user_recv(void *opaque);
static int vfio_user_recv_one(VFIOUserProxy *proxy);
static void vfio_user_send(void *opaque);
static int vfio_user_send_one(VFIOUserProxy *proxy);
static void vfio_user_cb(void *opaque);

static void vfio_user_request(void *opaque);
static int vfio_user_send_queued(VFIOUserProxy *proxy, VFIOUserMsg *msg);
static void vfio_user_send_async(VFIOUserProxy *proxy, VFIOUserHdr *hdr,
                                 VFIOUserFDs *fds);
static void vfio_user_send_nowait(VFIOUserProxy *proxy, VFIOUserHdr *hdr,
                                  VFIOUserFDs *fds, int rsize);
static void vfio_user_send_wait(VFIOUserProxy *proxy, VFIOUserHdr *hdr,
                                VFIOUserFDs *fds, int rsize, bool nobql);
static void vfio_user_wait_reqs(VFIOUserProxy *proxy);
static void vfio_user_request_msg(VFIOUserHdr *hdr, uint16_t cmd,
                                  uint32_t size, uint32_t flags);
static void vfio_user_flush_multi(VFIOUserProxy *proxy);

static int vfio_user_get_info(VFIOUserProxy *proxy,
                              struct vfio_device_info *info);

static inline void vfio_user_set_error(VFIOUserHdr *hdr, uint32_t err)
{
    hdr->flags |= VFIO_USER_ERROR;
    hdr->error_reply = err;
}

/*
 * Functions called by main, CPU, or iothread threads
 */

static void vfio_user_shutdown(VFIOUserProxy *proxy)
{
    qio_channel_shutdown(proxy->ioc, QIO_CHANNEL_SHUTDOWN_READ, NULL);
    qio_channel_set_aio_fd_handler(proxy->ioc, proxy->ctx, NULL, NULL, NULL);
}

static int vfio_user_send_qio(VFIOUserProxy *proxy, VFIOUserMsg *msg)
{
    VFIOUserFDs *fds =  msg->fds;
    struct iovec iov = {
        .iov_base = msg->hdr,
        .iov_len = msg->hdr->size,
    };
    size_t numfds = 0;
    int ret, *fdp = NULL;
    Error *local_err = NULL;

    if (fds != NULL && fds->send_fds != 0) {
        numfds = fds->send_fds;
        fdp = fds->fds;
    }

    ret = qio_channel_writev_full(proxy->ioc, &iov, 1, fdp, numfds, 0,
                                  &local_err);

    if (ret == -1) {
        vfio_user_set_error(msg->hdr, EIO);
        vfio_user_shutdown(proxy);
        error_report_err(local_err);
    }
    trace_vfio_user_send_write(msg->hdr->id, ret);

    return ret;
}

static VFIOUserMsg *vfio_user_getmsg(VFIOUserProxy *proxy, VFIOUserHdr *hdr,
                                     VFIOUserFDs *fds)
{
    VFIOUserMsg *msg;

    msg = QTAILQ_FIRST(&proxy->free);
    if (msg != NULL) {
        QTAILQ_REMOVE(&proxy->free, msg, next);
    } else {
        msg = g_malloc0(sizeof(*msg));
        qemu_cond_init(&msg->cv);
    }

    msg->hdr = hdr;
    msg->fds = fds;
    return msg;
}

/*
 * Recycle a message list entry to the free list.
 */
static void vfio_user_recycle(VFIOUserProxy *proxy, VFIOUserMsg *msg)
{
    if (msg->type == VFIO_MSG_NONE) {
        error_printf("vfio_user_recycle - freeing free msg\n");
        return;
    }

    /* free msg buffer if no one is waiting to consume the reply */
    if (msg->type == VFIO_MSG_NOWAIT || msg->type == VFIO_MSG_ASYNC) {
        g_free(msg->hdr);
        if (msg->fds != NULL) {
            g_free(msg->fds);
        }
    }

    msg->type = VFIO_MSG_NONE;
    msg->hdr = NULL;
    msg->fds = NULL;
    msg->complete = false;
    msg->pending = false;
    QTAILQ_INSERT_HEAD(&proxy->free, msg, next);
}

static VFIOUserFDs *vfio_user_getfds(int numfds)
{
    VFIOUserFDs *fds = g_malloc0(sizeof(*fds) + (numfds * sizeof(int)));

    fds->fds = (int *)((char *)fds + sizeof(*fds));

    return fds;
}

/*
 * Functions only called by iothread
 */

/*
 * Process a received message.
 */
static void vfio_user_process(VFIOUserProxy *proxy, VFIOUserMsg *msg,
                              bool isreply)
{

    /*
     * Replies signal a waiter, if none just check for errors
     * and free the message buffer.
     *
     * Requests get queued for the BH.
     */
    if (isreply) {
        msg->complete = true;
        if (msg->type == VFIO_MSG_WAIT) {
            qemu_cond_signal(&msg->cv);
        } else {
            if (msg->hdr->flags & VFIO_USER_ERROR) {
                error_printf("vfio_user_process: error reply on async ");
                error_printf("request command %x error %s\n",
                             msg->hdr->command,
                             strerror(msg->hdr->error_reply));
            }
            /* youngest nowait msg has been ack'd */
            if (proxy->last_nowait == msg) {
                proxy->last_nowait = NULL;
            }
            vfio_user_recycle(proxy, msg);
        }
    } else {
        QTAILQ_INSERT_TAIL(&proxy->incoming, msg, next);
        qemu_bh_schedule(proxy->req_bh);
    }
}

/*
 * Complete a partial message read
 */
static int vfio_user_complete(VFIOUserProxy *proxy, Error **errp)
{
    VFIOUserMsg *msg = proxy->part_recv;
    size_t msgleft = proxy->recv_left;
    bool isreply;
    char *data;
    int ret;

    data = (char *)msg->hdr + (msg->hdr->size - msgleft);
    while (msgleft > 0) {
        ret = qio_channel_read(proxy->ioc, data, msgleft, errp);

        /* error or would block */
        if (ret <= 0) {
            /* try for rest on next iternation */
            if (ret == QIO_CHANNEL_ERR_BLOCK) {
                proxy->recv_left = msgleft;
            }
            return ret;
        }
        trace_vfio_user_recv_read(msg->hdr->id, ret);

        msgleft -= ret;
        data += ret;
    }

    /*
     * Read complete message, process it.
     */
    proxy->part_recv = NULL;
    proxy->recv_left = 0;
    isreply = (msg->hdr->flags & VFIO_USER_TYPE) == VFIO_USER_REPLY;
    vfio_user_process(proxy, msg, isreply);

    /* return positive value */
    return 1;
}

static void vfio_user_recv(void *opaque)
{
    VFIOUserProxy *proxy = opaque;

    QEMU_LOCK_GUARD(&proxy->lock);

    if (proxy->state == VFIO_PROXY_CONNECTED) {
        while (vfio_user_recv_one(proxy) == 0) {
            ;
        }
    }
}

/*
 * Receive and process one incoming message.
 *
 * For replies, find matching outgoing request and wake any waiters.
 * For requests, queue in incoming list and run request BH.
 */
static int vfio_user_recv_one(VFIOUserProxy *proxy)
{
    VFIOUserMsg *msg = NULL;
    g_autofree int *fdp = NULL;
    VFIOUserFDs *reqfds;
    VFIOUserHdr hdr;
    struct iovec iov = {
        .iov_base = &hdr,
        .iov_len = sizeof(hdr),
    };
    bool isreply = false;
    int i, ret;
    size_t msgleft, numfds = 0;
    char *data = NULL;
    char *buf = NULL;
    Error *local_err = NULL;

    /*
     * Complete any partial reads
     */
    if (proxy->part_recv != NULL) {
        ret = vfio_user_complete(proxy, &local_err);

        /* still not complete, try later */
        if (ret == QIO_CHANNEL_ERR_BLOCK) {
            return ret;
        }

        if (ret <= 0) {
            goto fatal;
        }
        /* else fall into reading another msg */
    }

    /*
     * Read header
     */
    ret = qio_channel_readv_full(proxy->ioc, &iov, 1, &fdp, &numfds, 0,
                                 &local_err);
    if (ret == QIO_CHANNEL_ERR_BLOCK) {
        return ret;
    }

    /* read error or other side closed connection */
    if (ret <= 0) {
        goto fatal;
    }

    if (ret < sizeof(msg)) {
        error_setg(&local_err, "short read of header");
        goto fatal;
    }

    /*
     * Validate header
     */
    if (hdr.size < sizeof(VFIOUserHdr)) {
        error_setg(&local_err, "bad header size");
        goto fatal;
    }
    switch (hdr.flags & VFIO_USER_TYPE) {
    case VFIO_USER_REQUEST:
        isreply = false;
        break;
    case VFIO_USER_REPLY:
        isreply = true;
        break;
    default:
        error_setg(&local_err, "unknown message type");
        goto fatal;
    }
    trace_vfio_user_recv_hdr(proxy->sockname, hdr.id, hdr.command, hdr.size,
                             hdr.flags);

    /*
     * For replies, find the matching pending request.
     * For requests, reap incoming FDs.
     */
    if (isreply) {
        QTAILQ_FOREACH(msg, &proxy->pending, next) {
            if (hdr.id == msg->id) {
                break;
            }
        }
        if (msg == NULL) {
            error_setg(&local_err, "unexpected reply");
            goto err;
        }
        QTAILQ_REMOVE(&proxy->pending, msg, next);

        /*
         * Process any received FDs
         */
        if (numfds != 0) {
            if (msg->fds == NULL || msg->fds->recv_fds < numfds) {
                error_setg(&local_err, "unexpected FDs");
                goto err;
            }
            msg->fds->recv_fds = numfds;
            memcpy(msg->fds->fds, fdp, numfds * sizeof(int));
        }
    } else {
        if (numfds != 0) {
            reqfds = vfio_user_getfds(numfds);
            memcpy(reqfds->fds, fdp, numfds * sizeof(int));
        } else {
            reqfds = NULL;
        }
    }

    /*
     * Put the whole message into a single buffer.
     */
    if (isreply) {
        if (hdr.size > msg->rsize) {
            error_setg(&local_err, "reply larger than recv buffer");
            goto err;
        }
        *msg->hdr = hdr;
        data = (char *)msg->hdr + sizeof(hdr);
    } else {
        if (hdr.size > proxy->max_xfer_size + sizeof(VFIOUserDMARW)) {
            error_setg(&local_err, "vfio_user_recv request larger than max");
            goto err;
        }
        buf = g_malloc0(hdr.size);
        memcpy(buf, &hdr, sizeof(hdr));
        data = buf + sizeof(hdr);
        msg = vfio_user_getmsg(proxy, (VFIOUserHdr *)buf, reqfds);
        msg->type = VFIO_MSG_REQ;
    }

    /*
     * Read rest of message.
     */
    msgleft = hdr.size - sizeof(hdr);
    while (msgleft > 0) {
        ret = qio_channel_read(proxy->ioc, data, msgleft, &local_err);

        /* prepare to complete read on next iternation */
        if (ret == QIO_CHANNEL_ERR_BLOCK) {
            proxy->part_recv = msg;
            proxy->recv_left = msgleft;
            return ret;
        }

        if (ret <= 0) {
            goto fatal;
        }
        trace_vfio_user_recv_read(hdr.id, ret);

        msgleft -= ret;
        data += ret;
    }

    vfio_user_process(proxy, msg, isreply);
    return 0;

    /*
     * fatal means the other side closed or we don't trust the stream
     * err means this message is corrupt
     */
fatal:
    vfio_user_shutdown(proxy);
    proxy->state = VFIO_PROXY_ERROR;

    /* set error if server side closed */
    if (ret == 0) {
        error_setg(&local_err, "server closed socket");
    }

err:
    for (i = 0; i < numfds; i++) {
        close(fdp[i]);
    }
    if (isreply && msg != NULL) {
        /* force an error to keep sending thread from hanging */
        vfio_user_set_error(msg->hdr, EINVAL);
        msg->complete = true;
        qemu_cond_signal(&msg->cv);
    }
    error_prepend(&local_err, "vfio_user_recv_one: ");
    error_report_err(local_err);
    return -1;
}

/*
 * Send messages from outgoing queue when the socket buffer has space.
 * If we deplete 'outgoing', remove ourselves from the poll list.
 */
static void vfio_user_send(void *opaque)
{
    VFIOUserProxy *proxy = opaque;

    QEMU_LOCK_GUARD(&proxy->lock);

    if (proxy->state == VFIO_PROXY_CONNECTED) {
        while (!QTAILQ_EMPTY(&proxy->outgoing)) {
            if (vfio_user_send_one(proxy) < 0) {
                return;
            }
        }
        qio_channel_set_aio_fd_handler(proxy->ioc, proxy->ctx,
                                       vfio_user_recv, NULL, proxy);

        /* queue empty - send any pending multi write msgs */
        if (proxy->wr_multi != NULL) {
            vfio_user_flush_multi(proxy);
        }
    }
}

/*
 * Send a single message.
 *
 * Sent async messages are freed, others are moved to pending queue.
 */
static int vfio_user_send_one(VFIOUserProxy *proxy)
{
    VFIOUserMsg *msg;
    int ret;

    msg = QTAILQ_FIRST(&proxy->outgoing);
    ret = vfio_user_send_qio(proxy, msg);
    if (ret < 0) {
        return ret;
    }

    QTAILQ_REMOVE(&proxy->outgoing, msg, next);
    proxy->num_outgoing--;
    if (msg->type == VFIO_MSG_ASYNC) {
        vfio_user_recycle(proxy, msg);
    } else {
        QTAILQ_INSERT_TAIL(&proxy->pending, msg, next);
        msg->pending = true;
    }

    return 0;
}

static void vfio_user_cb(void *opaque)
{
    VFIOUserProxy *proxy = opaque;

    QEMU_LOCK_GUARD(&proxy->lock);

    proxy->state = VFIO_PROXY_CLOSED;
    qemu_cond_signal(&proxy->close_cv);
}


/*
 * Functions called by main or CPU threads
 */

/*
 * Process incoming requests.
 *
 * The bus-specific callback has the form:
 *    request(opaque, msg)
 * where 'opaque' was specified in vfio_user_set_handler
 * and 'msg' is the inbound message.
 *
 * The callback is responsible for disposing of the message buffer,
 * usually by re-using it when calling vfio_send_reply or vfio_send_error,
 * both of which free their message buffer when the reply is sent.
 *
 * If the callback uses a new buffer, it needs to free the old one.
 */
static void vfio_user_request(void *opaque)
{
    VFIOUserProxy *proxy = opaque;
    VFIOUserMsgQ new, free;
    VFIOUserMsg *msg, *m1;

    /* reap all incoming */
    QTAILQ_INIT(&new);
    WITH_QEMU_LOCK_GUARD(&proxy->lock) {
        QTAILQ_FOREACH_SAFE(msg, &proxy->incoming, next, m1) {
            QTAILQ_REMOVE(&proxy->incoming, msg, next);
            QTAILQ_INSERT_TAIL(&new, msg, next);
        }
    }

    /* process list */
    QTAILQ_INIT(&free);
    QTAILQ_FOREACH_SAFE(msg, &new, next, m1) {
        QTAILQ_REMOVE(&new, msg, next);
        trace_vfio_user_recv_request(msg->hdr->command);
        proxy->request(proxy->req_arg, msg);
        QTAILQ_INSERT_HEAD(&free, msg, next);
    }

    /* free list */
    WITH_QEMU_LOCK_GUARD(&proxy->lock) {
        QTAILQ_FOREACH_SAFE(msg, &free, next, m1) {
            vfio_user_recycle(proxy, msg);
        }
    }
}

/*
 * Messages are queued onto the proxy's outgoing list.
 *
 * It handles 3 types of messages:
 *
 * async messages - replies and posted writes
 *
 * There will be no reply from the server, so message
 * buffers are freed after they're sent.
 *
 * nowait messages - map/unmap during address space transactions
 *
 * These are also sent async, but a reply is expected so that
 * vfio_wait_reqs() can wait for the youngest nowait request.
 * They transition from the outgoing list to the pending list
 * when sent, and are freed when the reply is received.
 *
 * wait messages - all other requests
 *
 * The reply to these messages is waited for by their caller.
 * They also transition from outgoing to pending when sent, but
 * the message buffer is returned to the caller with the reply
 * contents.  The caller is responsible for freeing these messages.
 *
 * As an optimization, if the outgoing list and the socket send
 * buffer are empty, the message is sent inline instead of being
 * added to the outgoing list.  The rest of the transitions are
 * unchanged.
 *
 * returns 0 if the message was sent or queued
 * returns -1 on send error
 */
static int vfio_user_send_queued(VFIOUserProxy *proxy, VFIOUserMsg *msg)
{
    int ret;

    /* older coalesced writes go first */
    if (proxy->wr_multi != NULL &&
        ((msg->hdr->flags & VFIO_USER_TYPE) == VFIO_USER_REQUEST)) {
        vfio_user_flush_multi(proxy);
    }

    /*
     * Unsent outgoing msgs - add to tail
     */
    if (!QTAILQ_EMPTY(&proxy->outgoing)) {
        QTAILQ_INSERT_TAIL(&proxy->outgoing, msg, next);
        proxy->num_outgoing++;
        return 0;
    }

    /*
     * Try inline - if blocked, queue it and kick send poller
     */
    if (proxy->flags & VFIO_PROXY_FORCE_QUEUED) {
        ret = QIO_CHANNEL_ERR_BLOCK;
    } else {
        ret = vfio_user_send_qio(proxy, msg);
    }
    if (ret == QIO_CHANNEL_ERR_BLOCK) {
        QTAILQ_INSERT_HEAD(&proxy->outgoing, msg, next);
        proxy->num_outgoing = 1;
        qio_channel_set_aio_fd_handler(proxy->ioc, proxy->ctx,
                                       vfio_user_recv, vfio_user_send,
                                       proxy);
        return 0;
    }
    if (ret == -1) {
        return ret;
    }

    /*
     * Sent - free async, add others to pending
     */
    if (msg->type == VFIO_MSG_ASYNC) {
        vfio_user_recycle(proxy, msg);
    } else {
        QTAILQ_INSERT_TAIL(&proxy->pending, msg, next);
        msg->pending = true;
    }

    return 0;
}

/*
 * async send - msg can be queued, but will be freed when sent
 */
static void vfio_user_send_async(VFIOUserProxy *proxy, VFIOUserHdr *hdr,
                                 VFIOUserFDs *fds)
{
    VFIOUserMsg *msg;
    int ret;

    if (!(hdr->flags & (VFIO_USER_NO_REPLY | VFIO_USER_REPLY))) {
        error_printf("vfio_user_send_async on sync message\n");
        return;
    }

    QEMU_LOCK_GUARD(&proxy->lock);

    msg = vfio_user_getmsg(proxy, hdr, fds);
    msg->id = hdr->id;
    msg->rsize = 0;
    msg->type = VFIO_MSG_ASYNC;

    ret = vfio_user_send_queued(proxy, msg);
    if (ret < 0) {
        vfio_user_recycle(proxy, msg);
    }
}

/*
 * nowait send - vfio_wait_reqs() can wait for it later
 */
static void vfio_user_send_nowait(VFIOUserProxy *proxy, VFIOUserHdr *hdr,
                                  VFIOUserFDs *fds, int rsize)
{
    VFIOUserMsg *msg;
    int ret;

    if (hdr->flags & VFIO_USER_NO_REPLY) {
        error_printf("vfio_user_send_nowait on async message\n");
        return;
    }

    QEMU_LOCK_GUARD(&proxy->lock);

    msg = vfio_user_getmsg(proxy, hdr, fds);
    msg->id = hdr->id;
    msg->rsize = rsize ? rsize : hdr->size;
    msg->type = VFIO_MSG_NOWAIT;

    ret = vfio_user_send_queued(proxy, msg);
    if (ret < 0) {
        vfio_user_recycle(proxy, msg);
        return;
    }

    proxy->last_nowait = msg;
}

static void vfio_user_send_wait(VFIOUserProxy *proxy, VFIOUserHdr *hdr,
                                VFIOUserFDs *fds, int rsize, bool nobql)
{
    VFIOUserMsg *msg;
    bool iolock = false;
    int ret;

    if (hdr->flags & VFIO_USER_NO_REPLY) {
        error_printf("vfio_user_send_wait on async message\n");
        vfio_user_set_error(hdr, EINVAL);
        return;
    }

    /*
     * We may block later, so use a per-proxy lock and drop
     * BQL while we sleep unless 'nobql' says not to.
     */
    qemu_mutex_lock(&proxy->lock);
    if (!nobql) {
        iolock = qemu_mutex_iothread_locked();
        if (iolock) {
            qemu_mutex_unlock_iothread();
        }
    }

    msg = vfio_user_getmsg(proxy, hdr, fds);
    msg->id = hdr->id;
    msg->rsize = rsize ? rsize : hdr->size;
    msg->type = VFIO_MSG_WAIT;

    ret = vfio_user_send_queued(proxy, msg);

    if (ret == 0) {
        while (!msg->complete) {
            if (!qemu_cond_timedwait(&msg->cv, &proxy->lock,
                                     proxy->wait_time)) {
                VFIOUserMsgQ *list;

                list = msg->pending ? &proxy->pending : &proxy->outgoing;
                QTAILQ_REMOVE(list, msg, next);
                vfio_user_set_error(hdr, ETIMEDOUT);
                break;
            }
        }
    }
    vfio_user_recycle(proxy, msg);

    /* lock order is BQL->proxy - don't hold proxy when getting BQL */
    qemu_mutex_unlock(&proxy->lock);
    if (iolock) {
        qemu_mutex_lock_iothread();
    }
}

static void vfio_user_wait_reqs(VFIOUserProxy *proxy)
{
    VFIOUserMsg *msg;
    bool iolock = false;

    /*
     * Any DMA map/unmap requests sent in the middle
     * of a memory region transaction were sent nowait.
     * Wait for them here.
     */
    qemu_mutex_lock(&proxy->lock);
    if (proxy->last_nowait != NULL) {
        iolock = qemu_mutex_iothread_locked();
        if (iolock) {
            qemu_mutex_unlock_iothread();
        }

        /*
         * Change type to WAIT to wait for reply
         */
        msg = proxy->last_nowait;
        msg->type = VFIO_MSG_WAIT;
        proxy->last_nowait = NULL;
        while (!msg->complete) {
            if (!qemu_cond_timedwait(&msg->cv, &proxy->lock,
                                     proxy->wait_time)) {
                VFIOUserMsgQ *list;

                list = msg->pending ? &proxy->pending : &proxy->outgoing;
                QTAILQ_REMOVE(list, msg, next);
                error_printf("vfio_wait_reqs - timed out\n");
                break;
            }
        }

        if (msg->hdr->flags & VFIO_USER_ERROR) {
            error_printf("vfio_user_wait_reqs - error reply on async ");
            error_printf("request: command %x error %s\n", msg->hdr->command,
                         strerror(msg->hdr->error_reply));
        }

        /*
         * Change type back to NOWAIT to free
         */
        msg->type = VFIO_MSG_NOWAIT;
        vfio_user_recycle(proxy, msg);
    }

    /* lock order is BQL->proxy - don't hold proxy when getting BQL */
    qemu_mutex_unlock(&proxy->lock);
    if (iolock) {
        qemu_mutex_lock_iothread();
    }
}

/*
 * Reply to an incoming request.
 */
void vfio_user_send_reply(VFIOUserProxy *proxy, VFIOUserHdr *hdr, int size)
{

    if (size < sizeof(VFIOUserHdr)) {
        error_printf("vfio_user_send_reply - size too small\n");
        g_free(hdr);
        return;
    }

    /*
     * convert header to associated reply
     */
    hdr->flags = VFIO_USER_REPLY;
    hdr->size = size;

    vfio_user_send_async(proxy, hdr, NULL);
}

/*
 * Send an error reply to an incoming request.
 */
void vfio_user_send_error(VFIOUserProxy *proxy, VFIOUserHdr *hdr, int error)
{

    /*
     * convert header to associated reply
     */
    hdr->flags = VFIO_USER_REPLY;
    hdr->flags |= VFIO_USER_ERROR;
    hdr->error_reply = error;
    hdr->size = sizeof(*hdr);

    vfio_user_send_async(proxy, hdr, NULL);
}

/*
 * Close FDs erroneously received in an incoming request.
 */
void vfio_user_putfds(VFIOUserMsg *msg)
{
    VFIOUserFDs *fds = msg->fds;
    int i;

    for (i = 0; i < fds->recv_fds; i++) {
        close(fds->fds[i]);
    }
    g_free(fds);
    msg->fds = NULL;
}

static QLIST_HEAD(, VFIOUserProxy) vfio_user_sockets =
    QLIST_HEAD_INITIALIZER(vfio_user_sockets);

VFIOUserProxy *vfio_user_connect_dev(SocketAddress *addr, Error **errp)
{
    VFIOUserProxy *proxy;
    QIOChannelSocket *sioc;
    QIOChannel *ioc;
    char *sockname;

    if (addr->type != SOCKET_ADDRESS_TYPE_UNIX) {
        error_setg(errp, "vfio_user_connect - bad address family");
        return NULL;
    }
    sockname = addr->u.q_unix.path;

    sioc = qio_channel_socket_new();
    ioc = QIO_CHANNEL(sioc);
    if (qio_channel_socket_connect_sync(sioc, addr, errp)) {
        object_unref(OBJECT(ioc));
        return NULL;
    }
    qio_channel_set_blocking(ioc, false, NULL);

    proxy = g_malloc0(sizeof(VFIOUserProxy));
    proxy->sockname = g_strdup_printf("unix:%s", sockname);
    proxy->ioc = ioc;

    /* init defaults */
    proxy->max_xfer_size = VFIO_USER_DEF_MAX_XFER;
    proxy->max_send_fds = VFIO_USER_DEF_MAX_FDS;
    proxy->max_dma = VFIO_USER_DEF_MAP_MAX;
    proxy->dma_pgsizes = VFIO_USER_DEF_PGSIZE;
    proxy->max_bitmap = VFIO_USER_DEF_MAX_BITMAP;
    proxy->migr_pgsize = VFIO_USER_DEF_PGSIZE;

    proxy->flags = VFIO_PROXY_CLIENT;
    proxy->state = VFIO_PROXY_CONNECTED;

    qemu_mutex_init(&proxy->lock);
    qemu_cond_init(&proxy->close_cv);

    if (vfio_user_iothread == NULL) {
        vfio_user_iothread = iothread_create("VFIO user", errp);
    }

    proxy->ctx = iothread_get_aio_context(vfio_user_iothread);
    proxy->req_bh = qemu_bh_new(vfio_user_request, proxy);

    QTAILQ_INIT(&proxy->outgoing);
    QTAILQ_INIT(&proxy->incoming);
    QTAILQ_INIT(&proxy->free);
    QTAILQ_INIT(&proxy->pending);
    QLIST_INSERT_HEAD(&vfio_user_sockets, proxy, next);

    return proxy;
}

void vfio_user_set_handler(VFIODevice *vbasedev,
                           void (*handler)(void *opaque, VFIOUserMsg *msg),
                           void *req_arg)
{
    VFIOUserProxy *proxy = vbasedev->proxy;

    proxy->request = handler;
    proxy->req_arg = req_arg;
    qio_channel_set_aio_fd_handler(proxy->ioc, proxy->ctx,
                                   vfio_user_recv, NULL, proxy);
}

void vfio_user_disconnect(VFIOUserProxy *proxy)
{
    VFIOUserMsg *r1, *r2;

    qemu_mutex_lock(&proxy->lock);

    /* our side is quitting */
    if (proxy->state == VFIO_PROXY_CONNECTED) {
        vfio_user_shutdown(proxy);
        if (!QTAILQ_EMPTY(&proxy->pending)) {
            error_printf("vfio_user_disconnect: outstanding requests\n");
        }
    }
    object_unref(OBJECT(proxy->ioc));
    proxy->ioc = NULL;
    qemu_bh_delete(proxy->req_bh);
    proxy->req_bh = NULL;

    proxy->state = VFIO_PROXY_CLOSING;
    QTAILQ_FOREACH_SAFE(r1, &proxy->outgoing, next, r2) {
        qemu_cond_destroy(&r1->cv);
        QTAILQ_REMOVE(&proxy->pending, r1, next);
        g_free(r1);
    }
    QTAILQ_FOREACH_SAFE(r1, &proxy->incoming, next, r2) {
        qemu_cond_destroy(&r1->cv);
        QTAILQ_REMOVE(&proxy->incoming, r1, next);
        g_free(r1);
    }
    QTAILQ_FOREACH_SAFE(r1, &proxy->pending, next, r2) {
        qemu_cond_destroy(&r1->cv);
        QTAILQ_REMOVE(&proxy->pending, r1, next);
        g_free(r1);
    }
    QTAILQ_FOREACH_SAFE(r1, &proxy->free, next, r2) {
        qemu_cond_destroy(&r1->cv);
        QTAILQ_REMOVE(&proxy->free, r1, next);
        g_free(r1);
    }

    /*
     * Make sure the iothread isn't blocking anywhere
     * with a ref to this proxy by waiting for a BH
     * handler to run after the proxy fd handlers were
     * deleted above.
     */
    aio_bh_schedule_oneshot(proxy->ctx, vfio_user_cb, proxy);
    qemu_cond_wait(&proxy->close_cv, &proxy->lock);

    /* we now hold the only ref to proxy */
    qemu_mutex_unlock(&proxy->lock);
    qemu_cond_destroy(&proxy->close_cv);
    qemu_mutex_destroy(&proxy->lock);

    QLIST_REMOVE(proxy, next);
    if (QLIST_EMPTY(&vfio_user_sockets)) {
        iothread_destroy(vfio_user_iothread);
        vfio_user_iothread = NULL;
    }

    g_free(proxy->sockname);
    g_free(proxy);
}

static int vfio_connect_proxy(VFIOUserProxy *proxy, VFIOGroup *group,
                              AddressSpace *as, Error **errp)
{
    VFIOAddressSpace *space;
    VFIOContainer *container;
    int ret;

    /*
     * try to mirror vfio_connect_container()
     * as much as possible
     */

    space = vfio_get_address_space(as);

    container = vfio_new_container(space);
    container->fd = -1;
    container->io = &vfio_cont_io_sock;
    container->proxy = proxy;

    /*
     * The proxy uses a SW IOMMU in lieu of the HW one
     * used in the ioctl() version.  Mascarade as TYPE1
     * for maximum compatibility
     */
    container->iommu_type = VFIO_TYPE1_IOMMU;

    /*
     * VFIO user allows the device server to map guest
     * memory so it has the same issue with discards as
     * a local IOMMU has.
     */
    ret = vfio_ram_block_discard_disable(container, true);
    if (ret) {
        error_setg_errno(errp, -ret, "Cannot set discarding of RAM broken");
        goto free_container_exit;
    }

    vfio_host_win_add(container, 0, (hwaddr)-1, proxy->dma_pgsizes);
    container->pgsizes = proxy->dma_pgsizes;
    container->dma_max_mappings = proxy->max_dma;

    /* setup bitmask now, but migration support won't be ready until v2 */
    container->dirty_pages_supported = true;
    container->max_dirty_bitmap_size = proxy->max_bitmap;
    container->dirty_pgsizes = proxy->migr_pgsize;

    vfio_link_container(container, group);

    if (container->error) {
        ret = -1;
        error_propagate_prepend(errp, container->error,
            "memory listener initialization failed: ");
        goto listener_release_exit;
    }

    container->initialized = true;

    return 0;

listener_release_exit:
    QLIST_REMOVE(group, container_next);
    QLIST_REMOVE(container, next);
    vfio_listener_release(container);
    vfio_ram_block_discard_disable(container, false);

free_container_exit:
    g_free(container);

    vfio_put_address_space(space);

    return ret;
}

static void vfio_disconnect_proxy(VFIOGroup *group)
{
    VFIOContainer *container = group->container;
    VFIOAddressSpace *space = container->space;

    /*
     * try to mirror vfio_disconnect_container()
     * as much as possible, knowing each device
     * is in one group and one container
     */

    QLIST_REMOVE(group, container_next);
    group->container = NULL;

    memory_listener_unregister(&container->listener);

    vfio_unmap_container(container);

    g_free(container);
    vfio_put_address_space(space);
}

int vfio_user_get_device(VFIOGroup *group, VFIODevice *vbasedev, Error **errp)
{
    struct vfio_device_info info = { .argsz = sizeof(info) };
    int ret;

    ret = vfio_user_get_info(vbasedev->proxy, &info);
    if (ret) {
        error_setg_errno(errp, -ret, "get info failure");
        return ret;
    }

    /* defend against a malicious server */
    if (info.num_regions > VFIO_USER_MAX_REGIONS ||
        info.num_irqs > VFIO_USER_MAX_IRQS) {
        error_printf("vfio_user_get_info: invalid reply\n");
        return -EINVAL;
    }

    vbasedev->fd = -1;
    vfio_init_device(vbasedev, group, &info);

    return 0;
}

VFIOGroup *vfio_user_get_group(VFIOUserProxy *proxy, AddressSpace *as,
                               Error **errp)
{
    VFIOGroup *group;

    /*
     * Mirror vfio_get_group(), except that each
     * device gets its own group and container,
     * unrelated to any host IOMMU groupings
     */
    group = g_malloc0(sizeof(*group));
    group->fd = -1;
    group->groupid = -1;
    QLIST_INIT(&group->device_list);

    if (vfio_connect_proxy(proxy, group, as, errp)) {
        error_prepend(errp, "failed to connect proxy");
        g_free(group);
        group = NULL;
    }

    if (QLIST_EMPTY(&vfio_group_list)) {
        qemu_register_reset(vfio_reset_handler, NULL);
    }

    QLIST_INSERT_HEAD(&vfio_group_list, group, next);

    return group;
}

void vfio_user_put_group(VFIOGroup *group)
{
    if (!group || !QLIST_EMPTY(&group->device_list)) {
        return;
    }

    vfio_ram_block_discard_disable(group->container, false);
    vfio_disconnect_proxy(group);
    QLIST_REMOVE(group, next);
    g_free(group);

    if (QLIST_EMPTY(&vfio_group_list)) {
        qemu_unregister_reset(vfio_reset_handler, NULL);
    }
}

static void vfio_user_request_msg(VFIOUserHdr *hdr, uint16_t cmd,
                                  uint32_t size, uint32_t flags)
{
    static uint16_t next_id;

    hdr->id = qatomic_fetch_inc(&next_id);
    hdr->command = cmd;
    hdr->size = size;
    hdr->flags = (flags & ~VFIO_USER_TYPE) | VFIO_USER_REQUEST;
    hdr->error_reply = 0;
}

struct cap_entry {
    const char *name;
    int (*check)(VFIOUserProxy *proxy, QObject *qobj, Error **errp);
};

static int caps_parse(VFIOUserProxy *proxy, QDict *qdict,
                      struct cap_entry caps[], Error **errp)
{
    QObject *qobj;
    struct cap_entry *p;

    for (p = caps; p->name != NULL; p++) {
        qobj = qdict_get(qdict, p->name);
        if (qobj != NULL) {
            if (p->check(proxy, qobj, errp)) {
                return -1;
            }
            qdict_del(qdict, p->name);
        }
    }

    /* warning, for now */
    if (qdict_size(qdict) != 0) {
        warn_report("spurious capabilities");
    }
    return 0;
}

static int check_migr_pgsize(VFIOUserProxy *proxy, QObject *qobj, Error **errp)
{
    QNum *qn = qobject_to(QNum, qobj);
    uint64_t pgsize;

    if (qn == NULL || !qnum_get_try_uint(qn, &pgsize)) {
        error_setg(errp, "malformed %s", VFIO_USER_CAP_PGSIZE);
        return -1;
    }

    /* must be larger than default */
    if (pgsize & (VFIO_USER_DEF_PGSIZE - 1)) {
        error_setg(errp, "pgsize 0x%"PRIx64" too small", pgsize);
        return -1;
    }

    proxy->migr_pgsize = pgsize;
    return 0;
}

static int check_bitmap(VFIOUserProxy *proxy, QObject *qobj, Error **errp)
{
    QNum *qn = qobject_to(QNum, qobj);
    uint64_t bitmap_size;

    if (qn == NULL || !qnum_get_try_uint(qn, &bitmap_size)) {
        error_setg(errp, "malformed %s", VFIO_USER_CAP_MAX_BITMAP);
        return -1;
    }

    /* can only lower it */
    if (bitmap_size > VFIO_USER_DEF_MAX_BITMAP) {
        error_setg(errp, "%s too large", VFIO_USER_CAP_MAX_BITMAP);
        return -1;
    }

    proxy->max_bitmap = bitmap_size;
    return 0;
}

static struct cap_entry caps_migr[] = {
    { VFIO_USER_CAP_PGSIZE, check_migr_pgsize },
    { VFIO_USER_CAP_MAX_BITMAP, check_bitmap },
    { NULL }
};

static int check_max_fds(VFIOUserProxy *proxy, QObject *qobj, Error **errp)
{
    QNum *qn = qobject_to(QNum, qobj);
    uint64_t max_send_fds;

    if (qn == NULL || !qnum_get_try_uint(qn, &max_send_fds) ||
        max_send_fds > VFIO_USER_MAX_MAX_FDS) {
        error_setg(errp, "malformed %s", VFIO_USER_CAP_MAX_FDS);
        return -1;
    }
    proxy->max_send_fds = max_send_fds;
    return 0;
}

static int check_max_xfer(VFIOUserProxy *proxy, QObject *qobj, Error **errp)
{
    QNum *qn = qobject_to(QNum, qobj);
    uint64_t max_xfer_size;

    if (qn == NULL || !qnum_get_try_uint(qn, &max_xfer_size) ||
        max_xfer_size > VFIO_USER_MAX_MAX_XFER) {
        error_setg(errp, "malformed %s", VFIO_USER_CAP_MAX_XFER);
        return -1;
    }
    proxy->max_xfer_size = max_xfer_size;
    return 0;
}

static int check_pgsizes(VFIOUserProxy *proxy, QObject *qobj, Error **errp)
{
    QNum *qn = qobject_to(QNum, qobj);
    uint64_t pgsizes;

    if (qn == NULL || !qnum_get_try_uint(qn, &pgsizes)) {
        error_setg(errp, "malformed %s", VFIO_USER_CAP_PGSIZES);
        return -1;
    }

    /* must be larger than default */
    if (pgsizes & (VFIO_USER_DEF_PGSIZE - 1)) {
        error_setg(errp, "pgsize 0x%"PRIx64" too small", pgsizes);
        return -1;
    }

    proxy->dma_pgsizes = pgsizes;
    return 0;
}

static int check_max_dma(VFIOUserProxy *proxy, QObject *qobj, Error **errp)
{
    QNum *qn = qobject_to(QNum, qobj);
    uint64_t max_dma;

    if (qn == NULL || !qnum_get_try_uint(qn, &max_dma)) {
        error_setg(errp, "malformed %s", VFIO_USER_CAP_MAP_MAX);
        return -1;
    }

    /* can only lower it */
    if (max_dma > VFIO_USER_DEF_MAP_MAX) {
        error_setg(errp, "%s too large", VFIO_USER_CAP_MAP_MAX);
        return -1;
    }

    proxy->max_dma = max_dma;
    return 0;
}

static int check_migr(VFIOUserProxy *proxy, QObject *qobj, Error **errp)
{
    QDict *qdict = qobject_to(QDict, qobj);

    if (qdict == NULL) {
        error_setg(errp, "malformed %s", VFIO_USER_CAP_MAX_FDS);
        return -1;
    }
    return caps_parse(proxy, qdict, caps_migr, errp);
}

static int check_multi(VFIOUserProxy *proxy, QObject *qobj, Error **errp)
{
    QBool *qb = qobject_to(QBool, qobj);

    if (qb == NULL) {
        error_setg(errp, "malformed %s", VFIO_USER_CAP_MULTI);
        return -1;
    }
    if (qbool_get_bool(qb)) {
        proxy->flags |= VFIO_PROXY_USE_MULTI;
    }
    return 0;
}

static struct cap_entry caps_cap[] = {
    { VFIO_USER_CAP_MAX_FDS, check_max_fds },
    { VFIO_USER_CAP_MAX_XFER, check_max_xfer },
    { VFIO_USER_CAP_PGSIZES, check_pgsizes },
    { VFIO_USER_CAP_MAP_MAX, check_max_dma },
    { VFIO_USER_CAP_MIGR, check_migr },
    { VFIO_USER_CAP_MULTI, check_multi },
    { NULL }
};

static int check_cap(VFIOUserProxy *proxy, QObject *qobj, Error **errp)
{
   QDict *qdict = qobject_to(QDict, qobj);

    if (qdict == NULL) {
        error_setg(errp, "malformed %s", VFIO_USER_CAP);
        return -1;
    }
    return caps_parse(proxy, qdict, caps_cap, errp);
}

static struct cap_entry ver_0_0[] = {
    { VFIO_USER_CAP, check_cap },
    { NULL }
};

static int caps_check(VFIOUserProxy *proxy, int minor, const char *caps,
                      Error **errp)
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
    ret = caps_parse(proxy, qdict, ver_0_0, errp);

    qobject_unref(qobj);
    return ret;
}

static GString *caps_json(void)
{
    QDict *dict = qdict_new();
    QDict *capdict = qdict_new();
    QDict *migdict = qdict_new();
    GString *str;

    qdict_put_int(migdict, VFIO_USER_CAP_PGSIZE, VFIO_USER_DEF_PGSIZE);
    qdict_put_int(migdict, VFIO_USER_CAP_MAX_BITMAP, VFIO_USER_DEF_MAX_BITMAP);
    qdict_put_obj(capdict, VFIO_USER_CAP_MIGR, QOBJECT(migdict));

    qdict_put_int(capdict, VFIO_USER_CAP_MAX_FDS, VFIO_USER_MAX_MAX_FDS);
    qdict_put_int(capdict, VFIO_USER_CAP_MAX_XFER, VFIO_USER_DEF_MAX_XFER);
    qdict_put_int(capdict, VFIO_USER_CAP_PGSIZES, VFIO_USER_DEF_PGSIZE);
    qdict_put_int(capdict, VFIO_USER_CAP_MAP_MAX, VFIO_USER_DEF_MAP_MAX);
    qdict_put_bool(capdict, VFIO_USER_CAP_MULTI, true);

    qdict_put_obj(dict, VFIO_USER_CAP, QOBJECT(capdict));

    str = qobject_to_json(QOBJECT(dict));
    qobject_unref(dict);
    return str;
}

int vfio_user_validate_version(VFIOUserProxy *proxy, Error **errp)
{
    g_autofree VFIOUserVersion *msgp;
    GString *caps;
    char *reply;
    int size, caplen;

    caps = caps_json();
    caplen = caps->len + 1;
    size = sizeof(*msgp) + caplen;
    msgp = g_malloc0(size);

    vfio_user_request_msg(&msgp->hdr, VFIO_USER_VERSION, size, 0);
    msgp->major = VFIO_USER_MAJOR_VER;
    msgp->minor = VFIO_USER_MINOR_VER;
    memcpy(&msgp->capabilities, caps->str, caplen);
    g_string_free(caps, true);
    trace_vfio_user_version(msgp->major, msgp->minor, msgp->capabilities);

    vfio_user_send_wait(proxy, &msgp->hdr, NULL, 0, false);
    if (msgp->hdr.flags & VFIO_USER_ERROR) {
        error_setg_errno(errp, msgp->hdr.error_reply, "version reply");
        return -1;
    }

    if (msgp->major != VFIO_USER_MAJOR_VER ||
        msgp->minor > VFIO_USER_MINOR_VER) {
        error_setg(errp, "incompatible server version");
        return -1;
    }

    reply = msgp->capabilities;
    if (reply[msgp->hdr.size - sizeof(*msgp) - 1] != '\0') {
        error_setg(errp, "corrupt version reply");
        return -1;
    }

    if (caps_check(proxy, msgp->minor, reply, errp) != 0) {
        return -1;
    }

    trace_vfio_user_version(msgp->major, msgp->minor, msgp->capabilities);
    return 0;
}

static int vfio_user_dma_map(VFIOUserProxy *proxy,
                             struct vfio_iommu_type1_dma_map *map,
                             int fd, bool will_commit)
{
    VFIOUserFDs *fds = NULL;
    VFIOUserDMAMap *msgp = g_malloc0(sizeof(*msgp));
    int ret;

    vfio_user_request_msg(&msgp->hdr, VFIO_USER_DMA_MAP, sizeof(*msgp), 0);
    msgp->argsz = map->argsz;
    msgp->flags = map->flags;
    msgp->offset = map->vaddr;
    msgp->iova = map->iova;
    msgp->size = map->size;
    trace_vfio_user_dma_map(msgp->iova, msgp->size, msgp->offset, msgp->flags,
                        will_commit);

    /*
     * The will_commit case sends without blocking or dropping BQL.
     * They're later waited for in vfio_send_wait_reqs.
     */
    if (will_commit) {
        /* can't use auto variable since we don't block */
        if (fd != -1) {
            fds = vfio_user_getfds(1);
            fds->send_fds = 1;
            fds->fds[0] = fd;
        }
        vfio_user_send_nowait(proxy, &msgp->hdr, fds, 0);
        ret = 0;
    } else {
        VFIOUserFDs local_fds = { 1, 0, &fd };

        fds = fd != -1 ? &local_fds : NULL;
        vfio_user_send_wait(proxy, &msgp->hdr, fds, 0, will_commit);
        ret = (msgp->hdr.flags & VFIO_USER_ERROR) ? -msgp->hdr.error_reply : 0;
        g_free(msgp);
    }

    return ret;
}

static int vfio_user_dma_unmap(VFIOUserProxy *proxy,
                               struct vfio_iommu_type1_dma_unmap *unmap,
                               struct vfio_bitmap *bitmap, bool will_commit)
{
    struct {
        VFIOUserDMAUnmap msg;
        VFIOUserBitmap bitmap;
    } *msgp = NULL;
    int msize, rsize;
    bool blocking = !will_commit;

    if (bitmap == NULL &&
        (unmap->flags & VFIO_DMA_UNMAP_FLAG_GET_DIRTY_BITMAP)) {
        error_printf("vfio_user_dma_unmap mismatched flags and bitmap\n");
        return -EINVAL;
    }

    /*
     * If a dirty bitmap is returned, allocate extra space for it
     * and block for reply even in the will_commit case.
     * Otherwise, can send the unmap request without waiting.
     */
    if (bitmap != NULL) {
        blocking = true;
        msize = sizeof(*msgp);
        rsize = msize + bitmap->size;
        msgp = g_malloc0(rsize);
        msgp->bitmap.pgsize = bitmap->pgsize;
        msgp->bitmap.size = bitmap->size;
    } else {
        msize = rsize = sizeof(VFIOUserDMAUnmap);
        msgp = g_malloc0(rsize);
    }

    vfio_user_request_msg(&msgp->msg.hdr, VFIO_USER_DMA_UNMAP, msize, 0);
    msgp->msg.argsz = rsize - sizeof(VFIOUserHdr);
    msgp->msg.argsz = unmap->argsz;
    msgp->msg.flags = unmap->flags;
    msgp->msg.iova = unmap->iova;
    msgp->msg.size = unmap->size;
    trace_vfio_user_dma_unmap(msgp->msg.iova, msgp->msg.size, msgp->msg.flags,
                         bitmap != NULL, will_commit);

    if (blocking) {
        vfio_user_send_wait(proxy, &msgp->msg.hdr, NULL, rsize, will_commit);
        if (msgp->msg.hdr.flags & VFIO_USER_ERROR) {
            return -msgp->msg.hdr.error_reply;
        }
        if (bitmap != NULL) {
            memcpy(bitmap->data, &msgp->bitmap.data, bitmap->size);
        }
        g_free(msgp);
    } else {
        vfio_user_send_nowait(proxy, &msgp->msg.hdr, NULL, rsize);
    }

    return 0;
}

static int vfio_user_get_info(VFIOUserProxy *proxy,
                              struct vfio_device_info *info)
{
    VFIOUserDeviceInfo msg;
    uint32_t argsz = sizeof(msg) - sizeof(msg.hdr);

    memset(&msg, 0, sizeof(msg));
    vfio_user_request_msg(&msg.hdr, VFIO_USER_DEVICE_GET_INFO, sizeof(msg), 0);
    msg.argsz = argsz;

    vfio_user_send_wait(proxy, &msg.hdr, NULL, 0, false);
    if (msg.hdr.flags & VFIO_USER_ERROR) {
        return -msg.hdr.error_reply;
    }
    trace_vfio_user_get_info(msg.num_regions, msg.num_irqs);

    memcpy(info, &msg.argsz, argsz);
    return 0;
}

static int vfio_user_get_region_info(VFIOUserProxy *proxy,
                                     struct vfio_region_info *info,
                                     VFIOUserFDs *fds)
{
    g_autofree VFIOUserRegionInfo *msgp = NULL;
    uint32_t size;

    /* data returned can be larger than vfio_region_info */
    if (info->argsz < sizeof(*info)) {
        error_printf("vfio_user_get_region_info argsz too small\n");
        return -E2BIG;
    }
    if (fds != NULL && fds->send_fds != 0) {
        error_printf("vfio_user_get_region_info can't send FDs\n");
        return -EINVAL;
    }

    size = info->argsz + sizeof(VFIOUserHdr);
    msgp = g_malloc0(size);

    vfio_user_request_msg(&msgp->hdr, VFIO_USER_DEVICE_GET_REGION_INFO,
                          sizeof(*msgp), 0);
    msgp->argsz = info->argsz;
    msgp->index = info->index;

    vfio_user_send_wait(proxy, &msgp->hdr, fds, size, false);
    if (msgp->hdr.flags & VFIO_USER_ERROR) {
        return -msgp->hdr.error_reply;
    }
    trace_vfio_user_get_region_info(msgp->index, msgp->flags, msgp->size);

    memcpy(info, &msgp->argsz, info->argsz);

    /* read-after-write hazard if guest can directly access region */
    if (info->flags & VFIO_REGION_INFO_FLAG_MMAP) {
        WITH_QEMU_LOCK_GUARD(&proxy->lock) {
            proxy->flags |= VFIO_PROXY_NO_POST;
        }
    }

    return 0;
}

static int vfio_user_get_irq_info(VFIOUserProxy *proxy,
                                  struct vfio_irq_info *info)
{
    VFIOUserIRQInfo msg;

    memset(&msg, 0, sizeof(msg));
    vfio_user_request_msg(&msg.hdr, VFIO_USER_DEVICE_GET_IRQ_INFO,
                          sizeof(msg), 0);
    msg.argsz = info->argsz;
    msg.index = info->index;

    vfio_user_send_wait(proxy, &msg.hdr, NULL, 0, false);
    if (msg.hdr.flags & VFIO_USER_ERROR) {
        return -msg.hdr.error_reply;
    }
    trace_vfio_user_get_irq_info(msg.index, msg.flags, msg.count);

    memcpy(info, &msg.argsz, sizeof(*info));
    return 0;
}

static int irq_howmany(int *fdp, uint32_t cur, uint32_t max)
{
    int n = 0;

    if (fdp[cur] != -1) {
        do {
            n++;
        } while (n < max && fdp[cur + n] != -1);
    } else {
        do {
            n++;
        } while (n < max && fdp[cur + n] == -1);
    }

    return n;
}

static int vfio_user_set_irqs(VFIOUserProxy *proxy, struct vfio_irq_set *irq)
{
    g_autofree VFIOUserIRQSet *msgp = NULL;
    uint32_t size, nfds, send_fds, sent_fds, max;

    if (irq->argsz < sizeof(*irq)) {
        error_printf("vfio_user_set_irqs argsz too small\n");
        return -EINVAL;
    }

    /*
     * Handle simple case
     */
    if ((irq->flags & VFIO_IRQ_SET_DATA_EVENTFD) == 0) {
        size = sizeof(VFIOUserHdr) + irq->argsz;
        msgp = g_malloc0(size);

        vfio_user_request_msg(&msgp->hdr, VFIO_USER_DEVICE_SET_IRQS, size, 0);
        msgp->argsz = irq->argsz;
        msgp->flags = irq->flags;
        msgp->index = irq->index;
        msgp->start = irq->start;
        msgp->count = irq->count;
        trace_vfio_user_set_irqs(msgp->index, msgp->start, msgp->count,
                                 msgp->flags);

        vfio_user_send_wait(proxy, &msgp->hdr, NULL, 0, false);
        if (msgp->hdr.flags & VFIO_USER_ERROR) {
            return -msgp->hdr.error_reply;
        }

        return 0;
    }

    /*
     * Calculate the number of FDs to send
     * and adjust argsz
     */
    nfds = (irq->argsz - sizeof(*irq)) / sizeof(int);
    irq->argsz = sizeof(*irq);
    msgp = g_malloc0(sizeof(*msgp));
    /*
     * Send in chunks if over max_send_fds
     */
    for (sent_fds = 0; nfds > sent_fds; sent_fds += send_fds) {
        VFIOUserFDs *arg_fds, loop_fds;

        /* must send all valid FDs or all invalid FDs in single msg */
        max = nfds - sent_fds;
        if (max > proxy->max_send_fds) {
            max = proxy->max_send_fds;
        }
        send_fds = irq_howmany((int *)irq->data, sent_fds, max);

        vfio_user_request_msg(&msgp->hdr, VFIO_USER_DEVICE_SET_IRQS,
                              sizeof(*msgp), 0);
        msgp->argsz = irq->argsz;
        msgp->flags = irq->flags;
        msgp->index = irq->index;
        msgp->start = irq->start + sent_fds;
        msgp->count = send_fds;
        trace_vfio_user_set_irqs(msgp->index, msgp->start, msgp->count,
                                 msgp->flags);

        loop_fds.send_fds = send_fds;
        loop_fds.recv_fds = 0;
        loop_fds.fds = (int *)irq->data + sent_fds;
        arg_fds = loop_fds.fds[0] != -1 ? &loop_fds : NULL;

        vfio_user_send_wait(proxy, &msgp->hdr, arg_fds, 0, false);
        if (msgp->hdr.flags & VFIO_USER_ERROR) {
            return -msgp->hdr.error_reply;
        }
    }

    return 0;
}

static int vfio_user_region_read(VFIOUserProxy *proxy, uint8_t index,
                                 off_t offset, uint32_t count, void *data)
{
    g_autofree VFIOUserRegionRW *msgp = NULL;
    int size = sizeof(*msgp) + count;

    if (count > proxy->max_xfer_size) {
        return -EINVAL;
    }

    msgp = g_malloc0(size);
    vfio_user_request_msg(&msgp->hdr, VFIO_USER_REGION_READ, sizeof(*msgp), 0);
    msgp->offset = offset;
    msgp->region = index;
    msgp->count = count;
    trace_vfio_user_region_rw(msgp->region, msgp->offset, msgp->count);

    vfio_user_send_wait(proxy, &msgp->hdr, NULL, size, false);
    if (msgp->hdr.flags & VFIO_USER_ERROR) {
        return -msgp->hdr.error_reply;
    } else if (msgp->count > count) {
        return -E2BIG;
    } else {
        memcpy(data, &msgp->data, msgp->count);
    }

    return msgp->count;
}

static void vfio_user_flush_multi(VFIOUserProxy *proxy)
{
    VFIOUserMsg *msg;
    VFIOUserWRMulti *wm = proxy->wr_multi;
    int ret;

    proxy->wr_multi = NULL;

    /* adjust size for actual # of writes */
    wm->hdr.size -= (VFIO_USER_MULTI_MAX - wm->wr_cnt) * sizeof(VFIOUserWROne);

    msg = vfio_user_getmsg(proxy, &wm->hdr, NULL);
    msg->id = wm->hdr.id;
    msg->rsize = 0;
    msg->type = VFIO_MSG_ASYNC;
    trace_vfio_user_wrmulti("flush", wm->wr_cnt);

    ret = vfio_user_send_queued(proxy, msg);
    if (ret < 0) {
        vfio_user_recycle(proxy, msg);
    }
}

static void vfio_user_create_multi(VFIOUserProxy *proxy)
{
    VFIOUserWRMulti *wm;

    wm = g_malloc0(sizeof(*wm));
    vfio_user_request_msg(&wm->hdr, VFIO_USER_REGION_WRITE_MULTI,
                          sizeof(*wm), VFIO_USER_NO_REPLY);
    proxy->wr_multi = wm;
}

static void vfio_user_add_multi(VFIOUserProxy *proxy, uint8_t index,
                                off_t offset, uint32_t count, void *data)
{
    VFIOUserWRMulti *wm = proxy->wr_multi;
    VFIOUserWROne *w1 = &wm->wrs[wm->wr_cnt];

    w1->offset = offset;
    w1->region = index;
    w1->count = count;
    memcpy(&w1->data, data, count);

    wm->wr_cnt++;
    trace_vfio_user_wrmulti("add", wm->wr_cnt);
    if (wm->wr_cnt == VFIO_USER_MULTI_MAX ||
        proxy->num_outgoing < VFIO_USER_OUT_LOW) {
        vfio_user_flush_multi(proxy);
    }
}

static int vfio_user_region_write(VFIOUserProxy *proxy, uint8_t index,
                                  off_t offset, uint32_t count, void *data,
                                  bool post)
{
    VFIOUserRegionRW *msgp = NULL;
    int flags;
    int size = sizeof(*msgp) + count;
    bool can_multi;
    int ret;

    if (count > proxy->max_xfer_size) {
        return -EINVAL;
    }

    if (proxy->flags & VFIO_PROXY_NO_POST) {
        post = false;
    }

    /* write eligible to be in a WRITE_MULTI msg ? */
    can_multi = (proxy->flags & VFIO_PROXY_USE_MULTI) && post &&
        count <= VFIO_USER_MULTI_DATA;

    /*
     * This should be a rare case, so first check without the lock,
     * if we're wrong, vfio_send_queued() will flush any posted writes
     * we missed here
     */
    if (proxy->wr_multi != NULL ||
        (proxy->num_outgoing > VFIO_USER_OUT_HIGH && can_multi)) {

        /*
         * re-check with lock
         *
         * if already building a WRITE_MULTI msg,
         *  add this one if possible else flush pending before
         *  sending the current one
         *
         * else if outgoing queue is over the highwater,
         *  start a new WRITE_MULTI message
         */
        WITH_QEMU_LOCK_GUARD(&proxy->lock) {
            if (proxy->wr_multi != NULL) {
                if (can_multi) {
                    vfio_user_add_multi(proxy, index, offset, count, data);
                    return count;
                }
                vfio_user_flush_multi(proxy);
            } else if (proxy->num_outgoing > VFIO_USER_OUT_HIGH && can_multi) {
                vfio_user_create_multi(proxy);
                vfio_user_add_multi(proxy, index, offset, count, data);
                return count;
            }
        }
    }

    flags = post ? VFIO_USER_NO_REPLY : 0;
    msgp = g_malloc0(size);
    vfio_user_request_msg(&msgp->hdr, VFIO_USER_REGION_WRITE, size, flags);
    msgp->offset = offset;
    msgp->region = index;
    msgp->count = count;
    memcpy(&msgp->data, data, count);
    trace_vfio_user_region_rw(msgp->region, msgp->offset, msgp->count);

    /* async send will free msg after it's sent */
    if (post) {
        vfio_user_send_async(proxy, &msgp->hdr, NULL);
        return count;
    }

    vfio_user_send_wait(proxy, &msgp->hdr, NULL, 0, false);
    if (msgp->hdr.flags & VFIO_USER_ERROR) {
        ret = -msgp->hdr.error_reply;
    } else {
        ret = count;
    }

    g_free(msgp);
    return ret;
}

void vfio_user_reset(VFIOUserProxy *proxy)
{
    VFIOUserHdr msg;

    vfio_user_request_msg(&msg, VFIO_USER_DEVICE_RESET, sizeof(msg), 0);

    vfio_user_send_wait(proxy, &msg, NULL, 0, false);
    if (msg.flags & VFIO_USER_ERROR) {
        error_printf("reset reply error %d\n", msg.error_reply);
    }
}


/*
 * Socket-based io_ops
 */

static int vfio_user_io_get_region_info(VFIODevice *vbasedev,
                                        struct vfio_region_info *info,
                                        int *fd)
{
    int ret;
    VFIOUserFDs fds = { 0, 1, fd};

    ret = vfio_user_get_region_info(vbasedev->proxy, info, &fds);
    if (ret) {
        return ret;
    }

    if (info->index > vbasedev->num_regions) {
        return -EINVAL;
    }
    /* cap_offset in valid area */
    if ((info->flags & VFIO_REGION_INFO_FLAG_CAPS) &&
        (info->cap_offset < sizeof(*info) || info->cap_offset > info->argsz)) {
        return -EINVAL;
    }

    return 0;
}

static int vfio_user_io_get_irq_info(VFIODevice *vbasedev,
                                     struct vfio_irq_info *irq)
{
    int ret;

    ret = vfio_user_get_irq_info(vbasedev->proxy, irq);
    if (ret) {
        return ret;
    }

    if (irq->index > vbasedev->num_irqs) {
        return -EINVAL;
    }
    return 0;
}

static int vfio_user_io_set_irqs(VFIODevice *vbasedev,
                                 struct vfio_irq_set *irqs)
{
    return vfio_user_set_irqs(vbasedev->proxy, irqs);
}

static int vfio_user_io_region_read(VFIODevice *vbasedev, uint8_t index,
                                    off_t off, uint32_t size, void *data)
{
    return vfio_user_region_read(vbasedev->proxy, index, off, size, data);
}

static int vfio_user_io_region_write(VFIODevice *vbasedev, uint8_t index,
                                     off_t off, unsigned size, void *data,
                                     bool post)
{
    return vfio_user_region_write(vbasedev->proxy, index, off, size, data,
                                  post);
}

VFIODeviceIO vfio_dev_io_sock = {
    .get_region_info = vfio_user_io_get_region_info,
    .get_irq_info = vfio_user_io_get_irq_info,
    .set_irqs = vfio_user_io_set_irqs,
    .region_read = vfio_user_io_region_read,
    .region_write = vfio_user_io_region_write,
};

static int vfio_user_io_dma_map(VFIOContainer *container, MemoryRegion *mr,
                                struct vfio_iommu_type1_dma_map *map)
{
    VFIOUserProxy *proxy = container->proxy;
    int fd = memory_region_get_fd(mr);

    /*
     * map->vaddr enters as a QEMU process address
     * make it either a file offset for mapped areas or 0
     */
    if (fd != -1 && (container->proxy->flags & VFIO_PROXY_NO_MMAP) == 0) {
        void *addr = (void *)(uintptr_t)map->vaddr;

        map->vaddr = qemu_ram_block_host_offset(mr->ram_block, addr);
    } else {
        map->vaddr = 0;
    }

    return vfio_user_dma_map(proxy, map, fd, proxy->async_ops);
}

static int vfio_user_io_dma_unmap(VFIOContainer *container,
                                  struct vfio_iommu_type1_dma_unmap *unmap)
{
    VFIOUserProxy *proxy = container->proxy;
    struct vfio_bitmap *bitmap;

    if (unmap->flags & VFIO_DMA_UNMAP_FLAG_GET_DIRTY_BITMAP) {
        bitmap = (struct vfio_bitmap *)&unmap->data;
    } else {
        bitmap = NULL;
    }
    return vfio_user_dma_unmap(proxy, unmap, bitmap, proxy->async_ops);
}

static void vfio_user_io_listener_begin(VFIOContainer *container)
{

    /*
     * When DMA space is the physical address space,
     * the region add/del listeners will fire during
     * memory update transactions.  These depend on BQL
     * being held, so do any resulting map/demap ops async
     * while keeping BQL.
     */
    container->proxy->async_ops = true;
}

static void vfio_user_io_listener_commit(VFIOContainer *container)
{
    /* wait here for any async requests sent during the transaction */
    container->proxy->async_ops = false;
    vfio_user_wait_reqs(container->proxy);
}

VFIOContainerIO vfio_cont_io_sock = {
    .dma_map = vfio_user_io_dma_map,
    .dma_unmap = vfio_user_io_dma_unmap,
    .listener_begin = vfio_user_io_listener_begin,
    .listener_commit = vfio_user_io_listener_commit,
};
