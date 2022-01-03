/*
 * vfio PCI device over a UNIX socket.
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

#include "hw/hw.h"
#include "hw/pci/msi.h"
#include "hw/pci/msix.h"
#include "hw/pci/pci_bridge.h"
#include "hw/qdev-properties.h"
#include "hw/qdev-properties-system.h"
#include "migration/vmstate.h"
#include "qapi/qmp/qdict.h"
#include "qemu/error-report.h"
#include "qemu/main-loop.h"
#include "qemu/module.h"
#include "qemu/range.h"
#include "qemu/units.h"
#include "sysemu/kvm.h"
#include "sysemu/runstate.h"
#include "pci.h"
#include "trace.h"
#include "qapi/error.h"
#include "migration/blocker.h"
#include "migration/qemu-file.h"
#include "hw/vfio/user.h"

#define TYPE_VFIO_USER_PCI "vfio-user-pci"
OBJECT_DECLARE_SIMPLE_TYPE(VFIOUserPCIDevice, VFIO_USER_PCI)

struct VFIOUserPCIDevice {
    VFIOPCIDevice device;
    char *sock_name;
    bool no_direct_dma; /* disable shared mem for DMA */
    bool send_queued;   /* all sends are queued */
    bool no_post;       /* all regions write are sync */
};

/*
 * The server maintains the device's pending interrupts,
 * via its MSIX table and PBA, so we treat these acceses
 * like PCI config space and forward them.
 */
static uint64_t vfio_user_pba_read(void *opaque, hwaddr addr,
                                   unsigned size)
{
    VFIOPCIDevice *vdev = opaque;
    VFIORegion *region = &vdev->bars[vdev->msix->pba_bar].region;
    uint64_t data;

    /* server copy is what matters */
    data = vfio_region_read(region, addr + vdev->msix->pba_offset, size);
    return data;
}

static void vfio_user_pba_write(void *opaque, hwaddr addr,
                                  uint64_t data, unsigned size)
{
    /* dropped */
}

static const MemoryRegionOps vfio_user_pba_ops = {
    .read = vfio_user_pba_read,
    .write = vfio_user_pba_write,
    .endianness = DEVICE_LITTLE_ENDIAN,
};

static void vfio_user_msix_setup(VFIOPCIDevice *vdev)
{
    MemoryRegion *vfio_reg, *msix_reg, *pba_reg;

    pba_reg = g_new0(MemoryRegion, 1);
    vdev->msix->pba_region = pba_reg;

    vfio_reg = vdev->bars[vdev->msix->pba_bar].mr;
    msix_reg = &vdev->pdev.msix_pba_mmio;
    memory_region_init_io(pba_reg, OBJECT(vdev), &vfio_user_pba_ops, vdev,
                          "VFIO MSIX PBA", int128_get64(msix_reg->size));
    memory_region_add_subregion_overlap(vfio_reg, vdev->msix->pba_offset,
                                        pba_reg, 1);
}

static void vfio_user_msix_teardown(VFIOPCIDevice *vdev)
{
    MemoryRegion *mr, *sub;

    mr = vdev->bars[vdev->msix->pba_bar].mr;
    sub = vdev->msix->pba_region;
    memory_region_del_subregion(mr, sub);

    g_free(vdev->msix->pba_region);
    vdev->msix->pba_region = NULL;
}

/*
 * Incoming request message callback.
 *
 * Runs off main loop, so BQL held.
 */
static void vfio_user_pci_process_req(void *opaque, VFIOUserMsg *msg)
{

}

/*
 * Emulated devices don't use host hot reset
 */
static void vfio_user_compute_needs_reset(VFIODevice *vbasedev)
{
    vbasedev->needs_reset = false;
}

static VFIODeviceOps vfio_user_pci_ops = {
    .vfio_compute_needs_reset = vfio_user_compute_needs_reset,
    .vfio_eoi = vfio_intx_eoi,
    .vfio_get_object = vfio_pci_get_object,
    .vfio_save_config = vfio_pci_save_config,
    .vfio_load_config = vfio_pci_load_config,
};

static void vfio_user_pci_realize(PCIDevice *pdev, Error **errp)
{
    ERRP_GUARD();
    VFIOUserPCIDevice *udev = VFIO_USER_PCI(pdev);
    VFIOPCIDevice *vdev = VFIO_PCI_BASE(pdev);
    VFIODevice *vbasedev = &vdev->vbasedev;
    SocketAddress addr;
    VFIOUserProxy *proxy;
    VFIOGroup *group = NULL;
    int ret;
    Error *err = NULL;

    /*
     * TODO: make option parser understand SocketAddress
     * and use that instead of having scalar options
     * for each socket type.
     */
    if (!udev->sock_name) {
        error_setg(errp, "No socket specified");
        error_append_hint(errp, "Use -device vfio-user-pci,socket=<name>\n");
        return;
    }

    memset(&addr, 0, sizeof(addr));
    addr.type = SOCKET_ADDRESS_TYPE_UNIX;
    addr.u.q_unix.path = udev->sock_name;
    proxy = vfio_user_connect_dev(&addr, &err);
    if (!proxy) {
        error_propagate(errp, err);
        return;
    }
    vbasedev->proxy = proxy;
    vfio_user_set_handler(vbasedev, vfio_user_pci_process_req, vdev);

    if (udev->no_direct_dma) {
        proxy->flags |= VFIO_PROXY_NO_MMAP;
    }
    if (udev->send_queued) {
        proxy->flags |= VFIO_PROXY_FORCE_QUEUED;
    }
    if (udev->no_post) {
        proxy->flags |= VFIO_PROXY_NO_POST;
    }

    vfio_user_validate_version(proxy, &err);
    if (err != NULL) {
        error_propagate(errp, err);
        goto error;
    }

    vbasedev->name = g_strdup_printf("VFIO user <%s>", udev->sock_name);
    vbasedev->ops = &vfio_user_pci_ops;
    vbasedev->type = VFIO_DEVICE_TYPE_PCI;
    vbasedev->dev = DEVICE(vdev);
    vbasedev->io = &vfio_dev_io_sock;
    vbasedev->use_regfds = true;

    group = vfio_user_get_group(proxy, pci_device_iommu_address_space(pdev),
                                errp);
    if (!group) {
        goto error;
    }

    ret = vfio_user_get_device(group, vbasedev, errp);
    if (ret) {
        vfio_user_put_group(group);
        goto error;
    }

    vfio_populate_device(vdev, &err);
    if (err) {
        error_propagate(errp, err);
        goto error;
    }

    /* Get a copy of config space */
    ret = vbasedev->io->region_read(vbasedev, VFIO_PCI_CONFIG_REGION_INDEX, 0,
                               MIN(pci_config_size(pdev), vdev->config_size),
                               pdev->config);
    if (ret < (int)MIN(pci_config_size(&vdev->pdev), vdev->config_size)) {
        error_setg_errno(errp, -ret, "failed to read device config space");
        goto error;
    }

    vfio_pci_config_setup(vdev, &err);
    if (err) {
        error_propagate(errp, err);
        goto error;
    }

    /*
     * vfio_pci_config_setup will have registered the device's BARs
     * and setup any MSIX BARs, so errors after it succeeds must
     * use out_teardown
     */

    ret = vfio_add_capabilities(vdev, errp);
    if (ret) {
        goto out_teardown;
    }
    if (vdev->msix != NULL) {
        vfio_user_msix_setup(vdev);
    }

    ret = vfio_interrupt_setup(vdev, errp);
    if (ret) {
        goto out_teardown;
    }

    vfio_register_err_notifier(vdev);
    vfio_register_req_notifier(vdev);

    return;

out_teardown:
    vfio_teardown_msi(vdev);
    vfio_bars_exit(vdev);
error:
    error_prepend(errp, VFIO_MSG_PREFIX, vdev->vbasedev.name);
}

static void vfio_user_instance_finalize(Object *obj)
{
    VFIOPCIDevice *vdev = VFIO_PCI_BASE(obj);
    VFIODevice *vbasedev = &vdev->vbasedev;
    VFIOGroup *group = vbasedev->group;

    vfio_bars_finalize(vdev);
    g_free(vdev->emulated_config_bits);
    g_free(vdev->rom);

    if (vdev->msix != NULL) {
        vfio_user_msix_teardown(vdev);
    }

    vfio_put_device(vdev);
    vfio_user_put_group(group);

    if (vbasedev->proxy != NULL) {
        vfio_user_disconnect(vbasedev->proxy);
    }
}

static Property vfio_user_pci_dev_properties[] = {
    DEFINE_PROP_STRING("socket", VFIOUserPCIDevice, sock_name),
    DEFINE_PROP_BOOL("no-direct-dma", VFIOUserPCIDevice, no_direct_dma, false),
    DEFINE_PROP_BOOL("x-send-queued", VFIOUserPCIDevice, send_queued, false),
    DEFINE_PROP_BOOL("x-no-posted-writes", VFIOUserPCIDevice, no_post, false),
    DEFINE_PROP_END_OF_LIST(),
};

static void vfio_user_pci_dev_class_init(ObjectClass *klass, void *data)
{
    DeviceClass *dc = DEVICE_CLASS(klass);
    PCIDeviceClass *pdc = PCI_DEVICE_CLASS(klass);

    device_class_set_props(dc, vfio_user_pci_dev_properties);
    dc->desc = "VFIO over socket PCI device assignment";
    pdc->realize = vfio_user_pci_realize;
}

static const TypeInfo vfio_user_pci_dev_info = {
    .name = TYPE_VFIO_USER_PCI,
    .parent = TYPE_VFIO_PCI_BASE,
    .instance_size = sizeof(VFIOUserPCIDevice),
    .class_init = vfio_user_pci_dev_class_init,
    .instance_init = vfio_instance_init,
    .instance_finalize = vfio_user_instance_finalize,
};

static void register_vfio_user_dev_type(void)
{
    type_register_static(&vfio_user_pci_dev_info);
}

type_init(register_vfio_user_dev_type)
