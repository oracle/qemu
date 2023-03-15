%ifarch x86_64
    %global kvm_target    x86_64
%endif
%ifarch aarch64
    %global kvm_target    aarch64
%endif
%global buildarch %{kvm_target}-softmmu

# Generate documentation
%global have_docs 0

# Generate position-independent executables; note that disabling
# this makes it difficult to patch QEMU
%global have_pie 1

# Support for loadable modules
%global have_modules 1

# Debug switches
# Generate debug info
%global have_debug_info 0
# Debug the Tiny Code Generator
%global have_tcg_debug 0
# Debug casts
%global have_qom_cast_debug 0
# Enable Sparse semantic checker
%global have_sparse 0
# Mutex debugging support
%global have_debug_mutex 0

# Support for gperftools
%global have_gperftools 0

# Support for BPF
%global have_bpf 1

# Build qemu-io, qemu-nbd and qemu-img tools
%global have_tools 1

# Support for capstone disassembler
%global have_capstone 0

# Support for vnuma
%global have_numa 1

# Support curses on the HMP interface
%global have_curses 0
%global have_iconv 0

# Support for Linux AIO
%global have_linux_aio 1

# Support for Linux io_uring
%global have_have_io_uring 1

# Support Linux's vhost-net module
%global have_vhost_net 1

# Support virtio sockets for host/guest communication
%global have_vhost_vsock 1

# Support vhost-crypto acceleration
%global have_vhost_crypto 0

# Support vhost-user
%global have_vhost_user 1

# Support vhost-kernel
%global have_vhost_kernel 1

# Support vhost-user-blk-server
%global have_vhost_user_blk_server 1

# Support vhost-vdpa
%global have_vhost_vdpa 1

# Support for replication
%global have_replication 1

# Support for multiprocess
%global have_multiprocess 1

# Memory knobs
# Allocate a pool of memory for coroutines
%global have_coroutine_pool 1
# membarrier system call (for Linux 4.14+ or Windows)
%global have_membarrier 0
# pmem support (note that there's no libpmem support on aarch64)
%ifarch x86_64
%global have_libpmem 1
%else
%global have_libpmem 0
%endif

# Security and capabilities checking knobs
# libseccomp
%global have_seccomp 1
# libattr
%global have_attr 1
# libcap-ng
%global have_libcapng 1

# Support for block storage backends
# iSCSI
%global have_iscsi 1
# Ceph/RBD
%global have_rbd 1
# GlusterFS
%global have_gluster 1
# VirtFS (required for Kata Containers)
%global have_virtfs 1
# virtiofs daemon
%global have_virtiofsd 1
# SSH
%global have_ssh 1
# Curl
%global have_curl 1
# Block migration in the main migration stream
%global have_live_block_migration 1
# FUSE
%global have_fuse 1

# Support for image formats
# bochs
%global have_bochs 0
# cloop
%global have_cloop 0
# qcow1
%global have_qcow1 0
# vvfat
%global have_vvfat 0
# qed
%global have_qed 0
# Parallels
%global have_parallels 0
# MacOS DMG
%global have_dmg 0

# Support for multipath persistent reservations
%global have_mpath 0

# Support for remote graphical consoles
# VNC
%global have_vnc 1
# SASL encryption for VNC
%global have_vnc_sasl 1
# JPEG compression for VNC
%global have_vnc_jpg 0
# Spice
%global have_spice 0

# Support for compression libraries
# LZO
%global have_lzo 1
# Snappy
%global have_snappy 1
# bzip
%global have_bzip2 0
# lzfse
%global have_lzfse 0

# Support for encryption libraries
# GNU TLS
%global have_gnutls 1
# Nettle
%global have_nettle 0
# libgrypt
%global have_gcrypt 0
# Linux AF_ALG crypto backend driver
%global have_crypto_afalg 1

# Miscellaneous networking support
# RDMA (for migration only)
%global have_rdma 0
# Virtual Distributed Ethernet (VDE)
%global have_vde 0
# netmap
%global have_netmap 0

# Support for miscellaneous hardware
# Trusted Platform Modules (TPM)
%global have_tpm 1
# USB redirection and passthrough
%global have_usb 0
# SmartCards
%global have_smartcard 0
# Flat Device Trees
%global have_fdt 1
# HAX acceleration support
%global have_hax 0
# Hypervisor.framework acceleration support
%global have_hvf 0
# Windows Hypervisor Platform acceleration support
%global have_whpx 0

# Support for guest graphics APIs
# SDL/GTK
%global have_sdl_gtk 0
# OpenGL
%global have_opengl 0
# virgl
%global have_virgl 0

# Build guest agents for Linux and Windows
%global have_agent 1
%global have_windows_agent 0

# Xen is available only on i386/x86_64 (from libvirt spec)
%ifarch x86_64
%global have_xen 0
%endif

# Support for xkbcommon
%global have_xkbcommon 0

# Support for module upgrades
%global have_module_upgrades 1

# Support for slirp
%global have_slirp 1

# Support for vfio-user-server
%global have_vfio_user_server 1

# Support for vduse-blk-export
%global have_vduse_blk_export 1

# Include dependencies on EDK2 packages
%ifarch x86_64 aarch64
%global have_edk2 1
%endif

# QMP regdump tool (and sosreport plugin) is supported on x86_64 and aarch64
%ifarch x86_64 aarch64
%global have_qmpregdump 1
%endif

%global requires_all_modules                                     \
%if %{have_iscsi}                                                \
Requires: %{name}-block-iscsi = %{epoch}:%{version}-%{release}   \
%endif                                                           \
%if %{have_gluster}                                              \
Requires: %{name}-block-gluster = %{epoch}:%{version}-%{release} \
%endif                                                           \
%if %{have_rbd}                                                  \
Requires: %{name}-block-rbd = %{epoch}:%{version}-%{release}     \
%endif                                                           \
%if %{have_curl}                                                 \
Requires: %{name}-block-curl = %{epoch}:%{version}-%{release}    \
%endif                                                           \
%if %{have_ssh}                                                  \
Requires: %{name}-block-ssh = %{epoch}:%{version}-%{release}     \
%endif

Summary: QEMU is a machine emulator and virtualizer
Name: qemu-kvm
Version: 7.2.0
Release: 1%{?dist}
Epoch: 15
License: GPLv2+ and LGPLv2+ and BSD
Group: Development/Tools
URL: http://www.qemu.org/
Obsoletes: qemu-kvm-ev, qemu-img-ev, qemu-kvm-common-ev
ExclusiveArch: x86_64 aarch64

# Note that the source tarball is still called "qemu" (instead of "qemu-kvm")
# to avoid breaking the automated build system
Source0: qemu-7.2.0.tar.xz

# Creates /dev/kvm
Source3: 80-kvm.rules

%if 0%{?have_agent}
# Guest agent service
Source9: qemu-guest-agent.service
# Guest agent service environment file
Source10: qemu-ga.sysconfig
# Guest agent udev rules
Source11: 99-qemu-guest-agent.rules
%endif

# /etc/qemu/bridge.conf
Source12: bridge.conf

# /etc/modprobe.d/kvm.conf
Source20: kvm.conf
# /etc/modprobe.d/vhost.conf
Source21: vhost.conf

%if 0%{?have_qmpregdump}
# /usr/bin/qmp-regdump
Source22: qmp-regdump
# /usr/lib/<python sitelib>/sos/plugins/qemu_regdump.py
Source23: qemu_regdump.py
%endif

# Generic build dependencies
BuildRequires: zlib-devel
BuildRequires: glib2-devel
BuildRequires: which
BuildRequires: gnutls-devel
BuildRequires: cyrus-sasl-devel
BuildRequires: libaio-devel
BuildRequires: libtool
BuildRequires: pciutils-devel
BuildRequires: python3-devel
BuildRequires: texinfo
BuildRequires: perl-podlators
BuildRequires: chrpath
BuildRequires: ninja-build

# ACPI compilation on x86_64
%ifarch x86_64
BuildRequires: iasl
BuildRequires: cpp
%endif

%if 0%{?have_sdl_gtk}
# -display sdl support
BuildRequires: SDL2-devel
%endif
# qemu-pr-helper multipath support (requires libudev too)
%if 0%{?have_mpath}
BuildRequires: device-mapper-multipath-devel
%endif
BuildRequires: systemd-devel
%if 0%{?have_iscsi}
# iscsi drive support
BuildRequires: libiscsi-devel
%endif
%if 0%{?have_snappy}
# snappy compression for memory dump
BuildRequires: snappy-devel
%endif
%if 0%{?have_lzo}
# lzo compression for memory dump
BuildRequires: lzo-devel
%endif
%if 0%{?have_curses}
# needed for -display curses
BuildRequires: ncurses-devel
%endif
# used by 9pfs
%if 0%{?have_attr}
BuildRequires: libattr-devel
%endif
BuildRequires: libcap-devel
%if 0%{?have_libcapng}
# used by qemu-bridge-helper
BuildRequires: libcap-ng-devel
%endif
%if 0%{?have_spice}
# spice usb redirection support
BuildRequires: usbredir-devel >= 0.7.1
%endif
%ifnarch s390 s390x
%if 0%{?have_gperftools}
# tcmalloc support
BuildRequires: gperftools-devel
%endif
%endif
%if 0%{?have_bpf}
BuildRequires: libbpf-devel
%endif
%if 0%{?have_spice}
# spice graphics support
BuildRequires: spice-protocol >= 0.12.2
BuildRequires: spice-server-devel >= 0.12.0
%endif
%if 0%{?have_seccomp}
# seccomp containment support
BuildRequires: libseccomp-devel >= 2.4.0
%endif
%if 0%{?have_rbd}
# For rbd block driver
BuildRequires: librbd1-devel
%endif
# We need both because the 'stap' binary is probed for by configure
BuildRequires: systemtap
BuildRequires: systemtap-sdt-devel
%if 0%{?have_vnc_jpg}
# For VNC JPEG support
BuildRequires: libjpeg-devel
%endif
# For uuid generation
BuildRequires: libuuid-devel
%if 0%{?have_fdt}
# For FDT device tree support
BuildRequires: libfdt-devel
%endif
# Hard requirement for version >= 1.3
BuildRequires: pixman-devel
%if 0%{?have_gluster}
# For gluster support
BuildRequires: glusterfs-devel >= 3.4.0
BuildRequires: glusterfs-api-devel >= 3.4.0
%endif
%if 0%{?have_usb}
# Needed for USB passthrough
BuildRequires: libusbx-devel >= 1.0.22
%endif
%if 0%{?have_ssh}
# SSH block driver
BuildRequires: libssh-devel
%endif
%if 0%{?have_curl}
# For network block driver
BuildRequires: libcurl-devel
%endif
%if 0%{?have_fuse}
BuildRequires: fuse3-devel
%endif
%if 0%{?have_sdl_gtk}
# GTK frontend
BuildRequires: gtk3-devel
BuildRequires: vte291-devel
# GTK translations
BuildRequires: gettext
%endif
# RDMA migration
%if 0%{have_rdma}
BuildRequires: librdmacm-devel
%endif
%if 0%{?have_xen}
# Xen support
BuildRequires: xen-devel
%endif
%ifarch %{ix86} x86_64 aarch64
# qemu 2.1: needed for memdev hostmem backend
BuildRequires: numactl-devel
%endif
# qemu 2.3: reading bzip2 compressed dmg images
BuildRequires: bzip2-devel
%if 0%{?have_sdl_gtk}
# qemu 2.4: needed for opengl bits
BuildRequires: libepoxy-devel
%endif
# qemu 2.5: needed for TLS test suite
BuildRequires: libtasn1-devel
%if 0%{?have_smartcard}
# qemu 2.5: libcacard is it's own project now
BuildRequires: libcacard-devel >= 2.5.0
%endif
%if 0%{?have_virgl}
# qemu 2.5: virgl 3d support
BuildRequires: virglrenderer-devel
%endif
%if 0%{?have_sdl_gtk}
# qemu 2.6: Needed for gtk GL support
BuildRequires: mesa-libgbm-devel
%endif
%if 0%{?have_libpmem}
BuildRequires: libpmem-devel
%endif
%if 0%{?have_xkbcommon}
BuildRequires: libxkbcommon-devel
%endif
%if 0%{?have_virtiofsd}
BuildRequires: libcap-ng-devel
%endif
%if 0%{?have_slirp}
BuildRequires: libslirp-devel
%endif

Requires: qemu-kvm-core = %{epoch}:%{version}-%{release}

%{requires_all_modules}

%description
qemu-kvm is an open source virtualizer that provides hardware
emulation for the KVM hypervisor. qemu-kvm acts as a virtual
machine monitor together with the KVM kernel modules, and emulates the
hardware for a full system such as a PC and its associated peripherals.


%package -n qemu-kvm-core
Summary: qemu-kvm core components
Requires: kernel-uek
Requires: %{name}-common = %{epoch}:%{version}-%{release}
Requires: qemu-img = %{epoch}:%{version}-%{release}
%if 0%{?have_seccomp}
Requires: libseccomp >= 2.4.0
%endif
%ifarch x86_64
Requires: edk2-ovmf
%endif
%ifarch aarch64
Requires: edk2-aarch64
%endif
%if 0%{?have_gluster}
Requires: glusterfs-api >= 3.12.2
%endif
%if 0%{?have_usb}
Requires: libusbx >= 1.0.23
Requires: usbredir >= 0.8.0
%endif
Provides: qemu

%description -n qemu-kvm-core
qemu-kvm is an open source virtualizer that provides hardware
emulation for the KVM hypervisor. qemu-kvm acts as a virtual
machine monitor together with the KVM kernel modules, and emulates the
hardware for a full system such as a PC and its associated peripherals.


%package -n qemu-img
Summary: QEMU command line tool for manipulating disk images
Group: Development/Tools

%description -n qemu-img
This package provides a command line tool for manipulating disk images.


%package -n qemu-kvm-common
Summary: QEMU common files needed by all QEMU targets
Group: Development/Tools
Requires(post): /usr/bin/getent
Requires(post): /usr/sbin/groupadd
Requires(post): /usr/sbin/useradd
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
%ifarch x86_64
Requires: seabios-bin >= 1.10.2-1
Requires: sgabios-bin
%endif
%ifnarch aarch64
Requires: seavgabios-bin >= 1.12.0-3
Requires: ipxe-roms-qemu >= 20181214-8.git133f4c47
%endif

%description -n qemu-kvm-common
qemu-kvm is an open source virtualizer that provides hardware emulation for
the KVM hypervisor.

This package provides documentation and auxiliary programs used with qemu-kvm.


%if 0%{?have_agent}
%package -n qemu-guest-agent
Summary: QEMU guest agent
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units

%description -n qemu-guest-agent
qemu-kvm is an open source virtualizer that provides hardware emulation for
the KVM hypervisor.

This package provides an agent to run inside guests, which communicates
with the host over a virtio-serial channel named "org.qemu.guest_agent.0"

This package does not need to be installed on the host OS.
%endif


%if 0%{?have_gluster}
%package  block-gluster
Summary: QEMU Gluster block driver
Requires: %{name}-common%{?_isa} = %{epoch}:%{version}-%{release}
%description block-gluster
This package provides the additional Gluster block driver for QEMU.

Install this package if you want to access remote Gluster storage.
%endif


%if 0%{?have_iscsi}
%package  block-iscsi
Summary: QEMU iSCSI block driver
Requires: %{name}-common%{?_isa} = %{epoch}:%{version}-%{release}

%description block-iscsi
This package provides the additional iSCSI block driver for QEMU.

Install this package if you want to access iSCSI volumes.
%endif


%if 0%{?have_rbd}
%package  block-rbd
Summary: QEMU Ceph/RBD block driver
Requires: %{name}-common%{?_isa} = %{epoch}:%{version}-%{release}

%description block-rbd
This package provides the additional Ceph/RBD block driver for QEMU.

Install this package if you want to access remote Ceph volumes
using the rbd protocol.
%endif


%if 0%{?have_ssh}
%package  block-ssh
Summary: QEMU SSH block driver
Requires: %{name}-common%{?_isa} = %{epoch}:%{version}-%{release}

%description block-ssh
This package provides the additional SSH block driver for QEMU.

Install this package if you want to access remote disks using
the Secure Shell (SSH) protocol.
%endif


%if 0%{?have_curl}
%package  block-curl
Summary: QEMU CURL block driver
Requires: %{name}-common%{?_isa} = %{epoch}:%{version}-%{release}

%description block-curl
This package provides the additional CURL block driver for QEMU.

Install this package if you want to access remote disks over
http, https, ftp and other transports provided by the CURL library.
%endif


%if 0%{?have_virtiofsd}
%package -n qemu-virtiofsd
Summary: QEMU virtio-fs shared file system daemon
Provides: virtiofsd
%description -n qemu-virtiofsd
This package provides virtiofsd daemon. This program is a vhost-user backend
that implements the virtio-fs device that is used for sharing a host directory
tree with a guest.
%endif


%prep
%setup -q -n qemu-%{version}%{?rcstr}
%autopatch -p1

%global build_dir build
mkdir -p %{build_dir}

%build

%if 0%{?have_spice}
    %global spiceflag --enable-spice
%else
    %global spiceflag --disable-spice
%endif

%if 0%{?have_iscsi}
    %global iscsiflag --enable-libiscsi
%else
    %global iscsiflag --disable-libiscsi
%endif

%if 0%{?have_smartcard}
    %global smartcardflag --enable-smartcard
%else
    %global smartcardflag --disable-smartcard
%endif

%if 0%{?have_fdt}
    %global fdtflag --enable-fdt
%else
    %global fdtflag --disable-fdt
%endif

%if 0%{?have_rbd}
    %global rbdflag --enable-rbd
%else
    %global rbdflag --disable-rbd
%endif

%if 0%{?have_sdl_gtk}
    %global sdlflag --enable-sdl --enable-sdl-image --enable-virglrenderer --enable-gtk --enable-vte
%else
    %global sdlflag --disable-sdl --disable-sdl-image --disable-virglrenderer --disable-gtk --disable-vte
%endif

%if 0%{?have_agent}
    %global guestflags --enable-guest-agent
%else
    %global guestflags --disable-guest-agent
%endif

%if 0%{?have_windows_agent}
    %global windowsguestflags --enable-guest-agent-msi
%else
    %global windowsguestflags --disable-guest-agent-msi
%endif

%if 0%{?have_tpm}
    %global tpmflags --enable-tpm
%else
    %global tpmflags --disable-tpm
%endif

%if 0%{?have_docs}
    %global docsflags --enable-docs
%else
    %global docsflags --disable-docs
%endif

%if 0%{?have_pie}
    %global pieflags --enable-pie
%else
    %global pieflags --disable-pie
%endif

%if 0%{?have_modules}
    %global moduleflags --enable-modules
%else
    %global moduleflags --disable-modules
%endif

%if 0%{?have_tcg_debug}
    %global tcgdebugflags --enable-debug-tcg
%else
    %global tcgdebugflags --disable-debug-tcg
%endif

%if 0%{?have_debug_info}
    %global debuginfoflags --enable-debug-info
%else
    %global debuginfoflags --disable-debug-info
%endif

%if 0%{?have_sparse}
    %global sparseflags --enable-sparse
%else
    %global sparseflags --disable-sparse
%endif

%if 0%{?have_gnutls}
    %global gnutlsflags --enable-gnutls
%else
    %global gnutlsflags --disable-gnutls
%endif

%if 0%{?have_nettle}
    %global nettleflags --enable-nettle
%else
    %global nettleflags --disable-nettle
%endif

%if 0%{?have_gcrypt}
    %global gcryptflags --enable-gcrypt
%else
    %global gcryptflags --disable-gcrypt
%endif

%if 0%{?have_curses}
    %global cursesflags --enable-curses
%else
    %global cursesflags --disable-curses
%endif

%if 0%{have_iconv}
    %global iconvflags --enable-iconv
%else
    %global iconvflags --disable-iconv
%endif

%if 0%{?have_vnc}
    %global vncflags --enable-vnc
%else
    %global vncflags --disable-vnc
%endif

%if 0%{?have_vnc_sasl}
    %global vncsaslflags --enable-vnc-sasl
%else
    %global vncsaslflags --disable-vnc-sasl
%endif

%if 0%{?have_vnc_jpg}
    %global vncjpgflags --enable-vnc-jpeg
%else
    %global vncjpgflags --disable-vnc-jpeg
%endif

%if 0%{?have_virtfs}
    %global virtfsflags --enable-virtfs
%else
    %global virtfsflags --disable-virtfs
%endif

%if 0%{?have_virtiofsd}
    %global virtiofsdflags --enable-virtiofsd
%else
    %global virtiofsdflags --disable-virtiofsd
%endif

%if 0%{?have_xen}
    %global xenflags --enable-xen --enable-xen-pci-passthrough
%else
    %global xenflags --disable-xen --disable-xen-pci-passthrough
%endif

%if 0%{?have_rdma}
    %global rdmaflags --enable-rdma --enable-pvrdma
%else
    %global rdmaflags --disable-rdma --disable-pvrdma
%endif

%if 0%{?have_vde}
    %global vdeflags --enable-vde
%else
    %global vdeflags --disable-vde
%endif

%if 0%{?have_netmap}
    %global netmapflags --enable-netmap
%else
    %global netmapflags --disable-netmap
%endif

%if 0%{?have_linux_aio}
    %global linuxaioflags --enable-linux-aio
%else
    %global linuxaioflags --disable-linux-aio
%endif

%if 0%{?have_linux_io_uring}
    %global linuxiouringflags --enable-linux-io-uring
%else
    %global linuxiouringflags --disable-linux-io-uring
%endif

%if 0%{?have_libcapng}
    %global libcapngflags --enable-cap-ng
%else
    %global libcapngflags --disable-cap-ng
%endif

%if 0%{?have_attr}
    %global attrflags --enable-attr
%else
    %global attrflags --disable-attr
%endif

%if 0%{?have_vhost_net}
    %global vhostnetflags --enable-vhost-net
%else
    %global vhostnetflags --disable-vhost-net
%endif

%if 0%{?have_usb}
    %global usbflags --enable-libusb --enable-usb-redir
%else
    %global usbflags --disable-libusb --disable-usb-redir
%endif

%if 0%{?have_lzo}
    %global lzoflags --enable-lzo
%else
    %global lzoflags --disable-lzo
%endif

%if 0%{?have_snappy}
    %global snappyflags --enable-snappy
%else
    %global snappyflags --disable-snappy
%endif

%if 0%{?have_bzip2}
    %global bzip2flags --enable-bzip2
%else
    %global bzip2flags --disable-bzip2
%endif

%if 0%{?have_lzfse}
    %global lzfseflags --enable-lzfse
%else
    %global lzfseflags --disable-lzfse
%endif

%if 0%{?have_seccomp}
    %global seccompflags --enable-seccomp
%else
    %global seccompflags --disable-seccomp
%endif

%if 0%{?have_coroutine_pool}
    %global coroutineflags --enable-coroutine-pool
%else
    %global coroutineflags --disable-coroutine-pool
%endif

%if 0%{?have_gluster}
    %global glusterflags --enable-glusterfs
%else
    %global glusterflags --disable-glusterfs
%endif

%if 0%{?have_ssh}
    %global sshflags --enable-libssh
%else
    %global sshflags --disable-libssh
%endif

%if 0%{?have_curl}
    %global curlflags --enable-curl
%else
    %global curlflags --disable-curl
%endif

%if 0%{?have_fuse}
    %global fuseflags --enable-fuse
%else
    %global fuseflags --disable-fuse
%endif

%if 0%{?have_numa}
    %global numaflags --enable-numa
%else
    %global numaflags --disable-numa
%endif

%if 0%{?have_replication}
    %global replicationflags --enable-replication
%else
    %global replicationflags --disable-replication
%endif

%if 0%{?have_opengl}
    %global openglflags --enable-opengl
%else
    %global openglflags --disable-opengl
%endif

%if 0%{?have_virgl}
    %global virglflags --enable-virglrenderer
%else
    %global virglflags --disable-virglrenderer
%endif

%if 0%{?have_multiprocess}
    %global multiprocessflags --enable-multiprocess
%else
    %global multiprocessflags --disable-multiprocess
%endif

%if 0%{?have_mpath}
    %global mpathflags --enable-mpath
%else
    %global mpathflags --disable-mpath
%endif

%if 0%{?have_capstone}
    %global capstoneflags --enable-capstone
%else
    %global capstoneflags --disable-capstone
%endif

%if 0%{?have_qom_cast_debug}
    %global qomcastflags --enable-qom-cast-debug
%else
    %global qomcastflags --disable-qom-cast-debug
%endif

%if 0%{?have_membarrier}
    %global membarrierflags --enable-membarrier
%else
    %global membarrierflags --disable-membarrier
%endif

%if 0%{?have_libpmem}
    %global libpmemflags --enable-libpmem
%else
    %global libpmemflags --disable-libpmem
%endif

%if 0%{?have_hax}
    %global haxflags --enable-hax
%else
    %global haxflags --disable-hax
%endif

%if 0%{?have_hvf}
    %global hvfflags --enable-hvf
%else
    %global hvfflags --disable-hvf
%endif

%if 0%{?have_whpx}
    %global whpxflags --enable-whpx
%else
    %global whpxflags --disable-whpx
%endif

%if 0%{?have_vhost_crypto}
    %global vhostcyptoflags --enable-vhost-crypto
%else
    %global vhostcyptoflags --disable-vhost-crypto
%endif

%if 0%{?have_live_block_migration}
    %global liveblockmigrationflags --enable-live-block-migration
%else
    %global liveblockmigrationflags --disable-live-block-migration
%endif

%if 0%{have_bochs}
    %global bochsflags --enable-bochs
%else
    %global bochsflags --disable-bochs
%endif

%if 0%{have_cloop}
    %global cloopflags --enable-cloop
%else
    %global cloopflags --disable-cloop
%endif

%if 0%{have_qcow1}
    %global qcow1flags --enable-qcow1
%else
    %global qcow1flags --disable-qcow1
%endif

%if 0%{have_vvfat}
    %global vvfatflags --enable-vvfat
%else
    %global vvfatflags --disable-vvfat
%endif

%if 0%{have_qed}
    %global qedflags --enable-qed
%else
    %global qedflags --disable-qed
%endif

%if 0%{have_parallels}
    %global parallelsflags --enable-parallels
%else
    %global parallelsflags --disable-parallels
%endif

%if 0%{have_dmg}
    %global dmgflags --enable-dmg
%else
    %global dmgflags --disable-dmg
%endif

%if 0%{?have_bpf}
    %global bpfflags --enable-bpf
%else
    %global bpfflags --disable-bpf
%endif

%if 0%{?have_tools}
    %global toolsflags --enable-tools
%else
    %global toolsflags --disable-tools
%endif

%if 0%{?have_crypto_afalg}
    %global cryptoafalgflags --enable-crypto-afalg
%else
    %global cryptoafalgflags --disable-crypto-afalg
%endif

%if 0%{?have_vhost_user}
    %global vhostuserflags --enable-vhost-user
%else
    %global vhostuserflags --disable-vhost-user
%endif

%if 0%{?have_vhost_kernel}
    %global vhostkernelflags --enable-vhost-kernel
%else
    %global vhostkernelflags --disable-vhost-kernel
%endif

%if 0%{?have_vhost_user_blk_server}
    %global vhostuserblkserverflags --enable-vhost-user-blk-server
%else
    %global vhostuserblkserverflags --disable-vhost-user-blk-server
%endif

%if 0%{?have_vhost_vdpa}
    %global vhostvdpaflags --enable-vhost-vdpa
%else
    %global vhostvdpaflags --disable-vhost-vdpa
%endif

%if 0%{?have_debug_mutex}
    %global debugmutexflags --enable-debug-mutex
%else
    %global debugmutexflags --disable-debug-mutex
%endif

%if 0%{?have_xkbcommon}
   %global xkbcommonflags --enable-xkbcommon
%else
   %global xkbcommonflags --disable-xkbcommon
%endif

%if 0%{?have_module_upgrades}
    %global moduleupgradeflags --enable-module-upgrades
%else
    %global moduleupgradeflags --disable-module-upgrades
%endif

%if 0%{?have_slirp}
    %global slirpflags --enable-slirp
%else
    %global slirpflags --disable-slirp
%endif

%if 0%{?have_vfio_user_server}
    %global vfiouserserverflags --enable-vfio-user-server
%else
    %global vfiouserserfverflags --disable-vfio-user-server
%endif

%if 0%{?have_vduse_blk_export}
    %global vduseblkexportflags --enable-vduse-blk-export
%else
    %global vduseblkexportflags --disable-vduse-blk-export
%endif

%global block_drivers_rw_list qcow2,raw,file,host_device,nbd,blkdebug,luks,null-co,nvme,copy-on-read,throttle
%global block_drivers_ro_list vmdk,vhdx,vpc,https,ssh

%if 0%{?have_gluster}
    %global block_drivers_rw_list %{block_drivers_rw_list},gluster
%endif
%if 0%{?have_iscsi}
    %global block_drivers_rw_list %{block_drivers_rw_list},iscsi
%endif
%if 0%{?have_rbd}
    %global block_drivers_rw_list %{block_drivers_rw_list},rbd
%endif
%if 0%{?have_vxhs}
    %global block_drivers_rw_list %{block_drivers_rw_list},vxhs
%endif
%if 0%{?have_ssh}
    %global block_drivers_rw_list %{block_drivers_rw_list},ssh
%endif
%if 0%{?have_curl}
    %global block_drivers_rw_list %{block_drivers_rw_list},curl
%endif

pushd %{build_dir}

../configure \
    --prefix=%{_prefix} \
    --libdir=%{_libdir} \
    --sysconfdir=%{_sysconfdir} \
    --interp-prefix=%{_prefix}/qemu-%%M \
    --localstatedir=%{_localstatedir} \
    --docdir="%{qemudocdir}" \
    --libexecdir=%{_libexecdir} \
    --with-pkgversion=%{name}-%{version}-%{release} \
    --with-suffix="%{name}" \
    --firmwarepath=%{_prefix}/share/qemu-firmware \
    --extra-ldflags="%{build_ldflags}" \
    --extra-cflags="%{optflags}" \
    --meson=git \
    --target-list="%{buildarch}" \
    --with-coroutine=ucontext \
    --block-drv-rw-whitelist=%{block_drivers_rw_list} \
    --block-drv-ro-whitelist=%{block_drivers_ro_list} \
    --tls-priority=@QEMU,SYSTEM \
    --disable-strip \
    --enable-kvm \
    --enable-trace-backend=dtrace \
    --disable-user \
    --disable-linux-user \
    --disable-bsd-user \
    --disable-libnfs \
    --disable-brlapi \
    --audio-drv-list="" \
    %{spiceflag} \
    %{iscsiflag} \
    %{smartcardflag} \
    %{fdtflag} \
    %{rbdflag} \
    %{sdlflag} \
    %{guestflags} \
    %{windowsguestflags} \
    %{tpmflags} \
    %{docsflags} \
    %{pieflags} \
    %{moduleflags} \
    %{tcgdebugflags} \
    %{debuginfoflags} \
    %{bpfflags} \
    %{sparseflags} \
    %{gnutlsflags} \
    %{nettleflags} \
    %{gcryptflags} \
    %{cursesflags} \
    %{iconvflags} \
    %{vncflags} \
    %{vncsaslflags} \
    %{vncjpgflags} \
    %{virtfsflags} \
    %{virtiofsdflags} \
    %{xenflags} \
    %{rdmaflags} \
    %{vdeflags} \
    %{netmapflags} \
    %{linuxaioflags} \
    %{linuxiouringflags} \
    %{libcapngflags} \
    %{attrflags} \
    %{vhostnetflags} \
    %{usbflags} \
    %{lzoflags} \
    %{snappyflags} \
    %{bzip2flags} \
    %{lzfseflags} \
    %{seccompflags} \
    %{coroutineflags} \
    %{glusterflags} \
    %{sshflags} \
    %{curlflags} \
    %{fuseflags} \
    %{numaflags} \
    %{replicationflags} \
    %{openglflags} \
    %{virglflags} \
    %{qomcastflags} \
    %{mpathflags} \
    %{capstoneflags} \
    %{membarrierflags} \
    %{libpmemflags} \
    %{haxflags} \
    %{hvfflags} \
    %{whpxflags} \
    %{vhostcyptoflags} \
    %{liveblockmigrationflags} \
    %{bochsflags} \
    %{cloopflags} \
    %{qcow1flags} \
    %{vvfatflags} \
    %{qedflags} \
    %{parallelsflags} \
    %{dmgflags} \
    %{toolsflags} \
    %{cryptoafalgflags} \
    %{vhostuserflags} \
    %{vhostkernelflags} \
    %{vhostuserblkserverflags} \
    %{vhostvdpaflags} \
    %{debugmutexflags} \
    %{xkbcommonflags} \
    %{multiprocessflags} \
    %{moduleupgradeflags} \
    %{slirpflags} \
    %{vfiouserserfverflags} \
    %{vduseblkexportflags}

%make_build

# Generate trace backend files
%{__python3} scripts/tracetool.py --backend dtrace --format stap \
  --group=all --binary %{_libexecdir}/qemu-kvm --probe-prefix qemu.kvm \
  trace/trace-events-all qemu-kvm.stp

%{__python3} scripts/tracetool.py --backends=dtrace --format=log-stap \
  --group=all --binary %{_libexecdir}/qemu-kvm --probe-prefix qemu.kvm \
  trace/trace-events-all qemu-kvm-log.stp

%{__python3} scripts/tracetool.py --backend dtrace --format simpletrace-stap \
  --group=all --binary %{_libexecdir}/qemu-kvm --probe-prefix qemu.kvm \
  trace/trace-events-all qemu-kvm-simpletrace.stp

# Ugly Red Hat creation that results in packaging the QEMU executable as
# /usr/libexec/qemu-kvm instead of upstream's /usr/bin/qemu-system-<arch>
cp -a %{kvm_target}-softmmu/qemu-system-%{kvm_target} qemu-kvm

popd


%install

%if 0%{?have_agent}
# Install qemu-guest-agent service and udev rules
install -D -m 0644 %{_sourcedir}/qemu-guest-agent.service %{buildroot}%{_unitdir}/qemu-guest-agent.service
install -D -m 0644 %{_sourcedir}/qemu-ga.sysconfig %{buildroot}%{_sysconfdir}/sysconfig/qemu-ga
install -D -m 0644 %{_sourcedir}/99-qemu-guest-agent.rules %{buildroot}%{_udevrulesdir}/99-qemu-guest-agent.rules

# Install the fsfreeze hook scripts
mkdir -p %{buildroot}%{_sysconfdir}/qemu-ga/fsfreeze-hook.d
install -p scripts/qemu-guest-agent/fsfreeze-hook %{buildroot}%{_sysconfdir}/qemu-ga/fsfreeze-hook
mkdir -p %{buildroot}%{_datadir}/%{name}/qemu-ga/fsfreeze-hook.d/
install -p -m 0644 scripts/qemu-guest-agent/fsfreeze-hook.d/*.sample %{buildroot}%{_datadir}/%{name}/qemu-ga/fsfreeze-hook.d/

# Create the log directory
mkdir -p -v %{buildroot}%{_localstatedir}/log/qemu-ga/

# Install the qemu-ga binary
pushd %{build_dir}
install -D -p -m 0755 qga/qemu-ga %{buildroot}%{_bindir}/qemu-ga
popd
%endif


install -D -p -m 0644 %{_sourcedir}/vhost.conf %{buildroot}%{_sysconfdir}/modprobe.d/vhost.conf
%ifarch x86_64
    install -D -p -m 0644 %{_sourcedir}/kvm.conf %{buildroot}%{_sysconfdir}/modprobe.d/kvm.conf
%endif

mkdir -p %{buildroot}%{_bindir}/
mkdir -p %{buildroot}%{_udevrulesdir}/
mkdir -p %{buildroot}%{_datadir}/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/%{name}

install -m 0644 %{_sourcedir}/80-kvm.rules %{buildroot}%{_udevrulesdir}/80-kvm.rules

pushd %{build_dir}
%make_install
popd


mkdir -p %{buildroot}%{_datadir}/systemtap/tapset

mkdir -p %{buildroot}%{_datadir}/qemu

%if 0%{?have_vhost_user}
# Move vhost-user JSON files to the standard "qemu" directory
mv %{buildroot}%{_datadir}/%{name}/vhost-user %{buildroot}%{_datadir}/qemu/
%endif

install -m 0755 %{build_dir}/%{kvm_target}-softmmu/qemu-system-%{kvm_target} %{buildroot}%{_libexecdir}/qemu-kvm
install -m 0644 %{build_dir}/qemu-kvm.stp %{buildroot}%{_datadir}/systemtap/tapset/
install -m 0644 %{build_dir}/qemu-kvm-log.stp %{buildroot}%{_datadir}/systemtap/tapset/
install -m 0644 %{build_dir}/qemu-kvm-simpletrace.stp %{buildroot}%{_datadir}/systemtap/tapset/

rm %{buildroot}%{_bindir}/qemu-system-%{kvm_target}
rm %{buildroot}%{_datadir}/systemtap/tapset/qemu-system-%{kvm_target}.stp
rm %{buildroot}%{_datadir}/systemtap/tapset/qemu-system-%{kvm_target}-simpletrace.stp
rm %{buildroot}%{_datadir}/systemtap/tapset/qemu-system-%{kvm_target}-log.stp
rm %{buildroot}%{_datadir}/applications/qemu.desktop
rm %{buildroot}%{_bindir}/elf2dmp

# Install simpletrace
install -m 0755 scripts/simpletrace.py %{buildroot}%{_datadir}/%{name}/simpletrace.py
mkdir -p %{buildroot}%{_datadir}/%{name}/tracetool
install -m 0644 -t %{buildroot}%{_datadir}/%{name}/tracetool scripts/tracetool/*.py
mkdir -p %{buildroot}%{_datadir}/%{name}/tracetool/backend
install -m 0644 -t %{buildroot}%{_datadir}/%{name}/tracetool/backend scripts/tracetool/backend/*.py
mkdir -p %{buildroot}%{_datadir}/%{name}/tracetool/format
install -m 0644 -t %{buildroot}%{_datadir}/%{name}/tracetool/format scripts/tracetool/format/*.py

%if 0%{?have_docs}
mkdir -p %{buildroot}%{qemudocdir}
install -p -m 0644 -t %{buildroot}%{qemudocdir} Changelog README COPYING COPYING.LIB LICENSE docs/interop/qmp-spec.txt
chmod -x %{buildroot}%{_mandir}/man1/*
chmod -x %{buildroot}%{_mandir}/man8/*
%endif

install -D -p -m 0644 qemu.sasl %{buildroot}%{_sysconfdir}/sasl2/%{name}.conf

# Provided by package openbios
rm -rf %{buildroot}%{_datadir}/%{name}/openbios-ppc
rm -rf %{buildroot}%{_datadir}/%{name}/openbios-sparc32
rm -rf %{buildroot}%{_datadir}/%{name}/openbios-sparc64
# Provided by package SLOF
rm -rf %{buildroot}%{_datadir}/%{name}/slof.bin
# Provided by package ipxe-roms-qemu
rm -rf %{buildroot}%{_datadir}/%{name}/pxe*rom
# Provided by package seavgabios
rm -rf %{buildroot}%{_datadir}/%{name}/vgabios*bin
# Provided by package seabios-bin
rm -rf %{buildroot}%{_datadir}/%{name}/bios.bin
rm -rf %{buildroot}%{_datadir}/%{name}/bios-256k.bin
# Provided by package sgabios
rm -rf %{buildroot}%{_datadir}/%{name}/sgabios.bin
# Provided by the OVMF and/or AAVMF packages
rm -rf %{buildroot}%{_datadir}/%{name}/edk2*
rm -rf %{buildroot}%{_datadir}/%{name}/firmware
# We don't package RISC-V
rm -rf %{buildroot}%{_datadir}/%{name}/opensbi-riscv*
# We don't package UI elements
rm -rf %{buildroot}%{_datadir}/applications
rm -rf %{buildroot}%{_datadir}/icons
rm -rf %{buildroot}%{_datadir}/%{name}/qemu-nsis.bmp
# We don't package the setuid root qemu-bridge-helper script
rm -rf %{buildroot}%{_libexecdir}/qemu-bridge-helper
# We don't package elf2dmp
rm -rf %{buildroot}%{_bindir}/elf2dmp
# We don't package virtfs-proxy-helper
rm -rf %{buildroot}%{_libexecdir}/virtfs-proxy-helper
rm -rf %{buildroot}%{_mandir}/man1/virtfs-proxy-helper*
# We don't package hw-s390x-virtio* stuff
rm -rf %{buildroot}/usr/lib64/qemu-kvm/hw-s390x-virtio-*
rm -rf %{buildroot}/usr/lib/debug/usr/lib64/qemu-kvm/hw-s390x-virtio-*
# We don't package the QEMU plugin header file
rm -rf %{buildroot}/usr/include/qemu-plugin.h
# We don't package the oss audio library that shouldn't
# have been build in the first place
rm -rf %{buildroot}/usr/lib64/qemu-kvm/audio-oss.so
rm -rf %{buildroot}/usr/lib/debug/usr/lib64/qemu-kvm/audio-oss.so*

unused_blobs="QEMU,cgthree.bin QEMU,tcx.bin bamboo.dtb palcode-clipper \
petalogix-ml605.dtb petalogix-s3adsp1800.dtb ppc_rom.bin \
s390-ccw.img s390-zipl.rom spapr-rtas.bin u-boot.e500 \
skiboot.lid qemu_vga.ndrv s390-netboot.img canyonlands.dtb \
hppa-firmware.img u-boot-sam460-20100605.bin qboot.rom \
npcm7xx_bootrom.bin vof-nvram.bin vof.bin"
for blob in $unused_blobs; do
   rm -rf %{buildroot}%{_datadir}/%{name}/$blob
done

rm -rf %{buildroot}%{_bindir}/qemu-edid
rm -rf %{buildroot}%{_bindir}/qemu-keymap
rm -rf %{buildroot}%{_bindir}/qemu-trace-stap

# Remove ivshmem example programs
rm -rf %{buildroot}%{_bindir}/ivshmem-client
rm -rf %{buildroot}%{_bindir}/ivshmem-server

# Remove unused ROM images
%ifarch aarch64
rm -rf %{buildroot}%{_datadir}/%{name}/efi-e1000.rom
rm -rf %{buildroot}%{_datadir}/%{name}/efi-e1000e.rom
rm -rf %{buildroot}%{_datadir}/%{name}/efi-eepro100.rom
rm -rf %{buildroot}%{_datadir}/%{name}/efi-ne2k_pci.rom
rm -rf %{buildroot}%{_datadir}/%{name}/efi-pcnet.rom
rm -rf %{buildroot}%{_datadir}/%{name}/efi-rtl8139.rom
rm -rf %{buildroot}%{_datadir}/%{name}/efi-virtio.rom
rm -rf %{buildroot}%{_datadir}/%{name}/efi-vmxnet3.rom
rm -rf %{buildroot}%{_datadir}/%{name}/kvmvapic.bin
rm -rf %{buildroot}%{_datadir}/%{name}/linuxboot.bin
rm -rf %{buildroot}%{_datadir}/%{name}/linuxboot_dma.bin
rm -rf %{buildroot}%{_datadir}/%{name}/multiboot.bin
rm -rf %{buildroot}%{_datadir}/%{name}/pvh.bin
rm -rf %{buildroot}%{_datadir}/%{name}/bios-microvm.bin
%endif
rm -rf %{buildroot}%{_datadir}/%{name}/multiboot_dma.bin

pxe_link() {
	ln -s ../ipxe/$2.rom %{buildroot}%{_datadir}/%{name}/pxe-$1.rom
}

%ifarch x86_64
pxe_link e1000 8086100e
pxe_link ne2k_pci 10ec8029
pxe_link pcnet 10222000
pxe_link rtl8139 10ec8139
pxe_link virtio 1af41000
pxe_link eepro100 80861209
pxe_link e1000e 808610d3
pxe_link vmxnet3 15ad07b0
%endif

rom_link() {
    ln -s $1 %{buildroot}%{_datadir}/%{name}/$2
}

%ifarch x86_64
rom_link ../seavgabios/vgabios-isavga.bin vgabios.bin
rom_link ../seavgabios/vgabios-cirrus.bin vgabios-cirrus.bin
rom_link ../seavgabios/vgabios-qxl.bin vgabios-qxl.bin
rom_link ../seavgabios/vgabios-stdvga.bin vgabios-stdvga.bin
rom_link ../seavgabios/vgabios-vmware.bin vgabios-vmware.bin
rom_link ../seavgabios/vgabios-virtio.bin vgabios-virtio.bin
rom_link ../seabios/bios.bin bios.bin
rom_link ../seabios/bios-256k.bin bios-256k.bin
rom_link ../sgabios/sgabios.bin sgabios.bin
%endif

# Install rules to use the bridge helper with libvirt's virbr0
install -m 0644 %{_sourcedir}/bridge.conf %{buildroot}%{_sysconfdir}/%{name}/bridge.conf

%if 0%{?have_qmpregdump}
# Install in /usr/bin
install -m 0755 %{_sourcedir}/qmp-regdump %{buildroot}%{_bindir}/
# Install in /usr/lib/<python sitelib>/sos/plugins/
mkdir -p %{buildroot}%{python3_sitelib}/sos/plugins
install -m 0755 %{_sourcedir}/qemu_regdump.py %{buildroot}%{python3_sitelib}/sos/plugins
%endif

# We need to make the block device modules executable else
# RPM won't pick up their dependencies.
chmod +x %{buildroot}%{_libdir}/qemu-kvm/block-*.so


%check


%post -n qemu-kvm-core
udevadm control --reload >/dev/null 2>&1 || :
udevadm trigger --subsystem-match=misc --sysname-match=kvm --action=add || :
chmod --quiet 666 /dev/kvm || :

%post -n qemu-kvm-common
getent group kvm >/dev/null || groupadd -g 36 -r kvm
getent group qemu >/dev/null || groupadd -g 107 -r qemu
getent passwd qemu >/dev/null || \
  useradd -r -u 107 -g qemu -G kvm -d / -s /sbin/nologin \
    -c "qemu user" qemu

%global qemu_kvm_files \
%{_libexecdir}/qemu-kvm \
%{_datadir}/systemtap/tapset/qemu-kvm.stp \
%{_datadir}/%{name}/trace-events-all \
%{_datadir}/systemtap/tapset/qemu-kvm-simpletrace.stp \
%{_datadir}/systemtap/tapset/qemu-kvm-log.stp

%files
# Deliberately empty

%if 0%{?have_sdl_gtk}
%files qemu-kvm-common -f %{name}.lang
%else
%files -n qemu-kvm-common
%endif
%if 0%{?have_docs}
%dir %{qemudocdir}
%doc %{qemudocdir}/Changelog
%doc %{qemudocdir}/COPYING
%doc %{qemudocdir}/COPYING.LIB
%doc %{qemudocdir}/LICENSE
%doc %{qemudocdir}/qemu-doc.html
%doc %{qemudocdir}/qemu-doc.txt
%doc %{qemudocdir}/qemu-ga-ref.html
%doc %{qemudocdir}/qemu-ga-ref.txt
%doc %{qemudocdir}/qemu-qmp-ref.html
%doc %{qemudocdir}/qemu-qmp-ref.txt
%doc %{qemudocdir}/README
%{_mandir}/man1/qemu.1*
%{_mandir}/man7/qemu-ga-ref.7*
%{_mandir}/man7/qemu-qmp-ref.7*
%endif
%dir %{_datadir}/%{name}/
%{_datadir}/%{name}/keymaps/
%{_bindir}/qemu-pr-helper
%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/bridge.conf
%ifarch x86_64
%config(noreplace) %{_sysconfdir}/modprobe.d/kvm.conf
%endif
%config(noreplace) %{_sysconfdir}/modprobe.d/vhost.conf
%config(noreplace) %{_sysconfdir}/sasl2/%{name}.conf
%{_datadir}/%{name}/simpletrace.py*
%{_datadir}/%{name}/tracetool/*.py*
%{_datadir}/%{name}/tracetool/backend/*.py*
%{_datadir}/%{name}/tracetool/format/*.py*
%if 0%{?have_qmpregdump}
%config(noreplace) %{_bindir}/qmp-regdump
%config(noreplace) %{python3_sitelib}/sos/plugins/qemu_regdump.py*
%config(noreplace) %{python3_sitelib}/sos/plugins/__pycache__/*.pyc
%endif

%files -n qemu-kvm-core
%defattr(-,root,root)
%ifarch x86_64
    %{_datadir}/%{name}/bios.bin
    %{_datadir}/%{name}/bios-256k.bin
    %{_datadir}/%{name}/linuxboot.bin
    %{_datadir}/%{name}/linuxboot_dma.bin
    %{_datadir}/%{name}/multiboot.bin
    %{_datadir}/%{name}/kvmvapic.bin
    %{_datadir}/%{name}/sgabios.bin
    %{_datadir}/%{name}/pvh.bin
    %{_datadir}/%{name}/bios-microvm.bin
    %{_datadir}/%{name}/vgabios.bin
    %{_datadir}/%{name}/vgabios-cirrus.bin
    %{_datadir}/%{name}/vgabios-qxl.bin
    %{_datadir}/%{name}/vgabios-stdvga.bin
    %{_datadir}/%{name}/vgabios-vmware.bin
    %{_datadir}/%{name}/vgabios-virtio.bin
    %{_datadir}/%{name}/pxe-e1000.rom
    %{_datadir}/%{name}/efi-e1000.rom
    %{_datadir}/%{name}/pxe-e1000e.rom
    %{_datadir}/%{name}/efi-e1000e.rom
    %{_datadir}/%{name}/pxe-eepro100.rom
    %{_datadir}/%{name}/efi-eepro100.rom
    %{_datadir}/%{name}/pxe-ne2k_pci.rom
    %{_datadir}/%{name}/efi-ne2k_pci.rom
    %{_datadir}/%{name}/pxe-pcnet.rom
    %{_datadir}/%{name}/efi-pcnet.rom
    %{_datadir}/%{name}/pxe-rtl8139.rom
    %{_datadir}/%{name}/efi-rtl8139.rom
    %{_datadir}/%{name}/pxe-virtio.rom
    %{_datadir}/%{name}/efi-virtio.rom
    %{_datadir}/%{name}/pxe-vmxnet3.rom
    %{_datadir}/%{name}/efi-vmxnet3.rom
%endif
%{_udevrulesdir}/80-kvm.rules
%{_libdir}/%{name}/accel-qtest-%{kvm_target}.so
%ifarch x86_64
%{_libdir}/%{name}/accel-tcg-%{kvm_target}.so
%endif
%{_libdir}/%{name}/hw-display-virtio-gpu-gl.so
%{_libdir}/%{name}/hw-display-virtio-gpu-pci-gl.so
%{_libdir}/%{name}/hw-display-virtio-gpu-pci.so
%{_libdir}/%{name}/hw-display-virtio-gpu.so
%ifarch x86_64
%{_libdir}/%{name}/hw-display-virtio-vga-gl.so
%{_libdir}/%{name}/hw-display-virtio-vga.so
%endif
%{?qemu_kvm_files:}


%files -n qemu-img
%defattr(-,root,root)
%{_bindir}/qemu-img
%{_bindir}/qemu-io
%{_bindir}/qemu-nbd
%{_bindir}/qemu-storage-daemon
%if 0%{?have_docs}
%{_mandir}/man1/qemu-img.1*
%{_mandir}/man8/qemu-nbd.8*
%endif


%if 0%{?have_agent}
%files -n qemu-guest-agent
%defattr(-,root,root,-)
%{_bindir}/qemu-ga
%if 0%{?have_docs}
%{_mandir}/man8/qemu-ga.8*
%endif
%{_unitdir}/qemu-guest-agent.service
%{_udevrulesdir}/99-qemu-guest-agent.rules
%config(noreplace) %{_sysconfdir}/sysconfig/qemu-ga
%{_sysconfdir}/qemu-ga
%{_datadir}/%{name}/qemu-ga
%dir %{_localstatedir}/log/qemu-ga
%endif


%if 0%{?have_gluster}
%files block-gluster
%{_libdir}/qemu-kvm/block-gluster.so
%endif


%if 0%{?have_iscsi}
%files block-iscsi
%{_libdir}/qemu-kvm/block-iscsi.so
%endif


%if 0%{?have_rbd}
%files block-rbd
%{_libdir}/qemu-kvm/block-rbd.so
%endif


%if 0%{?have_ssh}
%files block-ssh
%{_libdir}/qemu-kvm/block-ssh.so
%endif


%if 0%{?have_curl}
%files block-curl
%{_libdir}/qemu-kvm/block-curl.so
%endif


%if 0%{?have_virtiofsd}
%files -n qemu-virtiofsd
%if 0%{?have_docs}
%{_mandir}/man1/virtiofsd.1*
%endif
%{_libexecdir}/virtiofsd
# This is the standard location for vhost-user JSON files defined in the
# vhost-user specification for interoperability with other software. Unlike
# most other paths we use it's "qemu" instead of "qemu-kvm".
%{_datadir}/qemu/vhost-user/50-qemu-virtiofsd.json
%endif


%changelog
* Mon Apr 10 2023 Mark Kanda <mark.kanda@oracle.com>
- oslib-posix: fix uninitialized var in wait_mem_prealloc() (Mark Kanda)

* Mon Jan 30 2023 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-1-el8
- vl: Add an -action option to override MCE handling (Mark Kanda)
- hw/arm/virt: build SMBIOS 19 table (Mihai Carabas)
- virtio-net-pci: Don't use "efi-virtio.rom" on AArch64 (Mark Kanda)
- migration: increase listening socket backlog (Elena Ufimtseva)
- virtio: Set PCI subsystem vendor ID to Oracle (Karl Heubaum)
- Update to QEMU 7.2.0 (Karl Heubaum)

* Tue Sep 13 2022 Karl Heubaum <karl.heubaum@oracle.com> - 6.1.1-4-el8
- display/qxl-render: fix race condition in qxl_cursor (CVE-2021-4207) (Mauro Matteo Cascella) [Orabug: 34591445] {CVE-2021-4207}
- ui/cursor: fix integer overflow in cursor_alloc (CVE-2021-4206) (Mauro Matteo Cascella) [Orabug: 34591281] {CVE-2021-4206}
- scsi/lsi53c895a: really fix use-after-free in lsi_do_msgout (CVE-2022-0216) (Mauro Matteo Cascella) [Orabug: 34590706] {CVE-2022-0216}
- scsi/lsi53c895a: fix use-after-free in lsi_do_msgout (CVE-2022-0216) (Mauro Matteo Cascella) [Orabug: 34590706] {CVE-2022-0216}
- tests/qtest: Add fuzz-lsi53c895a-test (Philippe Mathieu-Daude) [Orabug: 34590706] {CVE-2022-0216}
- hw/scsi/lsi53c895a: Do not abort when DMA requested and no data queued (Philippe Mathieu-Daude) [Orabug: 34590706] {CVE-2022-0216}
- virtio-net: fix map leaking on error during receive (Jason Wang) [Orabug: 34538375] {CVE-2022-26353}
- vfio: defer to commit kvm irq routing when enable msi/msix (Mike Longpeng) [Orabug: 34528963]
- Revert "vfio: Avoid disabling and enabling vectors repeatedly in VFIO migration" (Mike Longpeng) [Orabug: 34528963]
- vfio: simplify the failure path in vfio_msi_enable (Mike Longpeng) [Orabug: 34528963]
- vfio: move re-enabling INTX out of the common helper (Mike Longpeng) [Orabug: 34528963]
- vfio: simplify the conditional statements in vfio_msi_enable (Mike Longpeng) [Orabug: 34528963]
- kvm/msi: do explicit commit when adding msi routes (Mike Longpeng) [Orabug: 34528963]
- kvm-irqchip: introduce new API to support route change (Mike Longpeng) [Orabug: 34528963]
- event_notifier: handle initialization failure better (Maxim Levitsky) [Orabug: 34528963]
- virtio-net: don't handle mq request in userspace handler for vhost-vdpa (Si-Wei Liu)
- vhost-vdpa: change name and polarity for vhost_vdpa_one_time_request() (Si-Wei Liu)
- vhost-vdpa: backend feature should set only once (Si-Wei Liu)
- vhost-net: fix improper cleanup in vhost_net_start (Si-Wei Liu)
- vhost-vdpa: fix improper cleanup in net_init_vhost_vdpa (Si-Wei Liu)
- virtio-net: align ctrl_vq index for non-mq guest for vhost_vdpa (Si-Wei Liu)
- virtio-net: setup vhost_dev and notifiers for cvq only when feature is negotiated (Si-Wei Liu)
- virtio: fix the condition for iommu_platform not supported (Halil Pasic)
- vdpa: Make ncs autofree (Eugenio Perez)
- vhost-vdpa: make notifiers _init()/_uninit() symmetric (Laurent Vivier)
- hw/virtio: vdpa: Fix leak of host-notifier memory-region (Laurent Vivier)
- vhost-vdpa: stick to -errno error return convention (Roman Kagan)
- vdpa: Add dummy receive callback (Eugenio Perez)
- vdpa: Check for existence of opts.vhostdev (Eugenio Perez)
- vdpa: Replace qemu_open_old by qemu_open at (Eugenio Perez)
- vhost: Fix last vq queue index of devices with no cvq (Eugenio Perez)
- vhost: Rename last_index to vq_index_end (Eugenio Perez)
- net/vhost-vdpa: fix memory leak in vhost_vdpa_get_max_queue_pairs() (Stefano Garzarella)
- vhost-vdpa: Set discarding of RAM broken when initializing the backend (David Hildenbrand)
- vhost-vdpa: multiqueue support (Jason Wang)
- virtio-net: vhost control virtqueue support (Jason Wang)
- vhost: record the last virtqueue index for the virtio device (Jason Wang)
- virtio-net: use "queue_pairs" instead of "queues" when possible (Jason Wang)
- vhost-net: control virtqueue support (Jason Wang)
- net: introduce control client (Jason Wang)
- vhost-vdpa: let net_vhost_vdpa_init() returns NetClientState * (Jason Wang)
- vhost-vdpa: prepare for the multiqueue support (Jason Wang)
- vhost-vdpa: classify one time request (Jason Wang)
- vhost-vdpa: open device fd in net_init_vhost_vdpa() (Jason Wang)
- vdpa: Check for iova range at mappings changes (Eugenio Perez)
- vdpa: Add vhost_vdpa_section_end (Eugenio Perez)
- net/vhost-vdpa: Fix device compatibility check (Kevin Wolf)
- net/vhost-user: Fix device compatibility check (Kevin Wolf)
- net: Introduce NetClientInfo.check_peer_type() (Kevin Wolf)
- memory: Name all the memory listeners (Peter Xu)
- vhost-vdpa: remove the unncessary queue_index assignment (Jason Wang)
- vhost-vdpa: fix the wrong assertion in vhost_vdpa_init() (Jason Wang)
- vhost-vdpa: tweak the error label in vhost_vdpa_add() (Jason Wang)
- vhost-vdpa: fix leaking of vhost_net in vhost_vdpa_add() (Jason Wang)
- vhost-vdpa: don't cleanup twice in vhost_vdpa_add() (Jason Wang)
- vhost-vdpa: remove the unnecessary check in vhost_vdpa_add() (Jason Wang)
- vhost_net: do not assume nvqs is always 2 (Jason Wang)
- vhost: use unsigned int for nvqs (Jason Wang)
- vhost_net: remove the meaningless assignment in vhost_net_start_one() (Jason Wang)
- vhost-vdpa: correctly return err in vhost_vdpa_set_backend_cap() (Jason Wang)
- vhost-vdpa: remove unused variable "acked_features" (Jason Wang)
- vhost: correctly detect the enabling IOMMU (Jason Wang)
- virtio-pci: implement iommu_enabled() (Jason Wang)
- virtio-bus: introduce iommu_enabled() (Jason Wang)
- hw/virtio: Fix leak of host-notifier memory-region (Yajun Wu)
- vhost-vdpa: Do not send empty IOTLB update batches (Eugenio Perez)
- target/i386/kvm: Fix disabling MPX on "-cpu host" with MPX-capable host (Maciej S. Szmigiero) [Orabug: 33528615]

* Fri Apr 8 2022 Karl Heubaum <karl.heubaum@oracle.com> - 6.1.1-3.el8
- acpi: pcihp: pcie: set power on cap on parent slot (Igor Mammedov) [Orabug: 33984018] [Orabug: 33995665]
- pcie: expire pending delete (Gerd Hoffmann) [Orabug: 33984018] [Orabug: 33995665]
- pcie: fast unplug when slot power is off (Gerd Hoffmann) [Orabug: 33984018] [Orabug: 33995665]
- pcie: factor out pcie_cap_slot_unplug() (Gerd Hoffmann) [Orabug: 33984018] [Orabug: 33995665]
- pcie: add power indicator blink check (Gerd Hoffmann) [Orabug: 33984018] [Orabug: 33995665]
- pcie: implement slot power control for pcie root ports (Gerd Hoffmann) [Orabug: 33984018] [Orabug: 33995665]
- pci: implement power state (Gerd Hoffmann) [Orabug: 33984018] [Orabug: 33995665]
- tests: bios-tables-test update expected blobs (Igor Mammedov) [Orabug: 33984018] [Orabug: 33995665]
- hw/i386/acpi-build: Deny control on PCIe Native Hot-plug in _OSC (Julia Suvorova) [Orabug: 33984018] [Orabug: 33995665]
- bios-tables-test: Allow changes in DSDT ACPI tables (Julia Suvorova) [Orabug: 33984018] [Orabug: 33995665]
- hw/acpi/ich9: Add compat prop to keep HPC bit set for 6.1 machine type (Julia Suvorova) [Orabug: 33984018] [Orabug: 33995665]

* Wed Mar 9 2022 Karl Heubaum <karl.heubaum@oracle.com> - 6.1.1-2.el8
- vhost-vsock: detach the virqueue element in case of error (Stefano Garzarella) [Orabug: 33941752] {CVE-2022-26354}
- qemu_regdump.py/qmp-regdump: Switch to Python 3 (Karl Heubaum)
- block/mirror: fix NULL pointer dereference in mirror_wait_on_conflicts() (Stefano Garzarella) [Orabug: 33916572] {CVE-2021-4145}

* Wed Feb 2 2022 Karl Heubaum <karl.heubaum@oracle.com> - 6.1.1-1.el8
- virtio-net-pci: Don't use "efi-virtio.rom" on AArch64 (Mark Kanda)
- migration: increase listening socket backlog (Elena Ufimtseva)
- virtio: Set PCI subsystem vendor ID to Oracle (Karl Heubaum)
- virtiofsd: Drop membership of all supplementary groups (CVE-2022-0358) (Vivek Goyal) [Orabug: 33816690] {CVE-2022-0358}
- acpi: validate hotplug selector on access (Michael S. Tsirkin) [Orabug: 33816625] {CVE-2021-4158}
- Update to QEMU 6.1.1 (Karl Heubaum)

* Wed Jan 19 2022 Karl Heubaum <karl.heubaum@oracle.com> - 4.2.1.15.el8
- qemu-kvm.spec: Add support for reading vmdk, vhdx, vpc, https, and ssh disk image formats from qemu-kvm (Karl Heubaum) [Orabug: 33741340]
- Document CVE-2021-4158 and CVE-2021-3947 as fixed (Mark Kanda) [Orabug: 33719302] [Orabug: 33754145] {CVE-2021-4158} {CVE-2021-3947}
- hw/block/fdc: Kludge missing floppy drive to fix CVE-2021-20196 (Philippe Mathieu-Daudé) [Orabug: 32439466] {CVE-2021-20196}
- hw/block/fdc: Extract blk_create_empty_drive() (Philippe Mathieu-Daudé) [Orabug: 32439466] {CVE-2021-20196}
- net: vmxnet3: validate configuration values during activate (CVE-2021-20203) (Prasad J Pandit) [Orabug: 32559476] {CVE-2021-20203}
- lan9118: switch to use qemu_receive_packet() for loopback (Alexander Bulekov) [Orabug: 32560540] {CVE-2021-3416}
- pcnet: switch to use qemu_receive_packet() for loopback (Alexander Bulekov) [Orabug: 32560540] {CVE-2021-3416}
- rtl8139: switch to use qemu_receive_packet() for loopback (Alexander Bulekov) [Orabug: 32560540] {CVE-2021-3416}
- tx_pkt: switch to use qemu_receive_packet_iov() for loopback (Jason Wang) [Orabug: 32560540] {CVE-2021-3416}
- sungem: switch to use qemu_receive_packet() for loopback (Jason Wang) [Orabug: 32560540] {CVE-2021-3416}
- dp8393x: switch to use qemu_receive_packet() for loopback packet (Jason Wang) [Orabug: 32560540] {CVE-2021-3416}
- e1000: switch to use qemu_receive_packet() for loopback (Jason Wang) [Orabug: 32560540] {CVE-2021-3416}
- net: introduce qemu_receive_packet() (Jason Wang) [Orabug: 32560540] {CVE-2021-3416}
- target/i386: Populate x86_ext_save_areas offsets using cpuid where possible (Paolo Bonzini)
- target/i386: Observe XSAVE state area offsets (Paolo Bonzini)
- target/i386: Make x86_ext_save_areas visible outside cpu.c (Paolo Bonzini)
- target/i386: Pass buffer and length to XSAVE helper (Paolo Bonzini)
- target/i386: Clarify the padding requirements of X86XSaveArea (Paolo Bonzini)
- target/i386: Consolidate the X86XSaveArea offset checks (Paolo Bonzini)
- target/i386: Declare constants for XSAVE offsets (Paolo Bonzini)

* Wed Dec 22 2021 Karl Heubaum <karl.heubaum@oracle.com> - 4.2.1-14.el8
- scsi: fix sense code for EREMOTEIO (Paolo Bonzini) [Orabug: 33537443]
- scsi: move host_status handling into SCSI drivers (Hannes Reinecke) [Orabug: 33537443]
- scsi: inline sg_io_sense_from_errno() into the callers (Hannes Reinecke) [Orabug: 33537443]
- scsi-generic: do not snoop the output of failed commands (Paolo Bonzini) [Orabug: 33537443]
- scsi: Add mapping for generic SCSI_HOST status to sense codes (Hannes Reinecke) [Orabug: 33537443]
- scsi: Rename linux-specific SG_ERR codes to generic SCSI_HOST error codes (Hannes Reinecke) [Orabug: 33537443]
- scsi: drop 'result' argument from command_complete callback (Hannes Reinecke) [Orabug: 33537443]
- scsi-disk: pass guest recoverable errors through even for rerror=stop (Paolo Bonzini) [Orabug: 33537443]
- scsi-disk: pass SCSI status to scsi_handle_rw_error (Paolo Bonzini) [Orabug: 33537443]
- scsi: introduce scsi_sense_from_errno() (Paolo Bonzini) [Orabug: 33537443]
- scsi-disk: do not complete requests early for rerror/werror=ignore (Paolo Bonzini) [Orabug: 33537443]
- scsi-disk: move scsi_handle_rw_error earlier (Paolo Bonzini) [Orabug: 33537443]
- scsi-disk: convert more errno values back to SCSI statuses (Paolo Bonzini) [Orabug: 33537443]

* Wed Dec 15 2021 Karl Heubaum <karl.heubaum@oracle.com> - 4.2.1-13.el8
- pcie: Do not set power state for some hot-plugged devices (Annie Li) [Orabug: 33642532]

* Thu Dec 2 2021 Karl Heubaum <karl.heubaum@oracle.com> - 4.2.1-12.1.el8
- Update slirp to address various CVEs (Mark Kanda) [Orabug: 32208456] [Orabug: 33014409] [Orabug: 33014414] [Orabug: 33014417] [Orabug: 33014420] {CVE-2020-29129} {CVE-2020-29130} {CVE-2021-3592} {CVE-2021-3593} {CVE-2021-3594} {CVE-2021-3595}
- hw/pflash_cfi01: Allow backing devices to be smaller than memory region (David Edmondson)
- pcie: expire pending delete (Gerd Hoffmann) [Orabug: 33450706]
- pcie: fast unplug when slot power is off (Gerd Hoffmann) [Orabug: 33450706]
- pcie: factor out pcie_cap_slot_unplug() (Gerd Hoffmann) [Orabug: 33450706]
- pcie: add power indicator blink check (Gerd Hoffmann) [Orabug: 33450706]
- pcie: implement slot power control for pcie root ports (Gerd Hoffmann) [Orabug: 33450706]
- pci: implement power state (Gerd Hoffmann) [Orabug: 33450706]
- hw/pci/pcie: Move hot plug capability check to pre_plug callback (Julia Suvorova) [Orabug: 33450706]
- hw/pci/pcie: Replace PCI_DEVICE() casts with existing variable (Julia Suvorova) [Orabug: 33450706]
- hw/pci/pcie: Forbid hot-plug if it's disabled on the slot (Julia Suvorova) [Orabug: 33450706]
- pcie_root_port: Add hotplug disabling option (Julia Suvorova) [Orabug: 33450706]
- qdev-monitor: Forbid repeated device_del (Julia Suvorova) [Orabug: 33450706]
- i386:acpi: Remove _HID from the SMBus ACPI entry (Corey Minyard)
- uas: add stream number sanity checks (Gerd Hoffmann) [Orabug: 33280793] {CVE-2021-3713}
- usbredir: fix free call (Gerd Hoffmann) [Orabug: 33198441] {CVE-2021-3682}
- hw/scsi/scsi-disk: MODE_PAGE_ALLS not allowed in MODE SELECT commands (Mauro Matteo Cascella) [Orabug: 33548490] {CVE-2021-3930}
- e1000: fix tx re-entrancy problem (Jon Maloy) [Orabug: 32560552] {CVE-2021-20257}
- virtio-net-pci: Don't use "efi-virtio.rom" on AArch64 (Mark Kanda) [Orabug: 33537594]
- MAINTAINERS: Add ACPI/HEST/GHES entries (Dongjiu Geng)
- target-arm: kvm64: handle SIGBUS signal from kernel or KVM (Dongjiu Geng)
- ACPI: Record Generic Error Status Block(GESB) table (Dongjiu Geng)
- KVM: Move hwpoison page related functions into kvm-all.c (Dongjiu Geng)
- ACPI: Record the Generic Error Status Block address (Dongjiu Geng)
- ACPI: Build Hardware Error Source Table (Dongjiu Geng)
- ACPI: Build related register address fields via hardware error fw_cfg blob (Dongjiu Geng)
- docs: APEI GHES generation and CPER record description (Dongjiu Geng)
- hw/arm/virt: Introduce a RAS machine option (Dongjiu Geng)
- acpi: nvdimm: change NVDIMM_UUID_LE to a common macro (Dongjiu Geng)
- block/curl: HTTP header field names are case insensitive (David Edmondson) [Orabug: 33287589]
- block/curl: HTTP header fields allow whitespace around values (David Edmondson) [Orabug: 33287589]

* Sun Sep 12 2021 Karl Heubaum <karl.heubaum@oracle.com> - 4.2.1-11.el8
- trace: use STAP_SDT_V2 to work around symbol visibility (Stefan Hajnoczi) [Orabug: 33272428]

* Tue Jul 27 2021 Karl Heubaum <karl.heubaum@oracle.com> - 4.2.1-11.el8
- pvrdma: Fix the ring init error flow (Marcel Apfelbaum) [Orabug: 33120142] {CVE-2021-3608}
- pvrdma: Ensure correct input on ring init (Marcel Apfelbaum) [Orabug: 33120146] {CVE-2021-3607}
- hw/rdma: Fix possible mremap overflow in the pvrdma device (Marcel Apfelbaum) [Orabug: 33120084] {CVE-2021-3582}
- vhost-user-gpu: reorder free calls (Gerd Hoffmann) [Orabug: 32950701] {CVE-2021-3544}
- vhost-user-gpu: abstract vg_cleanup_mapping_iov (Li Qiang) [Orabug: 32950716] {CVE-2021-3546}
- vhost-user-gpu: fix OOB write in 'virgl_cmd_get_capset' (Li Qiang) [Orabug: 32950716] {CVE-2021-3546}
- vhost-user-gpu: fix memory leak in 'virgl_resource_attach_backing' (Li Qiang) [Orabug: 32950701] {CVE-2021-3544}
- vhost-user-gpu: fix memory leak in 'virgl_cmd_resource_unref' (Li Qiang) [Orabug: 32950701] {CVE-2021-3544}
- vhost-user-gpu: fix memory leak while calling 'vg_resource_unref' (Li Qiang) [Orabug: 32950701] {CVE-2021-3544}
- vhost-user-gpu: fix memory leak in vg_resource_attach_backing (Li Qiang) [Orabug: 32950701] {CVE-2021-3544}
- vhost-user-gpu: fix resource leak in 'vg_resource_create_2d' (Li Qiang) [Orabug: 32950701] {CVE-2021-3544}
- vhost-user-gpu: fix memory disclosure in virgl_cmd_get_capset_info (Li Qiang) [Orabug: 32950708] {CVE-2021-3545}
- usb: limit combined packets to 1 MiB (Gerd Hoffmann) [Orabug: 32842778] {CVE-2021-3527}
- usb/redir: avoid dynamic stack allocation (Gerd Hoffmann) [Orabug: 32842778] {CVE-2021-3527}
- mptsas: Remove unused MPTSASState 'pending' field (Michael Tokarev) [Orabug: 32470463] {CVE-2021-3392}
- oslib-posix: initialize backend memory objects in parallel (Mark Kanda) [Orabug: 32555402]
- oslib-posix: refactor memory prealloc threads (Mark Kanda) [Orabug: 32555402]

* Tue Jun 29 2021 Karl Heubaum <karl.heubaum@oracle.com> - 4.2.1-10.el8
- e1000: fail early for evil descriptor (Jason Wang) [Orabug: 32560552] {CVE-2021-20257}
- Document CVE-2020-27661 as fixed (Mark Kanda) [Orabug: 32960200] {CVE-2020-27661}
- block: Avoid stale pointer dereference in blk_get_aio_context() (Greg Kurz)
- block: Fix blk->in_flight during blk_wait_while_drained() (Kevin Wolf)
- block: Increase BB.in_flight for coroutine and sync interfaces (Kevin Wolf)
- block-backend: Reorder flush/pdiscard function definitions (Kevin Wolf)
- i386/pc: let iterator handle regions below 4G (Joao Martins)
- arm/virt: Add memory hot remove support (Shameer Kolothum) [Orabug: 32643506]
- i386/pc: consolidate usable iova iteration (Joao Martins)
- i386/acpi: fix SRAT ranges in accordance to usable IOVA (Joao Martins)
- migration: increase listening socket backlog (Elena Ufimtseva)
- multifd: Make multifd_save_setup() get an Error parameter (Juan Quintela)
- multifd: Make multifd_load_setup() get an Error parameter (Juan Quintela)
- migration: fix maybe-uninitialized warning (Marc-André Lureau)
- migration: Fix the re-run check of the migrate-incoming command (Yury Kotov)
- multifd: Initialize local variable (Juan Quintela)
- multifd: Be consistent about using uint64_t (Juan Quintela)
- Bug #1829242 correction. (Alexey Romko)
- migration/multifd: fix destroyed mutex access in terminating multifd threads (Jiahui Cen)
- migration/multifd: fix nullptr access in terminating multifd threads (Jiahui Cen)
- migration/multifd: not use multifd during postcopy (Wei Yang)
- migration/multifd: clean pages after filling packet (Wei Yang)
- migration: Make sure that we don't call write() in case of error (Juan Quintela)
- migration: fix multifd_send_pages() next channel (Laurent Vivier)
- migration/multifd: bypass uuid check for initial packet (Elena Ufimtseva) [Orabug: 32610480]
- migration/tls: add error handling in multifd_tls_handshake_thread (Hao Wang)
- migration/tls: fix inverted semantics in multifd_channel_connect (Hao Wang)
- migration/multifd: do not access uninitialized multifd_recv_state (Elena Ufimtseva) [Orabug: 32795384]
- io/channel-tls.c: make qio_channel_tls_shutdown thread-safe (Lukas Straub)
- qemu.spec: Enable qemu-guest-agent RPM for OL7 (Karl Heubaum) [Orabug: 32415543]
- virtio-net: Set mac address to hardware if the peer is vdpa (Cindy Lu)
- net: Add vhost-vdpa in show_netdevs() (Cindy Lu)
- vhost-vdpa: Add qemu_close in vhost_vdpa_cleanup (Cindy Lu)
- hw/virtio/vhost-vdpa: Fix Coverity CID 1432864 (Philippe Mathieu-Daudé)
- vhost-vdpa: negotiate VIRTIO_NET_F_STATUS with driver (Si-Wei Liu)
- configure: Fix build dependencies with vhost-vdpa. (Laurent Vivier)
- configure: simplify vhost condition with Kconfig (Marc-André Lureau)
- vhost-vdpa: add trace-events (Laurent Vivier)
- dma/pl330: Fix qemu_hexdump() usage in pl330.c (Mark Kanda)
- util/hexdump: introduce qemu_hexdump_line() (Laurent Vivier)
- util/hexdump: Reorder qemu_hexdump() arguments (Philippe Mathieu-Daudé)
- util/hexdump: Convert to take a void pointer argument (Philippe Mathieu-Daudé)
- net/colo-compare.c: Only hexdump packets if tracing is enabled (Lukas Straub)
- vhost-vdpa: batch updating IOTLB mappings (Jason Wang)
- vhost: switch to use IOTLB v2 format (Jason Wang)
- vhost-vdpa: remove useless variable (Laurent Vivier)
- virtio: vdpa: omit check return of g_malloc (Li Qiang)
- vhost-vdpa: fix indentation in vdpa_ops (Stefano Garzarella)
- virtio-net: check the existence of peer before accessing vDPA config (Jason Wang)
- virtio-pci: fix wrong index in virtio_pci_queue_enabled (Yuri Benditovich)
- virtio-pci: fix virtio_pci_queue_enabled() (Laurent Vivier)
- vhost-vdpa :Fix Coverity CID 1430270 / CID 1420267 (Cindy Lu)
- vhost-vdpa: fix the compile issue without kvm (Cindy Lu)
- vhost-vdpa: introduce vhost-vdpa net client (Cindy Lu)
- vhost-vdpa: introduce vhost-vdpa backend (Cindy Lu)
- linux headers: sync to 5.9-rc4 (Jason Wang)
- Linux headers: update (Cornelia Huck)
- virtio-net: fix rsc_ext compat handling (Cornelia Huck)
- linux-headers: update against Linux 5.7-rc3 (Cornelia Huck)
- linux-headers: update (Cornelia Huck)
- virtiofsd: Pull in kernel's fuse.h (Dr. David Alan Gilbert)
- linux-headers: Update (Bharata B Rao)
- linux-headers: Update (Greg Kurz)
- vhost_net: introduce set_config & get_config (Cindy Lu)
- vhost: implement vhost_force_iommu method (Cindy Lu)
- vhost: introduce new VhostOps vhost_force_iommu (Cindy Lu)
- vhost: implement vhost_vq_get_addr method (Cindy Lu)
- vhost: introduce new VhostOps vhost_vq_get_addr (Cindy Lu)
- vhost: implement vhost_dev_start method (Cindy Lu)
- vhost: introduce new VhostOps vhost_dev_start (Cindy Lu)
- vhost: check the existence of vhost_set_iotlb_callback (Jason Wang)
- virtio-pci: implement queue_enabled method (Jason Wang)
- virtio-bus: introduce queue_enabled method (Jason Wang)
- vhost_net: use the function qemu_get_peer (Cindy Lu)
- net: introduce qemu_get_peer (Cindy Lu)
- vhost: correctly turn on VIRTIO_F_IOMMU_PLATFORM (Jason Wang)
- imx7-ccm: add digprog mmio write method (Prasad J Pandit) [Orabug: 31576552] {CVE-2020-15469}
- tz-ppc: add dummy read/write methods (Prasad J Pandit) [Orabug: 31576552] {CVE-2020-15469}
- spapr_pci: add spapr msi read method (Prasad J Pandit) [Orabug: 31576552] {CVE-2020-15469}
- nvram: add nrf51_soc flash read method (Prasad J Pandit) [Orabug: 31576552] {CVE-2020-15469}
- prep: add ppc-parity write method (Prasad J Pandit) [Orabug: 31576552] {CVE-2020-15469}
- vfio: add quirk device write method (Prasad J Pandit) [Orabug: 31576552] {CVE-2020-15469}
- pci-host: designware: add pcie-msi read method (Prasad J Pandit) [Orabug: 31576552] {CVE-2020-15469}
- hw/pci-host: add pci-intack write method (Prasad J Pandit) [Orabug: 31576552] {CVE-2020-15469}
- oslib-posix: take lock before qemu_cond_broadcast (Bauerchen) [Orabug: 32555402]
- oslib-posix: initialize mutex and condition variable (Paolo Bonzini) [Orabug: 32555402]
- mem-prealloc: optimize large guest startup (Bauerchen) [Orabug: 32555402]
- i386: Add the support for AMD EPYC 3rd generation processors (Babu Moger)
- acpi: cpuhp: document CPHP_GET_CPU_ID_CMD command (Igor Mammedov)
- acpi: cpuhp: add CPHP_GET_CPU_ID_CMD command (Igor Mammedov)
- acpi: cpuhp: spec: add typical usecases (Igor Mammedov)
- acpi: cpuhp: spec: clarify store into 'Command data' when 'Command field' == 0 (Igor Mammedov)
- acpi: cpuhp: spec: fix 'Command data' description (Igor Mammedov)
- acpi: cpuhp: spec: clarify 'CPU selector' register usage and endianness (Igor Mammedov)
- acpi: cpuhp: introduce 'Command data 2' field (Igor Mammedov)
- x86: ich9: let firmware negotiate 'CPU hot-unplug with SMI' feature (Igor Mammedov)
- x86: ich9: factor out "guest_cpu_hotplug_features" (Igor Mammedov)
- x86: acpi: let the firmware handle pending "CPU remove" events in SMM (Igor Mammedov)
- x86: acpi: introduce AcpiPmInfo::smi_on_cpu_unplug (Igor Mammedov)
- acpi: cpuhp: introduce 'firmware performs eject' status/control bits (Igor Mammedov)
- x68: acpi: trigger SMI before sending hotplug Notify event to OSPM (Igor Mammedov)
- x86: acpi: introduce the PCI0.SMI0 ACPI device (Igor Mammedov)
- x86: acpi: introduce AcpiPmInfo::smi_on_cpuhp (Igor Mammedov)
- x86: ich9: expose "smi_negotiated_features" as a QOM property (Igor Mammedov)
- tests: acpi: mark to be changed tables in bios-tables-test-allowed-diff (Igor Mammedov)
- acpi: add aml_land() and aml_break() primitives (Igor Mammedov)
- x86: cpuhp: refuse cpu hot-unplug request earlier if not supported (Igor Mammedov)
- x86: cpuhp: prevent guest crash on CPU hotplug when broadcast SMI is in use (Igor Mammedov)
- x86: lpc9: let firmware negotiate 'CPU hotplug with SMI' features (Igor Mammedov)
- q35: implement 128K SMRAM at default SMBASE address (Igor Mammedov)
- hw/intc/arm_gic: Fix interrupt ID in GICD_SGIR register (Philippe Mathieu-Daudé) [Orabug: 32470471] {CVE-2021-20221}
- memory: clamp cached translation in case it points to an MMIO region (Paolo Bonzini) [Orabug: 32252673] {CVE-2020-27821}
- hw/sd/sdhci: Fix DMA Transfer Block Size field (Philippe Mathieu-Daudé) [Orabug: 32613470] {CVE-2021-3409}

* Wed Mar 31 2021 Karl Heubaum <karl.heubaum@oracle.com> - 4.2.1-6.el8
- i386/pc: Keep PCI 64-bit hole within usable IOVA space (Joao Martins)
- pc/cmos: Adjust CMOS above 4G memory size according to 1Tb boundary (Joao Martins)
- i386/pc: Round up the hotpluggable memory within valid IOVA ranges (Joao Martins)
- i386/pc: Account IOVA reserved ranges above 4G boundary (Joao Martins)

* Thu Mar 11 2021 Karl Heubaum <karl.heubaum@oracle.com> - 4.2.1-5.el8
- hostmem: fix default "prealloc-threads" count (Mark Kanda)
- hostmem: introduce "prealloc-threads" property (Igor Mammedov)
- qom: introduce object_register_sugar_prop (Paolo Bonzini)
- migration/multifd: Do error_free after migrate_set_error to avoid memleaks (Pan Nengyuan)
- multifd/tls: fix memoryleak of the QIOChannelSocket object when cancelling migration (Chuan Zheng)
- migration/multifd: fix hangup with TLS-Multifd due to blocking handshake (Chuan Zheng)
- migration/tls: add trace points for multifd-tls (Chuan Zheng)
- migration/tls: add support for multifd tls-handshake (Chuan Zheng)
- migration/tls: extract cleanup function for common-use (Chuan Zheng)
- migration/multifd: fix memleaks in multifd_new_send_channel_async (Pan Nengyuan)
- migration/multifd: fix nullptr access in multifd_send_terminate_threads (Zhimin Feng)
- migration/tls: add tls_hostname into MultiFDSendParams (Chuan Zheng)
- migration/tls: extract migration_tls_client_create for common-use (Chuan Zheng)
- migration/tls: save hostname into MigrationState (Chuan Zheng)
- tests/qtest: add a test case for pvpanic-pci (Mihai Carabas)
- pvpanic : update pvpanic spec document (Mihai Carabas)
- hw/misc/pvpanic: add PCI interface support (Mihai Carabas)
- hw/misc/pvpanic: split-out generic and bus dependent code (Mihai Carabas)
- qemu-img: Add --target-is-zero to convert (David Edmondson)
- 9pfs: Fully restart unreclaim loop (CVE-2021-20181) (Greg Kurz) [Orabug: 32441198] {CVE-2021-20181}
- ide: atapi: check logical block address and read size (CVE-2020-29443) (Prasad J Pandit) [Orabug: 32393835] {CVE-2020-29443}
- Document CVE-2019-20808 as fixed (Mark Kanda) [Orabug: 32339196] {CVE-2019-20808}
- block/iscsi:fix heap-buffer-overflow in iscsi_aio_ioctl_cb (Chen Qun) [Orabug: 32339207] {CVE-2020-11947}
- net: remove an assert call in eth_get_gso_type (Prasad J Pandit) [Orabug: 32102583] {CVE-2020-27617}
- nvdimm: honor -object memory-backend-file, readonly=on option (Stefan Hajnoczi) [Orabug: 32265408]
- hostmem-file: add readonly=on|off option (Stefan Hajnoczi) [Orabug: 32265408]
- memory: add readonly support to memory_region_init_ram_from_file() (Stefan Hajnoczi) [Orabug: 32265408]

* Thu Jan 14 2021 Karl Heubaum <karl.heubaum@oracle.com> - 4.2.1-4.el8
- Document CVE-2020-25723 as fixed (Mark Kanda) [Orabug: 32222397] {CVE-2020-25723}
- hw/net/e1000e: advance desc_offset in case of null descriptor (Prasad J Pandit) [Orabug: 32217517] {CVE-2020-28916}
- i386: Add 2nd Generation AMD EPYC processors (Babu Moger) [Orabug: 32217570]
- libslirp: Update version to include CVE fixes (Mark Kanda) [Orabug: 32208456] [Orabug: 32208462] {CVE-2020-29129} {CVE-2020-29130}
- Document CVE-2020-25624 as fixed (Mark Kanda) [Orabug: 32212527] {CVE-2020-25624}
- pvpanic: Advertise the PVPANIC_CRASHLOADED event support (Paolo Bonzini) [Orabug: 32102853]
- ati: check x y display parameter values (Prasad J Pandit) [Orabug: 32108251] {CVE-2020-27616}
- Add AArch64 support for QMP regdump tool and sosreport plugin (Mark Kanda) [Orabug: 32080658]
- Add qemu_regdump sosreport plugin support for '-mon' QMP sockets (Mark Kanda)
- migration/dirtyrate: present dirty rate only when querying the rate has completed (Chuan Zheng)
- migration/dirtyrate: record start_time and calc_time while at the measuring state (Chuan Zheng)
- migration/dirtyrate: Add trace_calls to make it easier to debug (Chuan Zheng)
- migration/dirtyrate: Implement qmp_cal_dirty_rate()/qmp_get_dirty_rate() function (Chuan Zheng)
- migration/dirtyrate: Implement calculate_dirtyrate() function (Chuan Zheng)
- migration/dirtyrate: Implement set_sample_page_period() and is_sample_period_valid() (Chuan Zheng)
- migration/dirtyrate: skip sampling ramblock with size below MIN_RAMBLOCK_SIZE (Chuan Zheng)
- migration/dirtyrate: Compare page hash results for recorded sampled page (Chuan Zheng)
- migration/dirtyrate: Record hash results for each sampled page (Chuan Zheng)
- migration/dirtyrate: move RAMBLOCK_FOREACH_MIGRATABLE into ram.h (Chuan Zheng)
- migration/dirtyrate: Add dirtyrate statistics series functions (Chuan Zheng)
- migration/dirtyrate: Add RamblockDirtyInfo to store sampled page info (Chuan Zheng)
- migration/dirtyrate: add DirtyRateStatus to denote calculation status (Chuan Zheng)
- migration/dirtyrate: setup up query-dirtyrate framwork (Chuan Zheng)
- ram_addr: Split RAMBlock definition (Juan Quintela)

* Tue Sep 29 2020 Karl Heubaum <karl.heubaum@oracle.com> - 4.2.1-3.el8
- qemu-kvm.spec: Install block storage module RPMs by default (Karl Heubaum) [Orabug: 31943789]
- qemu-kvm.spec: Enable block-ssh module RPM (Karl Heubaum) [Orabug: 31943763]
- hw: usb: hcd-ohci: check for processed TD before retire (Prasad J Pandit) [Orabug: 31901690] {CVE-2020-25625}
- hw: usb: hcd-ohci: check len and frame_number variables (Prasad J Pandit) [Orabug: 31901690] {CVE-2020-25625}
- hw: ehci: check return value of 'usb_packet_map' (Li Qiang) [Orabug: 31901649] {CVE-2020-25084}
- hw: xhci: check return value of 'usb_packet_map' (Li Qiang) [Orabug: 31901649] {CVE-2020-25084}
- usb: fix setup_len init (CVE-2020-14364) (Gerd Hoffmann) [Orabug: 31848849] {CVE-2020-14364}
- Document CVE-2020-12829 and CVE-2020-14415 as fixed (Mark Kanda) [Orabug: 31855502] [Orabug: 31855427] {CVE-2020-12829} {CVE-2020-14415}

* Mon Aug 31 2020 Karl Heubaum <karl.heubaum@oracle.com> - 4.2.1-2.el8
- hw/net/xgmac: Fix buffer overflow in xgmac_enet_send() (Mauro Matteo Cascella) [Orabug: 31667649] {CVE-2020-15863}
- hw/net/net_tx_pkt: fix assertion failure in net_tx_pkt_add_raw_fragment() (Mauro Matteo Cascella) [Orabug: 31737809] {CVE-2020-16092}
- migration: fix memory leak in qmp_migrate_set_parameters (Zheng Chuan) [Orabug: 31806256]
- virtio-net: fix removal of failover device (Juan Quintela) [Orabug: 31806255]
- pvpanic: introduce crashloaded for pvpanic (zhenwei pi) [Orabug: 31677154]

* Wed Jul 22 2020 Karl Heubaum <karl.heubaum@oracle.com> - 4.2.1-1.el8
- hw/sd/sdcard: Do not switch to ReceivingData if address is invalid (Philippe Mathieu-Daudé)  [Orabug: 31414336]  {CVE-2020-13253}
- hw/sd/sdcard: Update coding style to make checkpatch.pl happy (Philippe Mathieu-Daudé)  [Orabug: 31414336]
- hw/sd/sdcard: Do not allow invalid SD card sizes (Philippe Mathieu-Daudé)  [Orabug: 31414336]  {CVE-2020-13253}
- hw/sd/sdcard: Simplify realize() a bit (Philippe Mathieu-Daudé)  [Orabug: 31414336]
- hw/sd/sdcard: Restrict Class 6 commands to SCSD cards (Philippe Mathieu-Daudé)  [Orabug: 31414336]
- libslirp: Update to v4.3.1 to fix CVE-2020-10756 (Karl Heubaum)  [Orabug: 31604999]  {CVE-2020-10756}
- Document CVEs as fixed 2/2 (Karl Heubaum)  [Orabug: 30618035]  {CVE-2017-18043} {CVE-2018-10839} {CVE-2018-11806} {CVE-2018-12617} {CVE-2018-15746} {CVE-2018-16847} {CVE-2018-16867} {CVE-2018-17958} {CVE-2018-17962} {CVE-2018-17963} {CVE-2018-18849} {CVE-2018-19364} {CVE-2018-19489} {CVE-2018-3639} {CVE-2018-5683} {CVE-2018-7550} {CVE-2018-7858} {CVE-2019-12068} {CVE-2019-15034} {CVE-2019-15890} {CVE-2019-20382} {CVE-2020-10702} {CVE-2020-10761} {CVE-2020-11102} {CVE-2020-11869} {CVE-2020-13361} {CVE-2020-13765} {CVE-2020-13800} {CVE-2020-1711} {CVE-2020-1983} {CVE-2020-8608}
- Document CVEs as fixed 1/2 (Karl Heubaum)  [Orabug: 30618035]  {CVE-2017-10806} {CVE-2017-11334} {CVE-2017-12809} {CVE-2017-13672} {CVE-2017-13673} {CVE-2017-13711} {CVE-2017-14167} {CVE-2017-15038} {CVE-2017-15119} {CVE-2017-15124} {CVE-2017-15268} {CVE-2017-15289} {CVE-2017-16845} {CVE-2017-17381} {CVE-2017-18030} {CVE-2017-2630} {CVE-2017-2633} {CVE-2017-5715} {CVE-2017-5753} {CVE-2017-5754} {CVE-2017-5931} {CVE-2017-6058} {CVE-2017-7471} {CVE-2017-7493} {CVE-2017-8112} {CVE-2017-8309} {CVE-2017-8379} {CVE-2017-8380} {CVE-2017-9503} {CVE-2017-9524} {CVE-2018-12126} {CVE-2018-12127} {CVE-2018-12130} {CVE-2018-16872} {CVE-2018-20123} {CVE-2018-20124} {CVE-2018-20125} {CVE-2018-20126} {CVE-2018-20191} {CVE-2018-20216} {CVE-2018-20815} {CVE-2019-11091} {CVE-2019-12155} {CVE-2019-14378} {CVE-2019-3812} {CVE-2019-5008} {CVE-2019-6501} {CVE-2019-6778} {CVE-2019-8934} {CVE-2019-9824}
- qemu-kvm.spec: Add .spec file for OL8 (Karl Heubaum)  [Orabug: 30618035]
- qemu.spec: Add .spec file for OL7 (Karl Heubaum)  [Orabug: 30618035]
- qemu-submodule-init: Add Git submodule init script (Karl Heubaum)  [Orabug: 30618035]
- vhost.conf: Initial vhost.conf (Karl Heubaum)  [Orabug: 30618035]
- parfait: Add buildrpm/parfait-qemu.conf (Karl Heubaum)  [Orabug: 30618035]
- virtio: Set PCI subsystem vendor ID to Oracle (Karl Heubaum)  [Orabug: 30618035]
- qemu_regdump.py: Initial qemu_regdump.py (Karl Heubaum)  [Orabug: 30618035]
- qmp-regdump: Initial qmp-regdump (Karl Heubaum)  [Orabug: 30618035]
- bridge.conf: Initial bridge.conf (Karl Heubaum)  [Orabug: 30618035]
- kvm.conf: Initial kvm.conf (Karl Heubaum)  [Orabug: 30618035]
- 80-kvm.rules: Initial 80-kvm.rules (Karl Heubaum)  [Orabug: 30618035]
- exec: set map length to zero when returning NULL (Prasad J Pandit)  [Orabug: 31439733]  {CVE-2020-13659}
- megasas: use unsigned type for reply_queue_head and check index (Prasad J Pandit)  [Orabug: 31414338]  {CVE-2020-13362}
- memory: Revert "memory: accept mismatching sizes in memory_region_access_valid" (Michael S. Tsirkin)  [Orabug: 31439736] [Orabug: 31452202]  {CVE-2020-13754} {CVE-2020-13791}

* Wed Jul 22 2020 Karl Heubaum <karl.heubaum@oracle.com> - 4.1.1-3.el8
- buildrpm/spec files: Don't package elf2dmp (Karl Heubaum)  [Orabug: 31657424]
- qemu-kvm.spec: Enable the block-curl package (Karl Heubaum)  [Orabug: 31657424]
- qemu.spec: enable have_curl in spec (Dongli Zhang)  [Orabug: 31657424]

* Wed Jun 10 2020 Karl Heubaum <karl.heubaum@oracle.com> - 4.1.1-2.el8
- Document CVE-2020-13765 as fixed (Karl Heubaum)  [Orabug: 31463250]  {CVE-2020-13765}
- kvm: Reallocate dirty_bmap when we change a slot (Dr. David Alan Gilbert)  [Orabug: 31076399]
- kvm: split too big memory section on several memslots (Igor Mammedov)  [Orabug: 31076399]
- target/i386: do not set unsupported VMX secondary execution controls (Vitaly Kuznetsov)  [Orabug: 31463710]
- target/i386: add VMX definitions (Paolo Bonzini)  [Orabug: 31463710]
- ati-vga: check mm_index before recursive call (CVE-2020-13800) (Prasad J Pandit)  [Orabug: 31452206]  {CVE-2020-13800}
- es1370: check total frame count against current frame (Prasad J Pandit)  [Orabug: 31463235]  {CVE-2020-13361}
- ati-vga: Fix checks in ati_2d_blt() to avoid crash (BALATON Zoltan)  [Orabug: 31238432]  {CVE-2020-11869}
- libslirp: Update to stable-4.2 to fix CVE-2020-1983 (Karl Heubaum)  [Orabug: 31241227]  {CVE-2020-1983}
- Document CVEs as fixed (Karl Heubaum)   {CVE-2019-12068} {CVE-2019-15034}
- libslirp: Update to version 4.2.0 to fix CVEs (Karl Heubaum)  [Orabug: 30274592] [Orabug: 30869830]  {CVE-2019-15890} {CVE-2020-8608}
- target/i386: add support for MSR_IA32_TSX_CTRL (Paolo Bonzini)  [Orabug: 31124041]
- qemu-img: Add --target-is-zero to convert (David Edmondson)
- vnc: fix memory leak when vnc disconnect (Li Qiang)  [Orabug: 30996427]  {CVE-2019-20382}
- iscsi: Cap block count from GET LBA STATUS (CVE-2020-1711) (Felipe Franciosi)  [Orabug: 31124035]  {CVE-2020-1711}
- qemu.spec: Remove "BuildRequires: kernel" (Karl Heubaum)  [Orabug: 31124047]
