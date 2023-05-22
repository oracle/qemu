
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
%global have_linux_io_uring 1

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
%global have_gluster 0
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
%else                                                            \
Obsoletes: %{name}-block-gluster <= %{epoch}:%{version}-%{release} \
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
Release: 3%{?dist}
Epoch: 30
License: GPLv2+ and LGPLv2+ and BSD
Group: Development/Tools
URL: http://www.qemu.org/
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
%if 0%{?have_linux_io_uring}
BuildRequires: liburing-devel
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
%if 0%{have_tools}
Requires: qemu-img = %{epoch}:%{version}-%{release}
%endif
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

%if 0%{have_tools}

%package -n qemu-img
Summary: QEMU command line tool for manipulating disk images
Group: Development/Tools

%description -n qemu-img
This package provides a command line tool for manipulating disk images.

%endif

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

mkdir -p %{buildroot}%{_libexecdir}/
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
rm -f %{buildroot}%{_bindir}/elf2dmp

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
chmod -f +x %{buildroot}%{_libdir}/qemu-kvm/block-*.so || true


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
%if 0%{?have_tools}
%{_bindir}/qemu-pr-helper
%endif
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

%if 0%{have_tools}

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
* Thu May 18 2023  Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-3.el9
- vfio/migration: Skip log_sync during migration SETUP state (Avihai Horon) [Orabug: 35384144]
- migration: fix ram_state_pending_exact() (Juan Quintela) [Orabug: 35384144]

* Mon May 8 2023  Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-2.el9
- spec: allow have_tools 0 (Steve Sistare)
- spec: allow no block device modules (Steve Sistare)
- qemu-kvm.spec: fix Linux io_uring support (Mark Kanda)
- hw/intc/ioapic: Update KVM routes before redelivering IRQ, on RTE update (David Woodhouse) [Orabug: 35219295]
- oslib-posix: fix uninitialized var in wait_mem_prealloc() (Mark Kanda)
- vfio/migration: Rename entry points (Alex Williamson)
- docs/devel: Document VFIO device dirty page tracking (Avihai Horon)
- vfio/migration: Query device dirty page tracking support (Joao Martins)
- vfio/migration: Block migration with vIOMMU (Joao Martins)
- vfio/common: Add device dirty page bitmap sync (Joao Martins)
- vfio/common: Extract code from vfio_get_dirty_bitmap() to new function (Avihai Horon)
- vfio/common: Add device dirty page tracking start/stop (Joao Martins)
- vfio/common: Record DMA mapped IOVA ranges (Joao Martins)
- vfio/common: Add helper to consolidate iova/end calculation (Joao Martins)
- vfio/common: Consolidate skip/invalid section into helper (Joao Martins)
- vfio/common: Use a single tracepoint for skipped sections (Joao Martins)
- vfio/common: Add helper to validate iova/end against hostwin (Joao Martins)
- vfio/common: Add VFIOBitmap and alloc function (Avihai Horon)
- vfio/common: Abort migration if dirty log start/stop/sync fails (Avihai Horon)
- vfio/common: Fix wrong %m usages (Avihai Horon)
- vfio/common: Fix error reporting in vfio_get_dirty_bitmap() (Avihai Horon)
- docs/devel: Align VFIO migration docs to v2 protocol (Avihai Horon)
- vfio: Alphabetize migration section of VFIO trace-events file (Avihai Horon)
- vfio/migration: Remove VFIO migration protocol v1 (Avihai Horon)
- vfio/migration: Implement VFIO migration protocol v2 (Avihai Horon)
- vfio/migration: Rename functions/structs related to v1 protocol (Avihai Horon)
- vfio/migration: Move migration v1 logic to vfio_migration_init() (Avihai Horon)
- vfio/migration: Block multiple devices migration (Avihai Horon)
- vfio/common: Change vfio_devices_all_running_and_saving() logic to equivalent one (Avihai Horon)
- vfio/migration: Allow migration without VFIO IOMMU dirty tracking support (Avihai Horon)
- vfio/migration: Fix NULL pointer dereference bug (Avihai Horon)
- linux-headers: Update to v6.2-rc8 (Avihai Horon)
- migration/qemu-file: Add qemu_file_get_to_fd() (Avihai Horon)
- migration: Rename res_{postcopy,precopy}_only (Juan Quintela)
- migration: Remove unused res_compatible (Juan Quintela)
- migration: In case of postcopy, the memory ends in res_postcopy_only (Juan Quintela)
- migration: I messed state_pending_exact/estimate (Juan Quintela)
- linux-headers: Update to v6.1 (Peter Xu)
- migration: simplify migration_iteration_run() (Juan Quintela)
- migration: Remove unused threshold_size parameter (Juan Quintela)
- migration: Split save_live_pending() into state_pending_* (Juan Quintela)
- migration: No save_live_pending() method uses the QEMUFile parameter (Juan Quintela)
- Revert "virtio-scsi: Send "REPORTED LUNS CHANGED" sense data upon disk hotplug events" (Karl Heubaum) [Orabug: 35161059]
- oslib-posix: initialize backend memory objects in parallel (Mark Kanda) [Orabug: 32555402]
- oslib-posix: refactor memory prealloc threads (Mark Kanda) [Orabug: 32555402]
- qemu-kvm.spec: vhost-user is conditional (Steve Sistare) 
- qemu-kvm.spec: libseccomp is conditional (Steve Sistare) 

* Mon Jan 30 2023 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-1.el9
- vl: Add an -action option to override MCE handling (Mark Kanda)
- hw/arm/virt: build SMBIOS 19 table (Mihai Carabas)
- virtio-net-pci: Don't use "efi-virtio.rom" on AArch64 (Mark Kanda)
- migration: increase listening socket backlog (Elena Ufimtseva)
- virtio: Set PCI subsystem vendor ID to Oracle (Karl Heubaum)
- Update to QEMU 7.2.0 (Karl Heubaum)

* Tue Sep 13 2022 Karl Heubaum <karl.heubaum@oracle.com> - 6.1.1-4.el9
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

* Fri Apr 8 2022 Karl Heubaum <karl.heubaum@oracle.com> - 6.1.1-3.el9
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

* Wed Mar 9 2022 Karl Heubaum <karl.heubaum@oracle.com> - 6.1.1-2.el9
- vhost-vsock: detach the virqueue element in case of error (Stefano Garzarella) [Orabug: 33941752] {CVE-2022-26354}
- qemu_regdump.py/qmp-regdump: Switch to Python 3 (Karl Heubaum)
- block/mirror: fix NULL pointer dereference in mirror_wait_on_conflicts() (Stefano Garzarella) [Orabug: 33916572] {CVE-2021-4145}

* Fri Feb 25 2022 Karl Heubaum <karl.heubaum@oracle.com> - 6.1.1-1.el9
- ACPI ERST: step 6 of bios-tables-test.c (Eric DeVolder)
- ACPI ERST: bios-tables-test testcase (Eric DeVolder)
- ACPI ERST: qtest for ERST (Eric DeVolder)
- ACPI ERST: create ACPI ERST table for pc/x86 machines (Eric DeVolder)
- ACPI ERST: build the ACPI ERST table (Eric DeVolder)
- ACPI ERST: support for ACPI ERST feature (Eric DeVolder)
- ACPI ERST: header file for ERST (Eric DeVolder)
- ACPI ERST: PCI device_id for ERST (Eric DeVolder)
- hw/nvme: fix CVE-2021-3929 (Klaus Jensen) [Orabug: 33866395] {CVE-2021-3929}
- oslib-posix: initialize backend memory objects in parallel (Mark Kanda) [Orabug: 32555402]
- oslib-posix: refactor memory prealloc threads (Mark Kanda) [Orabug: 32555402]
- tests/plugin/syscall.c: fix compiler warnings (Juro Bystricky)
- virtio-net-pci: Don't use "efi-virtio.rom" on AArch64 (Mark Kanda)
- migration: increase listening socket backlog (Elena Ufimtseva)
- virtio: Set PCI subsystem vendor ID to Oracle (Karl Heubaum)
- virtiofsd: Drop membership of all supplementary groups (CVE-2022-0358) (Vivek Goyal) [Orabug: 33816690] {CVE-2022-0358}
- acpi: validate hotplug selector on access (Michael S. Tsirkin) [Orabug: 33816625] {CVE-2021-4158}
- Update to QEMU 6.1.1 (Karl Heubaum)
