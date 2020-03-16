/*
 * Copyright © 2018, 2020 Oracle and/or its affiliates.
 *
 * This work is licensed under the terms of the GNU GPL, version 2 or later.
 * See the COPYING file in the top-level directory.
 *
 */
#include "qemu/osdep.h"
#include "qemu-common.h"
#include "qapi/error.h"
#include "hw/qdev-core.h"
#include "qom/object.h"
#include "qom/object_interfaces.h"
#include "remote-pci-dev.h"
#include "remote-dev.h"

static void remote_pci_dev_class_init(ObjectClass *oc, void *data)
{
}

static void remote_pci_dev_set_rdevice(Object *obj, const char *remote_device,
                                 Error **errp)
{
    RemotePCIDev *rpdev = REMOTE_PCI_DEV(obj);
    Object *local_obj;
    RemoteDev *rdev; 

    if (rpdev->remote_device) {
        g_free(rpdev->remote_device);
    }
    if (remote_device) {
        rpdev->remote_device = g_strdup(remote_device);

        local_obj = object_resolve_path_component(
            object_get_objects_root(), remote_device);
        if (!local_obj) {
            error_setg(errp, "No remote-device with id '%s'",
                       remote_device);
            return;
        }
        rdev = (RemoteDev *)
            object_dynamic_cast(local_obj, TYPE_REMOTE_DEV);
        if (!rdev) {
            error_setg(errp, "Object with id '%s' is not Remote Device",
                       remote_device);
            return;
        }
    }

}

static char *remote_pci_dev_get_rdevice(Object *obj, Error **errp)
{
    RemotePCIDev *rpdev = REMOTE_PCI_DEV(obj);

    return g_strdup(rpdev->remote_device);
}

static void remote_pci_dev_inst_init(Object *obj)
{
     //RemotePCIDev *rdev = REMOTE_PCI_DEV(obj);

     object_property_add_str(obj, "remote-device",
                            remote_pci_dev_get_rdevice,
                            remote_pci_dev_set_rdevice,
                            NULL);

}

static void remote_pci_dev_int_finalize(Object *obj)
{
    //RemotePCIDev *rdev = REMOTE_PCI_DEV(obj);
}

static const TypeInfo remote_pci_dev_info = {
    .name = TYPE_REMOTE_PCI_DEV,
    .parent = TYPE_DEVICE,
    .class_init = remote_pci_dev_class_init,
    .instance_size = sizeof(RemotePCIDev),
    .instance_init = remote_pci_dev_inst_init,
    .instance_finalize = remote_pci_dev_int_finalize,
    .interfaces = (InterfaceInfo[]) {
        { TYPE_USER_CREATABLE },
        { }
    }
};

static void register_types(void)
{
    type_register_static(&remote_pci_dev_info);
}

type_init(register_types);

