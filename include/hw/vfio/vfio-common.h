/*
 * common header for vfio based device assignment support
 *
 * Copyright Red Hat, Inc. 2012
 *
 * Authors:
 *  Alex Williamson <alex.williamson@redhat.com>
 *
 * This work is licensed under the terms of the GNU GPL, version 2.  See
 * the COPYING file in the top-level directory.
 *
 * Based on qemu-kvm device-assignment:
 *  Adapted for KVM by Qumranet.
 *  Copyright (c) 2007, Neocleus, Alex Novik (alex@neocleus.com)
 *  Copyright (c) 2007, Neocleus, Guy Zana (guy@neocleus.com)
 *  Copyright (C) 2008, Qumranet, Amit Shah (amit.shah@qumranet.com)
 *  Copyright (C) 2008, Red Hat, Amit Shah (amit.shah@redhat.com)
 *  Copyright (C) 2008, IBM, Muli Ben-Yehuda (muli@il.ibm.com)
 */

#ifndef HW_VFIO_VFIO_COMMON_H
#define HW_VFIO_VFIO_COMMON_H

#include "exec/memory.h"
#include "qemu/queue.h"
#include "qemu/notify.h"
#include "ui/console.h"
#include "hw/display/ramfb.h"
#ifdef CONFIG_LINUX
#include <linux/vfio.h>
#endif
#include "sysemu/sysemu.h"

#define VFIO_MSG_PREFIX "vfio %s: "

enum {
    VFIO_DEVICE_TYPE_PCI = 0,
    VFIO_DEVICE_TYPE_PLATFORM = 1,
    VFIO_DEVICE_TYPE_CCW = 2,
    VFIO_DEVICE_TYPE_AP = 3,
};

typedef struct VFIOMmap {
    MemoryRegion mem;
    void *mmap;
    off_t offset;
    size_t size;
} VFIOMmap;

typedef struct VFIORegion {
    struct VFIODevice *vbasedev;
    off_t fd_offset; /* offset of region within device fd */
    MemoryRegion *mem; /* slow, read/write access */
    size_t size;
    uint32_t flags; /* VFIO region flags (rd/wr/mmap) */
    uint32_t nr_mmaps;
    VFIOMmap *mmaps;
    uint8_t nr; /* cache the region number for debug */
    int fd; /* fd to mmap() region */
    bool post_wr; /* writes can be posted */
} VFIORegion;

typedef struct VFIOMigration {
    struct VFIODevice *vbasedev;
    VMChangeStateEntry *vm_state;
    Notifier migration_state;
    uint32_t device_state;
    int data_fd;
    void *data_buffer;
    size_t data_buffer_size;
    uint64_t mig_flags;
    uint64_t precopy_init_size;
    uint64_t precopy_dirty_size;
    bool initial_data_sent;
} VFIOMigration;

typedef struct VFIOAddressSpace {
    AddressSpace *as;
    QLIST_HEAD(, VFIOContainer) containers;
    QLIST_ENTRY(VFIOAddressSpace) list;
} VFIOAddressSpace;

struct VFIOGroup;
typedef struct VFIOContainerIO VFIOContainerIO;
typedef struct VFIOUserProxy VFIOUserProxy;

typedef struct VFIOContainer {
    VFIOAddressSpace *space;
    int fd; /* /dev/vfio/vfio, empowered by the attached groups */
    MemoryListener listener;
    MemoryListener prereg_listener;
    unsigned iommu_type;
    Error *error;
    VFIOContainerIO *io;
    bool initialized;
    bool dirty_pages_supported;
    uint64_t dirty_pgsizes;
    uint64_t max_dirty_bitmap_size;
    unsigned long pgsizes;
    unsigned int dma_max_mappings;
    VFIOUserProxy *proxy;
    QLIST_HEAD(, VFIOGuestIOMMU) giommu_list;
    QLIST_HEAD(, VFIOHostDMAWindow) hostwin_list;
    QLIST_HEAD(, VFIOGroup) group_list;
    QLIST_HEAD(, VFIORamDiscardListener) vrdl_list;
    QLIST_ENTRY(VFIOContainer) next;
} VFIOContainer;

typedef struct VFIOGuestIOMMU {
    VFIOContainer *container;
    IOMMUMemoryRegion *iommu_mr;
    hwaddr iommu_offset;
    IOMMUNotifier n;
    QLIST_ENTRY(VFIOGuestIOMMU) giommu_next;
} VFIOGuestIOMMU;

typedef struct VFIORamDiscardListener {
    VFIOContainer *container;
    MemoryRegion *mr;
    hwaddr offset_within_address_space;
    hwaddr size;
    uint64_t granularity;
    RamDiscardListener listener;
    QLIST_ENTRY(VFIORamDiscardListener) next;
} VFIORamDiscardListener;

typedef struct VFIOHostDMAWindow {
    hwaddr min_iova;
    hwaddr max_iova;
    uint64_t iova_pgsizes;
    QLIST_ENTRY(VFIOHostDMAWindow) hostwin_next;
} VFIOHostDMAWindow;

typedef struct VFIODeviceOps VFIODeviceOps;
typedef struct VFIODeviceIO VFIODeviceIO;

typedef struct VFIODevice {
    QLIST_ENTRY(VFIODevice) next;
    struct VFIOGroup *group;
    char *sysfsdev;
    char *name;
    DeviceState *dev;
    int fd;
    int type;
    bool reset_works;
    bool needs_reset;
    bool no_mmap;
    bool ram_block_discard_allowed;
    OnOffAuto enable_migration;
    bool use_regfds;
    VFIODeviceOps *ops;
    VFIODeviceIO *io;
    unsigned int num_irqs;
    unsigned int num_regions;
    unsigned int flags;
    VFIOMigration *migration;
    Error *migration_blocker;
    OnOffAuto pre_copy_dirty_page_tracking;
    bool dirty_pages_supported;
    bool dirty_tracking;
    VFIOUserProxy *proxy;
    struct vfio_region_info **regions;
    int *regfds;
} VFIODevice;

struct VFIODeviceOps {
    void (*vfio_compute_needs_reset)(VFIODevice *vdev);
    int (*vfio_hot_reset_multi)(VFIODevice *vdev);
    void (*vfio_eoi)(VFIODevice *vdev);
    Object *(*vfio_get_object)(VFIODevice *vdev);
    void (*vfio_save_config)(VFIODevice *vdev, QEMUFile *f);
    int (*vfio_load_config)(VFIODevice *vdev, QEMUFile *f);
};

#ifdef CONFIG_LINUX

/*
 * The next 2 ops vectors are how Devices and Containers
 * communicate with the server.  The default option is
 * through ioctl() to the kernel VFIO driver, but vfio-user
 * can use a socket to a remote process.
 */
struct VFIODeviceIO {
    int (*get_region_info)(VFIODevice *vdev,
                           struct vfio_region_info *info, int *fd);
    int (*get_irq_info)(VFIODevice *vdev, struct vfio_irq_info *irq);
    int (*set_irqs)(VFIODevice *vdev, struct vfio_irq_set *irqs);
    int (*region_read)(VFIODevice *vdev, uint8_t nr, off_t off, uint32_t size,
                       void *data);
    int (*region_write)(VFIODevice *vdev, uint8_t nr, off_t off, uint32_t size,
                        void *data, bool post);
};

struct VFIOContainerIO {
    int (*dma_map)(VFIOContainer *container, MemoryRegion *mr,
                   struct vfio_iommu_type1_dma_map *map);
    int (*dma_unmap)(VFIOContainer *container,
                     struct vfio_iommu_type1_dma_unmap *unmap);
    int (*dirty_bitmap)(VFIOContainer *container,
                        struct vfio_iommu_type1_dirty_bitmap *bitmap);
    void (*listener_begin)(VFIOContainer *container);
    void (*listener_commit)(VFIOContainer *container);
};

extern VFIODeviceIO vfio_dev_io_ioctl;

#endif /* CONFIG_LINUX */

typedef struct VFIOGroup {
    int fd;
    int groupid;
    VFIOContainer *container;
    QLIST_HEAD(, VFIODevice) device_list;
    QLIST_ENTRY(VFIOGroup) next;
    QLIST_ENTRY(VFIOGroup) container_next;
    bool ram_block_discard_allowed;
} VFIOGroup;

typedef struct VFIODMABuf {
    QemuDmaBuf buf;
    uint32_t pos_x, pos_y, pos_updates;
    uint32_t hot_x, hot_y, hot_updates;
    int dmabuf_id;
    QTAILQ_ENTRY(VFIODMABuf) next;
} VFIODMABuf;

typedef struct VFIODisplay {
    QemuConsole *con;
    RAMFBState *ramfb;
    struct vfio_region_info *edid_info;
    struct vfio_region_gfx_edid *edid_regs;
    uint8_t *edid_blob;
    QEMUTimer *edid_link_timer;
    struct {
        VFIORegion buffer;
        DisplaySurface *surface;
    } region;
    struct {
        QTAILQ_HEAD(, VFIODMABuf) bufs;
        VFIODMABuf *primary;
        VFIODMABuf *cursor;
    } dmabuf;
} VFIODisplay;

int vfio_ram_block_discard_disable(VFIOContainer *container, bool state);
void vfio_put_base_device(VFIODevice *vbasedev);
void vfio_disable_irqindex(VFIODevice *vbasedev, int index);
void vfio_unmask_single_irqindex(VFIODevice *vbasedev, int index);
void vfio_mask_single_irqindex(VFIODevice *vbasedev, int index);
void vfio_unmask_single_irq(VFIODevice *vbasedev, int index, int irq);
void vfio_mask_single_irq(VFIODevice *vbasedev, int index, int irq);
int vfio_set_irq_signaling(VFIODevice *vbasedev, int index, int subindex,
                           int action, int fd, Error **errp);
void vfio_host_win_add(VFIOContainer *container, hwaddr min_iova,
                       hwaddr max_iova, uint64_t iova_pgsizes);
void vfio_listener_release(VFIOContainer *container);
void vfio_region_write(void *opaque, hwaddr addr,
                           uint64_t data, unsigned size);
uint64_t vfio_region_read(void *opaque,
                          hwaddr addr, unsigned size);
int vfio_region_setup(Object *obj, VFIODevice *vbasedev, VFIORegion *region,
                      int index, const char *name);
int vfio_region_mmap(VFIORegion *region);
void vfio_region_mmaps_set_enabled(VFIORegion *region, bool enabled);
void vfio_region_unmap(VFIORegion *region);
void vfio_region_exit(VFIORegion *region);
void vfio_region_finalize(VFIORegion *region);
void vfio_reset_handler(void *opaque);
VFIOAddressSpace *vfio_get_address_space(AddressSpace *as);
void vfio_put_address_space(VFIOAddressSpace *space);
VFIOGroup *vfio_get_group(int groupid, AddressSpace *as, Error **errp);
void vfio_put_group(VFIOGroup *group);
struct vfio_device_info *vfio_get_device_info(int fd);
int vfio_get_device(VFIOGroup *group, const char *name,
                    VFIODevice *vbasedev, Error **errp);

VFIOContainer *vfio_new_container(VFIOAddressSpace *space);
void vfio_link_container(VFIOContainer *container, VFIOGroup *group);
void vfio_unmap_container(VFIOContainer *container);
void vfio_init_device(VFIODevice *vbasedev, VFIOGroup *group,
                      struct vfio_device_info *info);

extern const MemoryRegionOps vfio_region_ops;
typedef QLIST_HEAD(VFIOGroupList, VFIOGroup) VFIOGroupList;
extern VFIOGroupList vfio_group_list;

bool vfio_mig_active(void);
int vfio_block_multiple_devices_migration(VFIODevice *vbasedev, Error **errp);
void vfio_unblock_multiple_devices_migration(void);
bool vfio_viommu_preset(VFIODevice *vbasedev);
int64_t vfio_mig_bytes_transferred(void);
void vfio_reset_bytes_transferred(void);

#ifdef CONFIG_LINUX
int vfio_get_region_info(VFIODevice *vbasedev, int index,
                         struct vfio_region_info **info);
int vfio_get_dev_region_info(VFIODevice *vbasedev, uint32_t type,
                             uint32_t subtype, struct vfio_region_info **info);
void vfio_get_all_regions(VFIODevice *vbasedev);
bool vfio_has_region_cap(VFIODevice *vbasedev, int region, uint16_t cap_type);
struct vfio_info_cap_header *
vfio_get_region_info_cap(struct vfio_region_info *info, uint16_t id);
bool vfio_get_info_dma_avail(struct vfio_iommu_type1_info *info,
                             unsigned int *avail);
struct vfio_info_cap_header *
vfio_get_device_info_cap(struct vfio_device_info *info, uint16_t id);
#endif
extern const MemoryListener vfio_prereg_listener;

int vfio_spapr_create_window(VFIOContainer *container,
                             MemoryRegionSection *section,
                             hwaddr *pgsize);
int vfio_spapr_remove_window(VFIOContainer *container,
                             hwaddr offset_within_address_space);

bool vfio_migration_realize(VFIODevice *vbasedev, Error **errp);
void vfio_migration_exit(VFIODevice *vbasedev);

#endif /* HW_VFIO_VFIO_COMMON_H */
