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
#include "monitor/qdev.h"
#include "qemu/option.h"
#include "qapi/qmp/qstring.h"
#include "qom/object.h"
#include "qom/object_interfaces.h"
#include "sysemu/sysemu.h"
#include "qemu/option.h"

#include "remote-dev.h"

static void remote_dev_class_init(ObjectClass *oc, void *data);

static void remote_dev_set_exec(Object *obj, const char *value, Error **errp)
{
    RemoteDev *rdev = REMOTE_DEV(obj);

    if (rdev->exec) {
        g_free(rdev->exec);
    }
    if (value) {
        rdev->exec = g_strdup(value);
    }
}

static char *remote_dev_get_exec(Object *obj, Error **errp)
{
    RemoteDev *rdev = REMOTE_DEV(obj);

    return g_strdup(rdev->exec);
}

static void remote_dev_set_command(Object *obj, const char *value, Error **errp)
{
    RemoteDev *rdev = REMOTE_DEV(obj);

    if (rdev->command) {
        g_free(rdev->command);
    }
    if (value) {
        rdev->command = g_strdup(value);
    } 
}

static char *remote_dev_get_command(Object *obj, Error **errp)
{
    RemoteDev *rdev = REMOTE_DEV(obj);

    return g_strdup(rdev->command);
}

static void remote_dev_set_socket(Object *obj, Visitor *v, const char *name,
                                  void *opaque, Error **errp)
{
    RemoteDev *rdev = REMOTE_DEV(obj);
    uint32_t value;
    Error *local_err = NULL;

    visit_type_uint32(v, name, &value, &local_err);
    if (local_err) {
        goto out;
    }
    if (!value) {
        error_setg(&local_err, "Property '%s.%s' doesn't take value '%"
                   PRIu32 "'", object_get_typename(obj), name, value);
        goto out;
    }
    rdev->socket = value;
out:
    error_propagate(errp, local_err);
}

static void
remote_dev_get_socket(Object *obj, Visitor *v, const char *name,
                             void *opaque, Error **errp)
{
    RemoteDev *rdev = REMOTE_DEV(obj);
    uint64_t value = rdev->socket;

    visit_type_uint64(v, name, &value, errp);
}

static PCIProxyDev *create_proxy(Object *obj, Error **errp)
{
    //PCIProxyDev *pdev;
    DeviceState *ds;
    char *rid = NULL;
    //ObjectProperty *p;
    Error *local_err;

    //p = g_hash_table_lookup(obj->properties, "id");
    //if (!p) {
    //    return NULL;
    //}
    rid = object_get_canonical_path_component(obj);

    uint64_t socket = object_property_get_int(obj, "socket", NULL);
    char *command = object_property_get_str(obj, "command", NULL);
    char *exec_name = object_property_get_str(obj, "exec", NULL);
    fprintf(stderr, "parameters for proxy: command %s, exec %s, socket %lu\n",
            command, exec_name, socket);
    /* Add bus here. */
    char *bus = NULL;
    char *id = NULL;

    fprintf(stderr, "Will try to create proxy for rid %s!\n", rid);
    ds = qdev_proxy_add(rid, id, (char *)bus, (char *)command,
                         (char *)exec_name,
                         socket ? socket : -1,
                         socket != -1 ? true : false, &local_err);
    if (!ds) {
        fprintf(stderr, "qdev_proxy_add error.");
        error_setg(errp, "qdev_proxy_add error.");
        return NULL;
    }

    return PCI_PROXY_DEV(ds);
}

static void remote_dev_inst_init(Object *obj)
{
    RemoteDev *rdev = REMOTE_DEV(obj);
    rdev->create_proxy = create_proxy;
}

static void remote_dev_class_init(ObjectClass *oc, void *data)
{

    object_class_property_add(oc, "socket", "int",
                           remote_dev_get_socket,
                           remote_dev_set_socket,
                           NULL, NULL, NULL);

    object_class_property_add_str(oc, "exec",
                           remote_dev_get_exec,
                           remote_dev_set_exec,
                           NULL);
    //object_class_property_add(oc, -1, "socket", NULL);

    object_class_property_add_str(oc, "command",
                           remote_dev_get_command,
                           remote_dev_set_command,
                           NULL);
    //rdev->exec = NULL;

}

static void remote_dev_inst_finalize(Object *obj)
{
    RemoteDev *rdev = REMOTE_DEV(obj);
    
    if (rdev->exec) {
        g_free(rdev->exec);
    }
}

static const TypeInfo remote_dev_info = {
    .name = TYPE_REMOTE_DEV,
    .parent = TYPE_OBJECT,
    .class_init = remote_dev_class_init,
    .instance_size = sizeof(RemoteDev),
    .instance_init = remote_dev_inst_init,
    .instance_finalize = remote_dev_inst_finalize,
    .interfaces = (InterfaceInfo[]) {
        { TYPE_USER_CREATABLE },
        { }
    }
};

static void register_types(void)
{
    type_register_static(&remote_dev_info);
}

type_init(register_types);
