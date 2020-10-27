

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
#include "hw/pci/msi.h"
#include "hw/pci/msix.h"
#include "hw/pci/pci_bridge.h"
#include "hw/qdev-properties.h"
#include "migration/vmstate.h"
#include "qemu/error-report.h"
#include "qemu/main-loop.h"
#include "qemu/module.h"
#include "qemu/option.h"
#include "qemu/range.h"
#include "qemu/sockets.h"
#include "qemu/units.h"
#include "sysemu/kvm.h"
#include "sysemu/runstate.h"
#include "sysemu/sysemu.h"
#include "pci.h"
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
    }
    vfio_user_send(proxy, hdr, NULL);
}

void vfio_user_recv(void *opaque)
{
    VFIOPCIDevice *vdev = opaque;
    VFIOProxy *proxy = vdev->vbasedev.proxy;
    VFIOUserReply *reply = NULL;
    int fdarray[REMOTE_MAX_FDS];
    VFIOUserFDs reqfds = { 0, REMOTE_MAX_FDS, fdarray };
    VFIOUserFDs *fds = NULL;
    vfio_user_hdr_t msg;
    union {
        char control[CMSG_SPACE(REMOTE_MAX_FDS * sizeof(int))];
        struct cmsghdr align;
    } u;
    struct msghdr hdr;
    struct cmsghdr *chdr;
    struct iovec iov = {
        .iov_base = &msg,
        .iov_len = sizeof(msg),
    };
    int isreply, i, ret, numfds = 0;
    size_t fdsize, msgleft;
    int *fdp;
    char *data, *buf = NULL;

    memset(&hdr, 0, sizeof(hdr));
    memset(&u, 0, sizeof(u));

    hdr.msg_iov = &iov;
    hdr.msg_iovlen = 1;
    hdr.msg_control = &u;
    hdr.msg_controllen = sizeof(u);

    /*
     * Since we use a per-proxy lock, let
     * the iothreads run free
     */
    qemu_mutex_unlock_iothread();
    qemu_mutex_lock(&proxy->lock);

    /*
     * read the header into 'msg' and read any
     * control messages into 'cmsg'
     */
    ret = recvmsg(proxy->socket, &hdr, 0);
    if (ret < 0) {
        error_printf("vfio_user_recv read error\n");
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
            error_printf("vfio_usr_recv unexpected reply\n");
            goto err;
        }
        QTAILQ_REMOVE(&proxy->pending, reply, next);
        fds = reply->fds;
    } else {
        /* 
         * Yhe client doesn't expect any FDs in requests, so
         * reqfds.maxfds is 0 here to catch this below
         * they will be expected on the server, however
         */
        if (proxy->flags & VFIO_PROXY_CLIENT) {
            reqfds.maxfds = 0;
        }
        fds = &reqfds;
    }

    /*
     * Find any embedded file descriptors
     */
    for (chdr = CMSG_FIRSTHDR(&hdr); chdr != NULL;
         chdr = CMSG_NXTHDR(&hdr, chdr)) {
        if ((chdr->cmsg_level == SOL_SOCKET) &&
            (chdr->cmsg_type == SCM_RIGHTS)) {

            fdp = (int *)CMSG_DATA(chdr);
            fdsize = chdr->cmsg_len - CMSG_LEN(0);
            numfds = fdsize / sizeof(int);

            if (fds == NULL || fds->maxfds < numfds) {
                error_printf("vfio_user_recv unexpected FDs\n");
                goto err;
            }
            fds->numfds = numfds;
            memcpy(fds->fds, fdp, fdsize);
            break;
        }
    }

    /*
     * put the whole message into a single buffer
     */
    msgleft = msg.size - sizeof(msg);
    if (isreply) {
        if (msg.size > reply->rsize) {
            error_printf("reply larger than recv buffer\n");
            goto err;
        }
        *reply->msg = msg;
        data = (char *)reply->msg + sizeof(msg);
    } else {
        buf = g_malloc0(msg.size);
        memcpy(buf, &msg, sizeof(msg));
        data = buf + sizeof(msg);
    }

    ret = read(proxy->socket, data, msgleft);
    if (ret != msgleft) {
        error_printf("short read of msg body\n");
        goto err;
    }

    /*
     * Replies signal a waiter, requests get processed by vfio code
     * that may assume the iothread lock is held.
     */
    qemu_mutex_unlock(&proxy->lock);
    qemu_mutex_lock_iothread();
    if (isreply) {
        reply->complete = 1;
        qemu_cond_signal(&reply->cv);
    } else {
        ret = proxy->request(proxy->reqarg, buf, fds);
        if (ret < 0) {
            vfio_user_send_reply(proxy, buf, ret);
        }
        g_free(buf);
    }
    return;

err:
    qemu_mutex_unlock(&proxy->lock);
    for (i = 0; i < numfds; i++) {
        close(fdp[i]);
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
    qemu_mutex_lock_iothread();
}
    
            
static void vfio_user_send_locked(VFIOProxy *proxy, vfio_user_hdr_t *msg, VFIOUserFDs *fds)
{
    union {
        char control[CMSG_SPACE(REMOTE_MAX_FDS * sizeof(int))];
        struct cmsghdr align;
    } u;
    struct msghdr hdr;
    struct cmsghdr *chdr;
    struct iovec iov = {
        .iov_base = msg,
        .iov_len = msg->size,
    };
    int ret;

    memset(&hdr, 0, sizeof(hdr));
    hdr.msg_iov = &iov;
    hdr.msg_iovlen = 1;

    if (fds != NULL && fds->numfds > 0) {
        size_t fdsize = fds->numfds * sizeof(int);

        memset(&u, 0, sizeof(u));
        hdr.msg_control = &u;
        hdr.msg_controllen = sizeof(u);
    
        chdr = CMSG_FIRSTHDR(&hdr);
        chdr->cmsg_len = CMSG_LEN(fdsize);
        chdr->cmsg_level = SOL_SOCKET;
        chdr->cmsg_type = SCM_RIGHTS;
        memcpy(CMSG_DATA(chdr), fds->fds, fdsize);
        hdr.msg_controllen = CMSG_SPACE(fdsize);
    }

    do {
        ret = sendmsg(proxy->socket, &hdr, 0);
    } while (ret < 0 && errno == EINTR);

    if (ret < 0) {
        error_printf("vfio_user_send errno %d\n", errno);
    }
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

VFIOProxy *vfio_user_connect_dev(char *sockname, Error **errp)
{
    VFIOProxy *proxy;
    int sockfd;

    sockfd = unix_connect(sockname, errp);
    if (sockfd == -1) {
        return NULL;
    }

    proxy = g_malloc0(sizeof(VFIOProxy));
    proxy->socket = sockfd;
    proxy->sockname = sockname;
    proxy->flags = VFIO_PROXY_CLIENT;

    qemu_mutex_init(&proxy->lock);
    QTAILQ_INIT(&proxy->free);
    QTAILQ_INIT(&proxy->pending);

    return proxy;
}

void vfio_user_disconnect(VFIOProxy *proxy)
{
    VFIOUserReply *r1, *r2;

    qemu_set_fd_handler(proxy->socket, NULL, NULL, NULL);
    QTAILQ_FOREACH_SAFE(r1, &proxy->free, next, r2) {
        QTAILQ_REMOVE(&proxy->free, r1, next);
        g_free(r1);
    }
    close(proxy->socket);
    g_free(proxy);
}

int vfio_user_validate_version(VFIODevice *vbasedev, Error **errp)
{
    struct vfio_user_version msg;

    vfio_user_request_msg(&msg.hdr, VFIO_USER_VERSION, sizeof(msg), 0);
    msg.major = 1;
    msg.minor = 0;

    vfio_user_send_recv(vbasedev->proxy, &msg.hdr, NULL, 0);
    if (msg.hdr.flags & VFIO_USER_ERROR) {
        error_setg_errno(errp, msg.hdr.error_reply, "version reply");
        return -1;
    }

    if (msg.major != VFIO_USER_MAJOR_VER || msg.minor > VFIO_USER_MINOR_VER) {
        error_setg(errp, "incompatible server version");
        return -1;
    }
    return 0;
}

int vfio_user_dma_map(VFIOProxy *proxy, struct vfio_user_map *map, VFIOUserFDs *fds,
                      uint64_t nelem)
{
    struct vfio_user_dma_map *msgp;
    int size = sizeof(*msgp) + (nelem * sizeof(struct vfio_user_map));
    int ret;

    if (fds->numfds != nelem) {
        error_printf("vfio_user_dma_map mismatch of FDs and table elements\n");
        return -EINVAL;
    }
    msgp = g_malloc0(size);
    vfio_user_request_msg(&msgp->hdr, VFIO_USER_DMA_MAP, size, 0);
    memcpy(&msgp->table, map, nelem * sizeof(*map));

    vfio_user_send_recv(proxy, &msgp->hdr, fds, 0);
    ret = (msgp->hdr.flags & VFIO_USER_ERROR) ? -msgp->hdr.error_reply : 0;

    g_free(msgp);
    return ret;
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
    size = info->argsz + sizeof(vfio_user_hdr_t);
    msgp = g_malloc0(size);

    vfio_user_request_msg(&msgp->hdr, VFIO_USER_DEVICE_GET_REGION_INFO, sizeof(*msgp), 0);
    msgp->reg_info = *info;

    vfio_user_send_recv(vbasedev->proxy, &msgp->hdr, fds, size);
    if (msgp->hdr.flags & VFIO_USER_ERROR) {
        return -msgp->hdr.error_reply;
    }

    memcpy(info, &msgp->reg_info, info->argsz);
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

int vfio_user_set_irq_info(VFIODevice *vbasedev, struct vfio_irq_set *irq)
{
    struct vfio_user_irq_set smallmsg, *msgp;

    /* only allocate if sending data array with set message */
    if (irq->argsz < sizeof(*irq)) {
        error_printf("vfio_user_set_irq_info argsz too small\n");
        return -EINVAL;
    }
    msgp = irq->argsz > sizeof(smallmsg) ? g_malloc0(irq->argsz) : &smallmsg;

    vfio_user_request_msg(&msgp->hdr, VFIO_USER_DEVICE_GET_IRQ_INFO, irq->argsz, 0);
    memcpy(&msgp->irq_set, irq, irq->argsz);

    vfio_user_send_recv(vbasedev->proxy, &msgp->hdr, NULL, 0);
    if (msgp->hdr.flags & VFIO_USER_ERROR) {
        return -msgp->hdr.error_reply;
    }

    if (msgp != &smallmsg) {
        g_free(msgp);
    }
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
        memcpy(data, (char *)msgp + sizeof(*msgp), msgp->count);
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
    memcpy((char *)msgp + sizeof(*msgp), data, count);

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
