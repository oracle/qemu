/*
 * Copyright © 2018, 2020 Oracle and/or its affiliates.
 *
 * This work is licensed under the terms of the GNU GPL, version 2 or later.
 * See the COPYING file in the top-level directory.
 *
 */

#ifndef QEMU_REMOTE_DEV_H
#define QEMU_REMOTE_DEV_H

#include "qom/object.h"
#include "qom/object_interfaces.h"
#include "hw/proxy/qemu-proxy.h"

#define TYPE_REMOTE_DEV "remote-dev"

#define REMOTE_DEV(obj) \
            OBJECT_CHECK(RemoteDev, (obj), TYPE_REMOTE_DEV)

#define REMOTE_DEV_CLASS(klass) \
            OBJECT_CLASS_CHECK(RemoteDevClass, (klass), TYPE_REMOTE_DEV)

#define REMOTE_DEV_GET_CLASS(obj) \
            OBJECT_GET_CLASS(RemoteDevClass, (obj), TYPE_REMOTE_DEV)

typedef struct RemoteDev RemoteDev;

struct RemoteDev {
    Object parent_obj;
    char *exec;
    char *command;
    int socket;
    PCIProxyDev *(*create_proxy)(Object *obj, Error **errp);
    PCIProxyDev *proxy;
};

typedef struct RemoteDevClass {
    ObjectClass parent_class;

} RemoteDevClass;

#endif /* QEMU_REMOTE_DEV_H */
