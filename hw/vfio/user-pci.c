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

#define TYPE_VFIO_USER_PCI "vfio-user-pci"
OBJECT_DECLARE_SIMPLE_TYPE(VFIOUserPCIDevice, VFIO_USER_PCI)

struct VFIOUserPCIDevice {
    VFIOPCIDevice device;
    char *sock_name;
};

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

    vbasedev->name = g_strdup_printf("VFIO user <%s>", udev->sock_name);
    vbasedev->ops = &vfio_user_pci_ops;
    vbasedev->type = VFIO_DEVICE_TYPE_PCI;
    vbasedev->dev = DEVICE(vdev);

}

static void vfio_user_instance_finalize(Object *obj)
{
    VFIOPCIDevice *vdev = VFIO_PCI_BASE(obj);

    vfio_put_device(vdev);
}

static Property vfio_user_pci_dev_properties[] = {
    DEFINE_PROP_STRING("socket", VFIOUserPCIDevice, sock_name),
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
