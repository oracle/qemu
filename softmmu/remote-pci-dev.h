/*
 * Copyright © 2018, 2020 Oracle and/or its affiliates.
 *
 * This work is licensed under the terms of the GNU GPL, version 2 or later.
 * See the COPYING file in the top-level directory.
 *
 */

#ifndef QEMU_REMOTE_PCI_DEV_H
#define QEMU_REMOTE_PCI_DEV_H

#include "qom/object.h"
#include "qom/object_interfaces.h"

#define TYPE_REMOTE_PCI_DEV "remote-pci-dev"

#define REMOTE_PCI_DEV(obj) \
            OBJECT_CHECK(RemotePCIDev, (obj), TYPE_REMOTE_PCI_DEV)

#define REMOTE_PCI_DEV_CLASS(klass) \
            OBJECT_CLASS_CHECK(RemotePCIDevClass, (klass), TYPE_REMOTE_PCI_DEV)

#define REMOTE_PCI_DEV_GET_CLASS(obj) \
            OBJECT_GET_CLASS(RemotePCIDevClass, (obj), TYPE_REMOTE_PCI_DEV)

typedef struct RemotePCIDev RemotePCIDev;

struct RemotePCIDev {
    DeviceClass parent_obj;
    char *remote_device;
};

typedef struct RemotePCIDevClass {
    DeviceClass parent_class;

} RemotePCIDevClass;

#endif //QEMU_REMOTE_PCI_DEV_H
