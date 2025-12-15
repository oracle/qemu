
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
# USB redirection
%global have_usb_redir 0
# USB passthrough
%global have_usb_host 1
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

# Support for static user mode emulation
%ifarch x86_64
%global have_user_static 1
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
Release: 32%{?dist}
Epoch: 31
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
%if 0%{?have_usb_host}
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

%if 0%{?have_user_static}
BuildRequires:  glibc-static
BuildRequires:  glib2-static
BuildRequires:  pcre-static
BuildRequires:  zlib-static
BuildRequires:  libstdc++-static
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
%if 0%{?have_usb_redir}
Requires: libusbx >= 1.0.23
Requires: usbredir >= 0.8.0
BuildRequires: usbredir-devel >= 0.8.0
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

%if 0%{?have_usb_redir}
%package -n qemu-kvm-device-usb-redirect
Summary: QEMU USB redirection support
%description -n qemu-kvm-device-usb-redirect
This package provides USB redirection support.
%endif

%if 0%{?have_usb_host}
%package -n qemu-kvm-device-usb-host
Summary: QEMU USB host device
%description -n qemu-kvm-device-usb-host
This package provides the USB pass through driver for QEMU.
%endif

%if 0%{?have_user_static}
%package -n qemu-user-static-aarch64
Summary: QEMU static user mode emulation for aarch64
%description -n qemu-user-static-aarch64
QEMU static user mode emulation for aarch64

%package -n qemu-user-static-mips
Summary: QEMU static user mode emulation for mips
%description -n qemu-user-static-mips
QEMU static user mode emulation for mips
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

%if 0%{?have_usb_redir}
    %global usbredirflags --enable-usb-redir
%else
    %global usbredirflags --disable-usb-redir
%endif

%if 0%{?have_usb_host}
    %global usbhostflags --enable-libusb
%else
    %global usbhostflags --disable-libusb
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

%global isal_major %(readelf -d %{_libdir}/libisal_crypto.so | grep SONAME | sed 's/.*\.so\.\([0-9]\+\)].*/\1/')

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
    --disable-libkeyutils \
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
    %{usbredirflags} \
    %{usbhostflags} \
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
    %{vduseblkexportflags} \
    --isal-major=%{isal_major}

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

%if 0%{?have_user_static}
%global build_dir_static build-static
mkdir -p %{build_dir_static}
pushd %{build_dir_static}

../configure \
    --enable-user \
    --disable-system \
    --disable-tools \
    --static \
    --enable-tcg \
    --enable-pie \
    --target-list="aarch64-linux-user,mips-linux-user,mips64-linux-user, \
    mips64el-linux-user,mipsel-linux-user,mipsn32-linux-user,mipsn32el-linux-user"

%make_build

popd
%endif

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
rm -rf %{buildroot}%{_datadir}/%{name}/multiboot_dma.bin
%endif

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

%if 0%{?have_user_static}
%global build_archs aarch64 mips mips64 mips64el mipsel mipsn32 mipsn32el

for i in %{build_archs}; do
    mv %{build_dir_static}/qemu-${i} %{build_dir_static}/qemu-${i}-static
    install -m 0755 %{build_dir_static}/qemu-${i}-static %{buildroot}%{_bindir}
done

# Install binfmt
%global binfmt_dir %{buildroot}%{_exec_prefix}/lib/binfmt.d
mkdir -p %{binfmt_dir}

for i in %{build_archs}; do
    ./scripts/qemu-binfmt-conf.sh --systemd ${i} --exportdir %{binfmt_dir} \
	--qemu-path %{_bindir} --qemu-suffix -static --persistent yes
done

for i in %{binfmt_dir}/*; do
    mv $i $(echo $i | sed 's/.conf/-static.conf/')
done
%endif

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

%if 0%{?have_user_static}
%post -n qemu-user-static-aarch64
/bin/systemctl --system try-restart systemd-binfmt.service &>/dev/null || :

%post -n qemu-user-static-mips
/bin/systemctl --system try-restart systemd-binfmt.service &>/dev/null || :

%postun -n qemu-user-static-aarch64
/bin/systemctl --system try-restart systemd-binfmt.service &>/dev/null || :

%postun -n qemu-user-static-mips
/bin/systemctl --system try-restart systemd-binfmt.service &>/dev/null || :
%endif

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
%{_bindir}/elf2dmp
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
    %{_datadir}/%{name}/multiboot_dma.bin
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

%if 0%{?have_usb_redir}
%files -n qemu-kvm-device-usb-redirect
%{_libdir}/%{name}/hw-usb-redirect.so
%endif

%if 0%{?have_usb_host}
%files -n qemu-kvm-device-usb-host
%{_libdir}/%{name}/hw-usb-host.so
%endif

%if 0%{?have_user_static}
%files -n qemu-user-static-aarch64
%{_bindir}/qemu-aarch64-static
%{_exec_prefix}/lib/binfmt.d/qemu-aarch64-static.conf

%files -n qemu-user-static-mips
%{_bindir}/qemu-mips-static
%{_bindir}/qemu-mips64-static
%{_bindir}/qemu-mips64el-static
%{_bindir}/qemu-mipsel-static
%{_bindir}/qemu-mipsn32-static
%{_bindir}/qemu-mipsn32el-static
%{_exec_prefix}/lib/binfmt.d/qemu-mips-static.conf
%{_exec_prefix}/lib/binfmt.d/qemu-mips64-static.conf
%{_exec_prefix}/lib/binfmt.d/qemu-mips64el-static.conf
%{_exec_prefix}/lib/binfmt.d/qemu-mipsel-static.conf
%{_exec_prefix}/lib/binfmt.d/qemu-mipsn32-static.conf
%{_exec_prefix}/lib/binfmt.d/qemu-mipsn32el-static.conf
%endif

%changelog
* Wed Jan 14 2026 Elena Ufimtseva <elena.ufimtseva@oracle.com> - 7.2.0-32.el9
- migration: find the major version (ABI) of the libisal_crypto library to pass to configure

* Tue Dec 23 2025 Mark Kanda <mark.kanda@oracle.com> - 7.2.0-32.el9
- spec: Provide aarch64 and mips user static packages (Mark Kanda)
  These packages are for Oracle internal use only (not for external customers)
- cpu: Only compile runstate_is_running() for system mode (Mark Kanda)
- linux-user: Do not define struct sched_attr if libc headers do (Khem Raj)

* Tue Dec 9 2025 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-31.el9
- migration: Fix the cancellation/error path (Elena Ufimtseva) [Orabug: 38739293]

* Wed Dec 3 2025 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-30.el9
- live migration: scan and clear contiguous dirty pages regions of ram (Elena Ufimtseva) [Orabug: 38388170]
- migration: add hash_rate trace point (Elena Ufimtseva) [Orabug: 38388170]
- migration: add parameter to specify max number of contiguous pages (Elena Ufimtseva) [Orabug: 38388170]
- multifd: send more pages then IOV_MAX (Elena Ufimtseva) [Orabug: 38388170]
- io: fix use after free in websocket handshake code (Daniel P. Berrangé) [Orabug: 38687831] {CVE-2025-11234}

* Fri Oct 24 2025 Mark Kanda <mark.kanda@oracle.com> - 7.2.0-29.el9
- hw/core/machine.c: Add vhost-scsi-pci num_queues = 1 to hw_compat_7_2_exadata (Greg Jumper) [Orabug: 38544462]
- target/i386/kvm: account blackout downtime for kvm-clock and guest TSC (Dongli Zhang) [Orabug: 38307402]
- cpus: resume hotplugged vCPU only when the guest is running (Dongli Zhang) [Orabug: 38307402]
- system/qdev-monitor: move drain_call_rcu call under if (!dev) in qmp_device_add() (Dmitrii Gavrilov) [Orabug: 38298220]
- acpi: pcihp: allow repeating hot-unplug requests (Igor Mammedov) [Orabug: 38257990]
- hw/usb/hcd-uhci: don't assert for SETUP to non-0 endpoint (Peter Maydell) [Orabug: 37517799] {CVE-2024-8354}
- target/i386: Introduce GraniteRapids-v2 model (Tao Su) [Orabug: 38330786]
- target/i386: Add AVX512 state when AVX10 is supported (Tao Su) [Orabug: 38330786]
- target/i386: Add feature dependencies for AVX10 (Tao Su) [Orabug: 38330786]
- target/i386: add CPUID.24 features for AVX10 (Tao Su) [Orabug: 38330786]
- target/i386: add AVX10 feature and AVX10 version property (Tao Su) [Orabug: 38330786]
- target/i386: return bool from x86_cpu_filter_features (Paolo Bonzini) [Orabug: 38330786]
- target/i386: do not rely on ExtSaveArea for accelerator-supported XCR0 bits (Paolo Bonzini) [Orabug: 38330786]
- target/i386: Call accel-agnostic x86_cpu_get_supported_cpuid() (Philippe Mathieu-Daudé) [Orabug: 38330786]
- target/i386: Add new CPU model GraniteRapids (Tao Su) [Orabug: 38330786]

* Tue Sep 9 2025 Mark Kanda <mark.kanda@oracle.com> - 7.2.0-28.el9
- hw/i386: Add an exadata machine (Joao Martins) [Orabug: 38408711]
- arm/kvm: add support for MTE (Cornelia Huck)
- target/arm: When tag memory is not present, set MTE=1 (Richard Henderson)
- spec: provide qemu-kvm-device-usb-host package (Mark Kanda) [Orabug: 38355110]
- kvm.conf: do not automatically enable virt when loading kvm (Mark Kanda) [Orabug: 38320046]

* Wed Aug 6 2025 Mark Kanda <mark.kanda@oracle.com> - 7.2.0-26.el9
- accel/kvm: Enable Dirty bit tracking if hash cache is used (Joao Martins) [Orabug: 37699414]
- migration/page_cache: Add nettle sha256 function (Elena Ufimtseva) [Orabug: 37699414]
- migration/page_cache: Add libgcrypt sha256 function (Elena Ufimtseva) [Orabug: 37699414]
- migration/page_cache: Add gnutls sha256 function (Joao Martins) [Orabug: 37699414]
- migration: Add a parameter to select sha256 library (Joao Martins) [Orabug: 37699414]
- migration: Export cache statistics to QMP (Joao Martins) [Orabug: 37699414]
- migration/ram: Adjust estimate/exact to time-to-hash dirty data (Joao Martins) [Orabug: 37699414]
- migration: Sync dirty bitmap in exact() considering factor (Joao Martins) [Orabug: 37699414]
- migration: Time cache hit/miss operations (Joao Martins) [Orabug: 37699414]
- migration/ram: Calculate real dirty pages based on hash cache stats (Elena Ufimtseva) [Orabug: 37699414]
- migration: Add hash cache for dirty page tracking (Elena Ufimtseva) [Orabug: 37699414]
- migration/page-cache: Differentiate page size from cache data size (Joao Martins) [Orabug: 37699414]
- target/i386: do not expose ARCH_CAPABILITIES on AMD CPU (Paolo Bonzini) [Orabug: 38225280]

* Tue Jul 8 2025 Mark Kanda <mark.kanda@oracle.com> - 7.2.0-24.el9
- Revert "migration: Temporarily re-enable our custom switchover event by default" (Mark Kanda)
- target/i386: Enumerate verw-clear CPUID feature (Boris Ostrovsky) [Orabug: 38118557] {CVE-2024-36350} {CVE-2024-36357}

* Wed Jun 25 2025 Mark Kanda <mark.kanda@oracle.com> - 7.2.0-23.el9
- vhost-scsi: support VIRTIO_SCSI_F_HOTPLUG (Dongli Zhang) [Orabug: 38113473]

* Fri Jun 13 2025 Mark Kanda <mark.kanda@oracle.com> - 7.2.0-22.el9
- migration/multifd: Don't send device state packets with zerocopy flag (Maciej S. Szmigiero) [Orabug: 37372623]
- migration/dirtyrate: skip kvm_log_start/kvm_log_stop for non-KVM (Dongli Zhang) [Orabug: 37939813]

* Fri May 16 2025 Mark Kanda <mark.kanda@oracle.com> - 7.2.0-21.el9
- migration: Temporarily re-enable our custom switchover event by default (Maciej S. Szmigiero)

* Wed May 7 2025 Mark Kanda <mark.kanda@oracle.com> - 7.2.0-20.el9
- Document CVEs as not applicable to QEMU 7.2.0 (Mark Kanda) [Orabug: 36869706] [Orabug: 36620547] [Orabug: 37043479] {CVE-2024-3567} {CVE-2024-4693} {CVE-2024-7730}
- target/i386: Remove rtm, hle and taa-no from the Sapphire Rapids CPU model (Mark Kanda) [Orabug: 37867203]
- target/i386: Reset parked vCPUs together with the online ones (Maciej S. Szmigiero)
- migration: Add capability for our custom switchover event (Maciej S. Szmigiero)
- iotests: Disable ones that hang (Maciej S. Szmigiero)
- vfio/migration: Use BE byte order for device state wire packets (Maciej S. Szmigiero)
- vfio/migration: Make x-migration-multifd-transfer VFIO property mutable (Maciej S. Szmigiero)
- vfio/migration: Add x-migration-multifd-transfer VFIO property (Maciej S. Szmigiero)
- vfio/migration: Multifd device state transfer support - send side (Maciej S. Szmigiero)
- vfio/migration: Multifd device state transfer support - config loading support (Maciej S. Szmigiero)
- migration/qemu-file: Define g_autoptr() cleanup function for QEMUFile (Maciej S. Szmigiero)
- vfio/migration: Multifd device state transfer support - load thread (Maciej S. Szmigiero)
- vfio/migration: Multifd device state transfer support - received buffers queuing (Maciej S. Szmigiero)
- vfio/migration: Setup and cleanup multifd transfer in these general methods (Maciej S. Szmigiero)
- vfio/migration: Multifd setup/cleanup functions and associated VFIOMultifd (Maciej S. Szmigiero)
- vfio/migration: Multifd device state transfer - add support checking function (Maciej S. Szmigiero)
- vfio/migration: Multifd device state transfer support - basic types (Maciej S. Szmigiero)
- vfio/migration: Move migration channel flags to vfio-common.h header file (Maciej S. Szmigiero)
- vfio/migration: Add vfio_add_bytes_transferred() (Maciej S. Szmigiero)
- vfio/migration: Convert bytes_transferred counter to atomic (Maciej S. Szmigiero)
- vfio/migration: Add load_device_config_state_start trace event (Maciej S. Szmigiero)
- migration: Add save_live_complete_precopy_thread handler (Maciej S. Szmigiero)
- migration/multifd: Add multifd_device_state_supported() (Maciej S. Szmigiero)
- migration/multifd: Make MultiFDSendData a struct (Peter Xu)
- migration/multifd: Device state transfer support - send side (Maciej S. Szmigiero)
- migration/multifd: Add an explicit MultiFDSendData destructor (Maciej S. Szmigiero)
- migration/multifd: Make multifd_send() thread safe (Maciej S. Szmigiero)
- migration/multifd: Device state transfer support - receive side (Maciej S. Szmigiero)
- migration/multifd: Split packet into header and RAM data (Maciej S. Szmigiero)
- migration: Add thread pool of optional load threads (Maciej S. Szmigiero)
- error: define g_autoptr() cleanup function for the Error type (Maciej S. Szmigiero)
- migration: Always take BQL for migration_incoming_state_destroy() (Maciej S. Szmigiero)
- migration: Add qemu_loadvm_load_state_buffer() and its handler (Maciej S. Szmigiero)
- migration: Add MIG_CMD_SWITCHOVER_START and its load handler (Maciej S. Szmigiero)
- thread-pool: Implement generic (non-AIO) pool support (Maciej S. Szmigiero)
- thread-pool: Rename AIO pool functions to *_aio() and data types to *Aio (Maciej S. Szmigiero)
- thread-pool: Remove thread_pool_submit() function (Maciej S. Szmigiero)
- migration: Check migration error after loadvm (Fabiano Rosas)
- migration/multifd: Add a compat property for TLS termination (Fabiano Rosas)
- migration/multifd: Terminate the TLS connection (Fabiano Rosas)
- io: Add a read flag for relaxed EOF (Fabiano Rosas)
- io: Add flags argument to qio_channel_readv_full_all_eof (Fabiano Rosas)
- crypto: Remove qcrypto_tls_session_get_handshake_status (Fabiano Rosas)
- io: tls: Add qio_channel_tls_bye (Fabiano Rosas)
- crypto: Allow gracefully ending the TLS session (Fabiano Rosas)
- migration/multifd: Fix compat with QEMU < 9.0 (Fabiano Rosas)
- vfio/migration: Add vfio_save_block_precopy_empty_hit trace event (Maciej S. Szmigiero)
- vfio/migration: Add save_{iterate, complete_precopy}_start trace events (Maciej S. Szmigiero)
- migration/ram: Add load start trace event (Maciej S. Szmigiero)
- migration/multifd: Stop changing the packet on recv side (Fabiano Rosas)
- migration/multifd: Replace multifd_send_state->pages with client data (Fabiano Rosas)
- migration/multifd: Don't send ram data during SYNC (Fabiano Rosas)
- migration/multifd: Isolate ram pages packet data (Fabiano Rosas)
- migration/multifd: Remove total pages tracing (Fabiano Rosas)
- migration/multifd: Move pages accounting into multifd_send_zero_page_detect() (Fabiano Rosas)
- migration/multifd: Replace p->pages with an union pointer (Fabiano Rosas)
- migration/multifd: Make MultiFDPages_t:offset a flexible array member (Fabiano Rosas)
- migration/multifd: Introduce MultiFDSendData (Fabiano Rosas)
- migration/multifd: Remove pages->allocated (Fabiano Rosas)
- migration/multifd: Inline page_size and page_count (Fabiano Rosas)
- migration/multifd: Reduce access to p->pages (Fabiano Rosas)
- migration/multifd: Decouple recv method from pages (Fabiano Rosas)
- migration/multifd: Rename MultiFDSend|RecvParams::data to compress_data (Fabiano Rosas)
- migration/multifd: Change multifd_pages_init argument (Fabiano Rosas)
- migration: Introduce migrate_has_error() (Peter Xu)
- test-vmstate: fix bad GTree usage, use-after-free (Eric Auger)
- Revert "vfio/migration: Add save_{iterate,complete_precopy}_started trace events" (Maciej S. Szmigiero)
- Revert "migration/ram: Add load start trace event" (Maciej S. Szmigiero)
- Revert "migration: Add save_live_complete_precopy_{begin,end} handlers" (Maciej S. Szmigiero)
- Revert "migration: Add qemu_loadvm_load_state_buffer() and its handler" (Maciej S. Szmigiero)
- Revert "migration: Add load_finish handler and associated functions" (Maciej S. Szmigiero)
- Revert "migration/multifd: Device state transfer support - receive side" (Maciej S. Szmigiero)
- Revert "migration/multifd: Convert multifd_send_pages::next_channel to atomic" (Maciej S. Szmigiero)
- Revert "migration/multifd: Device state transfer support - send side" (Maciej S. Szmigiero)
- Revert "migration/multifd: Add migration_has_device_state_support()" (Maciej S. Szmigiero)
- Revert "vfio/migration: Multifd device state transfer support - receive side" (Maciej S. Szmigiero)
- Revert "vfio/migration: Add x-orcl-migration-multifd-transfer VFIO property" (Maciej S. Szmigiero)
- Revert "vfio/migration: Multifd device state transfer support - send side" (Maciej S. Szmigiero)
- target/i386: fix feature dependency for WAITPKG (Paolo Bonzini) [Orabug: 35941551]
- target/i386: add support for VMX_SECONDARY_EXEC_ENABLE_USER_WAIT_PAUSE (Ake Koomsin) [Orabug: 35941551]
- vhost-scsi: Add support for a worker thread per virtqueue (Mike Christie) [Orabug: 37723795]
- vhost: Add worker backend callouts (Mike Christie) [Orabug: 37723795]
- linux-headers: update vhost related headers to v6.5-rc1 (Mark Kanda) [Orabug: 37723795]
- system/physmem: poisoned memory discard on reboot (William Roche) [Orabug: 34545034]
- system/physmem: handle hugetlb correctly in qemu_ram_remap() (William Roche) [Orabug: 34545034]
- qemu-kvm.spec: Ship multiboot_dma.bin (Liam Merwick) [Orabug: 37593199]
- target/i386: Change unavail from u32 to u64 (Xiong Zhang) [Orabug: 37560962]
- vfio/pci: Add x-device-dirty-page-tracking param (Joao Martins)

* Mon Jan 13 2025 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-18.el9
- tests: acpi: update expected blobs (Igor Mammedov) [Orabug: 37274182]
- cpuhp: make sure that remove events are handled within the same SCI (Igor Mammedov) [Orabug: 37274182]
- tests: acpi: whitelist expected blobs (Igor Mammedov) [Orabug: 37274182]
- target/i386: Reset TSCs of parked vCPUs too on VM reset (Maciej S. Szmigiero) [Orabug: 37318424]
- 9pfs: fix regression regarding CVE-2023-2861 (Christian Schoenebeck) [Orabug: 37409273]
- virtio-net: Ensure queue index fits with RSS (Akihiko Odaki) [Orabug: 36943011] {CVE-2024-6505}
- qemu-kvm.spec: pack elf2dmp tool (Annie Li)
- test: bios-tables-test: add IVRS changed binary (Bui Quang Minh) [Orabug: 35710551]
- amd_iommu: Fix kvm_enable_x2apic link error with clang in non-KVM builds (Sairaj Kodilkar) [Orabug: 35710551]
- amd_iommu: Check APIC ID > 255 for XTSup (Suravee Suthikulpanit) [Orabug: 35710551]
- amd_iommu: Send notification when invalidate interrupt entry cache (Suravee Suthikulpanit) [Orabug: 35710551]
- amd_iommu: Use shared memory region for Interrupt Remapping (Suravee Suthikulpanit) [Orabug: 35710551]
- amd_iommu: Add support for pass though mode (Suravee Suthikulpanit) [Orabug: 35710551]
- amd_iommu: Rename variable mmio to mr_mmio (Suravee Suthikulpanit) [Orabug: 35710551]
- hw/i386/amd_iommu: Don't leak memory in amdvi_update_iotlb() (Peter Maydell) [Orabug: 35710551]
- amd_iommu: report x2APIC support to the operating system (Bui Quang Minh) [Orabug: 35710551]
- hw/i386/amd_iommu: Do not use SysBus API to map local MMIO region (Philippe Mathieu-Daudé) [Orabug: 35710551]
- amd_iommu: Fix APIC address check (Akihiko Odaki) [Orabug: 35710551]
- hw/i386/amd_iommu: Factor amdvi_pci_realize out of amdvi_sysbus_realize (Philippe Mathieu-Daudé) [Orabug: 35710551]
- hw/i386/amd_iommu: Set PCI static/const fields via PCIDeviceClass (Philippe Mathieu-Daudé) [Orabug: 35710551]
- hw/i386/amd_iommu: Move capab_offset from AMDVIState to AMDVIPCIState (Philippe Mathieu-Daudé) [Orabug: 35710551]
- hw/i386/amd_iommu: Remove intermediate AMDVIState::devid field (Philippe Mathieu-Daudé) [Orabug: 35710551]
- hw/i386/amd_iommu: Explicit use of AMDVI_BASE_ADDR in amdvi_init (Philippe Mathieu-Daudé) [Orabug: 35710551]

* Wed Oct 16 2024 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-17.el9
- target/i386: add feature bits for Inception/SRSO mitigations (Mark Kanda) [Orabug: 37170148]
- hw/vfio/pci-quirks: Sanitize capability pointer (Alex Williamson) [Orabug: 37176213]
- hw/vfio/pci-quirks: Support alternate offset for GPUDirect Cliques (Alex Williamson) [Orabug: 37176213]
- migration/dirtyrate: Add new mode to dirty track non KVM device separately (Joao Martins) [Orabug: 37097510]
- vfio/migration: Allow dirty tracking reports with MIGRATION_STATUS_NONE (Joao Martins) [Orabug: 37097510]
- migration: Emit event when source starts switchover (Joao Martins) [Orabug: 37097503]

* Tue Oct 1 2024 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-16.el9
- block: fix failing assert on paused VM migration (Andrey Drobyshev) [Orabug: 37106834]
- migration/multifd: Fix rb->receivedmap cleanup race (Fabiano Rosas) [Orabug: 36932320]
- migration/savevm: Remove extra load cleanup calls (Fabiano Rosas) [Orabug: 36932320]
- migration: fix switchover abort termination paths (Elena Ufimtseva) [Orabug: 36932320]
- nbd/server: CVE-2024-7409: Avoid use-after-free when closing server (Eric Blake) [Orabug: 36921582] {CVE-2024-7409}
- nbd/server: CVE-2024-7409: Close stray clients at server-stop (Eric Blake) [Orabug: 36921582] {CVE-2024-7409}
- nbd/server: CVE-2024-7409: Drop non-negotiating clients (Eric Blake) [Orabug: 36921582] {CVE-2024-7409}
- nbd/server: CVE-2024-7409: Cap default max-connections to 100 (Eric Blake) [Orabug: 36921582] {CVE-2024-7409}
- nbd/server: Plumb in new args to nbd_client_add() (Eric Blake) [Orabug: 36921582] {CVE-2024-7409}
- nbd: Minor style and typo fixes (Eric Blake) [Orabug: 36921582] {CVE-2024-7409}
- scsi-disk: Always report RESERVATION_CONFLICT to guest (Kevin Wolf)
- scsi-disk: Add warning comments that host_status errors take a shortcut (Kevin Wolf)
- scsi-block: Don't skip callback for sgio error status/driver_status (Kevin Wolf)
- scsi-disk: Use positive return value for status in dma_readv/writev (Kevin Wolf)
- target/i386: Add new CPU model SierraForest (Tao Su)
- target/i386: Add few security fix bits in ARCH_CAPABILITIES into SapphireRapids CPU model (Lei Wang)
- target/i386: Add new bit definitions of MSR_IA32_ARCH_CAPABILITIES (Tao Su)
- target/i386: Allow MCDT_NO if host supports (Tao Su)
- target/i386: Add support for MCDT_NO in CPUID enumeration (Tao Su)
- target/i386: Adjust feature level according to FEAT_7_1_EDX (Tao Su)
- target/i386: Export MSR_ARCH_CAPABILITIES bits to guests (Pawan Gupta)
- target/i386: Add support for PREFETCHIT0/1 in CPUID enumeration (Jiaxi Chen)
- target/i386: Add support for AVX-NE-CONVERT in CPUID enumeration (Jiaxi Chen)
- target/i386: Add support for AVX-VNNI-INT8 in CPUID enumeration (Jiaxi Chen)
- target/i386: Add support for AVX-IFMA in CPUID enumeration (Jiaxi Chen)
- target/i386: Add support for AMX-FP16 in CPUID enumeration (Jiaxi Chen)
- target/i386: Add support for CMPCCXADD in CPUID enumeration (Jiaxi Chen)
- i386: Add new CPU model SapphireRapids (Wang, Lei)
- target/i386: KVM: allow fast string operations if host supports them (Paolo Bonzini)
- target/i386: add FZRM, FSRS, FSRC (Paolo Bonzini)
- spec: disable keyutils (Mark Kanda) [Orabug: 36903731]
- meson.build: Make keyutils independent from keyring (Thomas Huth) [Orabug: 36903731]

* Wed Jul 31 2024 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-15.el9
- migration: abort on destination if switchover limit exceeded (Elena Ufimtseva)
- migration: introduce strict switchover SLA (Elena Ufimtseva)
- migration: add error to MigrationIncomingState (Elena Ufimtseva)
- migration: Set migration status early in incoming side (Fabiano Rosas)
- tests/qtest: migration: Use migrate_incoming_qmp where appropriate (Fabiano Rosas)
- tests/qtest: migration: Add migrate_incoming_qmp helper (Fabiano Rosas)
- tests/qtest: migration: Expose migrate_set_capability (Fabiano Rosas)
- vfio/migration: Multifd device state transfer support - send side (Maciej S. Szmigiero)
- vfio/migration: Add x-orcl-migration-multifd-transfer VFIO property (Maciej S. Szmigiero)
- vfio/migration: Multifd device state transfer support - receive side (Maciej S. Szmigiero)
- migration/multifd: Add migration_has_device_state_support() (Maciej S. Szmigiero)
- migration/multifd: Device state transfer support - send side (Maciej S. Szmigiero)
- migration/multifd: Convert multifd_send_pages::next_channel to atomic (Maciej S. Szmigiero)
- migration/multifd: Device state transfer support - receive side (Maciej S. Szmigiero)
- migration: Add load_finish handler and associated functions (Maciej S. Szmigiero)
- migration: Add qemu_loadvm_load_state_buffer() and its handler (Maciej S. Szmigiero)
- migration: Add save_live_complete_precopy_{begin,end} handlers (Maciej S. Szmigiero)
- migration/multifd: Zero p->flags before starting filling a packet (Maciej S. Szmigiero)
- migration/ram: Add load start trace event (Maciej S. Szmigiero)
- vfio/migration: Add save_{iterate,complete_precopy}_started trace events (Maciej S. Szmigiero)
- hw/virtio/virtio-crypto: Protect from DMA re-entrancy bugs (Philippe Mathieu-Daudé) [Orabug: 36869694] {CVE-2024-3446}
- hw/char/virtio-serial-bus: Protect from DMA re-entrancy bugs (Philippe Mathieu-Daudé) [Orabug: 36869694] {CVE-2024-3446}
- hw/display/virtio-gpu: Protect from DMA re-entrancy bugs (Philippe Mathieu-Daudé) [Orabug: 36869694] {CVE-2024-3446}
- hw/virtio: Introduce virtio_bh_new_guarded() helper (Philippe Mathieu-Daudé) [Orabug: 36869694] {CVE-2024-3446}
- pcie_sriov: Validate NumVFs (Akihiko Odaki) [Orabug: 36314082] {CVE-2024-26327}
- hw/nvme: Use pcie_sriov_num_vfs() (Akihiko Odaki) [Orabug: 36314111] {CVE-2024-26328}
- pcie: Introduce pcie_sriov_num_vfs (Akihiko Odaki) [Orabug: 36314111] {CVE-2024-26328}
- qcow2: Don't open data_file with BDRV_O_NO_IO (Kevin Wolf) [Orabug: 36801853] {CVE-2024-4467}
- target/i386: drop AMD machine check bits from Intel CPUID (Paolo Bonzini) [Orabug: 36785079]
- target/i386: pass X86CPU to x86_cpu_get_supported_feature_word (Paolo Bonzini) [Orabug: 36785079]
- migration: prevent migration when VM has poisoned memory (William Roche) [Orabug: 35533097]
- i386: Add support for overflow recovery (John Allen) [Orabug: 34691766]
- i386: Add support for SUCCOR feature (John Allen) [Orabug: 34691766]
- i386: Fix MCE support for AMD hosts (John Allen) [Orabug: 34691766]

* Mon Jun 17 2024 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-13.el9
- vfio/migration: Enhance VFIO migration state tracing (Avihai Horon)
- vfio/migration: Don't emit STOP_COPY VFIO migration QAPI event twice (Avihai Horon)
- vfio/migration: Emit VFIO migration QAPI event (Avihai Horon)
- qapi/vfio: Add VFIO migration QAPI event (Avihai Horon)
- migration/multifd: solve zero page causing multiple page faults (Yuan Liu) [Orabug: 36727051]
- multifd: Add the ramblock to MultiFDRecvParams (Lukas Straub) [Orabug: 36727051]
- migration: Fix qmp_query_migrate mbps value (Fabiano Rosas) [Orabug: 36727104]
- migration: Allow user to specify available switchover bandwidth (Peter Xu) [Orabug: 35636284]
- migration/dirtyrate: Fix precision losses and g_usleep overshoot (Andrei Gudkov) [Orabug: 36727091]
- Use new created qemu_target_pages_to_MiB() (Juan Quintela) [Orabug: 36727091]
- softmmu: Create qemu_target_pages_to_MiB() (Juan Quintela) [Orabug: 36727091]
- migration/calc-dirty-rate: replaced CRC32 with xxHash (Andrei Gudkov) [Orabug: 36727063]
- migration/multifd: Enable multifd zero page checking by default. (Hao Xiang) [Orabug: 34131170]
- migration/multifd: Implement ram_save_target_page_multifd to handle multifd version of MigrationOps::ram_save_target_page. (Hao Xiang) [Orabug: 34131170]
- migration/multifd: Implement zero page transmission on the multifd thread. (Hao Xiang) [Orabug: 34131170]
- migration/multifd: Add new migration option zero-page-detection. (Hao Xiang) [Orabug: 34131170]
- migration: Make ram_save_target_page() a pointer (Juan Quintela) [Orabug: 34131170]
- migration: Yield bitmap_mutex properly when sending/sleeping (Peter Xu) [Orabug: 34131170]
- migration/multifd: Add a synchronization point for channel creation (Fabiano Rosas) [Orabug: 34131170]
- migration/multifd: Unify multifd and TLS connection paths (Fabiano Rosas) [Orabug: 34131170]
- migration/multifd: Move multifd_send_setup into migration thread (Fabiano Rosas) [Orabug: 34131170]
- migration/multifd: Move multifd_send_setup error handling in to the function (Fabiano Rosas) [Orabug: 34131170]
- migration/multifd: Remove p->running (Fabiano Rosas) [Orabug: 34131170]
- migration/multifd: Optimize sender side to be lockless (Peter Xu) [Orabug: 34131170]
- migration/multifd: Join the TLS thread (Fabiano Rosas) [Orabug: 34131170]
- migration/multifd: Fix MultiFDSendParams.packet_num race (Peter Xu) [Orabug: 34131170]
- migration/multifd: Stick with send/recv on function names (Peter Xu) [Orabug: 34131170]
- migration/multifd: Cleanup multifd_load_cleanup() (Peter Xu) [Orabug: 34131170]
- migration/multifd: Cleanup multifd_save_cleanup() (Peter Xu) [Orabug: 34131170]
- migration/multifd: Rewrite multifd_queue_page() (Peter Xu) [Orabug: 34131170]
- migration/multifd: Change retval of multifd_send_pages() (Peter Xu) [Orabug: 34131170]
- migration/multifd: Change retval of multifd_queue_page() (Peter Xu) [Orabug: 34131170]
- migration/multifd: Split multifd_send_terminate_threads() (Peter Xu) [Orabug: 34131170]
- migration/multifd: Forbid spurious wakeups (Peter Xu) [Orabug: 34131170]
- migration/multifd: Move header prepare/fill into send_prepare() (Peter Xu) [Orabug: 34131170]
- migration/multifd: multifd_send_prepare_header() (Peter Xu) [Orabug: 34131170]
- migration/multifd: Move trace_multifd_send|recv() (Peter Xu) [Orabug: 34131170]
- migration/multifd: Move total_normal_pages accounting (Peter Xu) [Orabug: 34131170]
- migration/multifd: Rename p->num_packets and clean it up (Peter Xu) [Orabug: 34131170]
- migration/multifd: Drop pages->num check in sender thread (Peter Xu) [Orabug: 34131170]
- migration/multifd: Simplify locking in sender thread (Peter Xu) [Orabug: 34131170]
- migration/multifd: Separate SYNC request with normal jobs (Peter Xu) [Orabug: 34131170]
- migration/multifd: Drop MultiFDSendParams.normal[] array (Peter Xu) [Orabug: 34131170]
- migration/multifd: Postpone reset of MultiFDPages_t (Peter Xu) [Orabug: 34131170]
- migration/multifd: Remove MultiFDPages_t::packet_num (Fabiano Rosas) [Orabug: 34131170]
- migration/multifd: Drop MultiFDSendParams.quit, cleanup error paths (Peter Xu) [Orabug: 34131170]
- migration/multifd: multifd_send_kick_main() (Peter Xu) [Orabug: 34131170]
- migration/multifd: Fix leaking of Error in TLS error flow (Avihai Horon) [Orabug: 34131170]
- migration/ram: Merge save_zero_page functions (Fabiano Rosas) [Orabug: 34131170]
- migration/ram: Move xbzrle zero page handling into save_zero_page (Fabiano Rosas) [Orabug: 34131170]
- migration/multifd: Stop setting p->ioc before connecting (Fabiano Rosas) [Orabug: 34131170]
- migration: Centralize BH creation and dispatch (Fabiano Rosas) [Orabug: 34131170]
- migration: Add a wrapper to qemu_bh_schedule (Fabiano Rosas) [Orabug: 34131170]
- migration: Remove transferred atomic counter (Juan Quintela) [Orabug: 35636284]
- migration: Use migration_transferred_bytes() (Juan Quintela) [Orabug: 35636284]
- migration: migration_rate_limit_reset() don't need the QEMUFile (Juan Quintela) [Orabug: 35636284]
- migration: migration_transferred_bytes() don't need the QEMUFile (Juan Quintela) [Orabug: 35636284]
- multifd: reset next_packet_len after sending pages (Elena Ufimtseva) [Orabug: 35636284]
- multifd: fix counters in multifd_send_thread (Elena Ufimtseva) [Orabug: 35636284]
- migration/multifd: Compute transferred bytes correctly (Juan Quintela) [Orabug: 35636284]
- migration: check for rate_limit_max for RATE_LIMIT_DISABLED (Elena Ufimtseva) [Orabug: 35636284]
- migration: Use the number of transferred bytes directly (Juan Quintela) [Orabug: 35636284]
- qemu_file: Use a stat64 for qemu_file_transferred (Juan Quintela) [Orabug: 35636284]
- migration: set file error on subsection loading (Marc-André Lureau) [Orabug: 35636284]
- migration: Receiving a zero page non zero is an error (Juan Quintela) [Orabug: 35636284]
- migration/multifd: Stop checking p->quit in multifd_send_thread (Fabiano Rosas) [Orabug: 35636284]
- migration/multifd: Clarify Error usage in multifd_channel_connect (Fabiano Rosas) [Orabug: 35636284]
- multifd: cleanup the function multifd_channel_connect (Li Zhang) [Orabug: 35636284]
- migration/multifd: Unify multifd_send_thread error paths (Fabiano Rosas) [Orabug: 35636284]
- migration: Non multifd migration don't care about multifd flushes (Juan Quintela) [Orabug: 35636284]
- migration: fix RAMBlock add NULL check (Dmitry Frolov) [Orabug: 35829153]
- migration: We don't need the field rate_limit_used anymore (Juan Quintela) [Orabug: 35636284]
- migration: Use migration_transferred_bytes() to calculate rate_limit (Juan Quintela) [Orabug: 35636284]
- migration: Add a trace for migration_transferred_bytes (Juan Quintela) [Orabug: 35636284]
- migration: Move migration_total_bytes() to migration-stats.c (Juan Quintela) [Orabug: 35636284]
- qemu-file: Remove total from qemu_file_total_transferred_*() (Juan Quintela) [Orabug: 35636284]
- migration: Move rate_limit_max and rate_limit_used to migration_stats (Juan Quintela) [Orabug: 35636284]
- qemu-file: Account for rate_limit usage on qemu_fflush() (Juan Quintela) [Orabug: 35636284]
- migration: Don't use INT64_MAX for unlimited rate (Juan Quintela) [Orabug: 35636284]
- qemu-file: Make rate_limit_used an uint64_t (Juan Quintela) [Orabug: 35636284]
- qemu-file: make qemu_file_[sg]et_rate_limit() use an uint64_t (Juan Quintela) [Orabug: 35636284]
- migration: We set the rate_limit by a second (Juan Quintela) [Orabug: 35829153]
- migration: A rate limit value of 0 is valid (Juan Quintela) [Orabug: 35636284]
- qemu-file: Make ram_control_save_page() use accessors for rate_limit (Juan Quintela) [Orabug: 35636284]
- qemu-file: Make total_transferred an uint64_t (Juan Quintela) [Orabug: 35636284]
- qemu-file: No need to check for shutdown in qemu_file_rate_limit (Juan Quintela) [Orabug: 35636284]
- migration: Document all migration_stats (Juan Quintela) [Orabug: 35636284]
- multifd: We already account for this packet on the multifd thread (Juan Quintela) [Orabug: 35636284]
- migration: Make dirty_bytes_last_sync atomic (Juan Quintela) [Orabug: 35636284]
- migration: Make dirty_pages_rate atomic (Juan Quintela) [Orabug: 35636284]
- stat64: Add stat64_set() operation (Paolo Bonzini) [Orabug: 35636284]
- multifd: Only flush once each full round of memory (Juan Quintela) [Orabug: 35636284]
- migration: Make find_dirty_block() return a single parameter (Juan Quintela) [Orabug: 35636284]
- migration: Simplify ram_find_and_save_block() (Juan Quintela) [Orabug: 35636284]
- multifd: Protect multifd_send_sync_main() calls (Juan Quintela) [Orabug: 35636284]
- multifd: Create property multifd-flush-after-each-section (Juan Quintela) [Orabug: 35636284]
- multifd: Fix the number of channels ready (Juan Quintela) [Orabug: 35636284]
- migration: Rename normal to normal_pages (Juan Quintela) [Orabug: 35636284]
- migration: Rename duplicate to zero_pages (Juan Quintela) [Orabug: 35636284]
- migration: Make dirty_sync_count atomic (Juan Quintela) [Orabug: 35636284]
- migration: Make downtime_bytes atomic (Juan Quintela) [Orabug: 35636284]
- migration: Make precopy_bytes atomic (Juan Quintela) [Orabug: 35636284]
- migration: Make dirty_sync_missed_zero_copy atomic (Juan Quintela) [Orabug: 35636284]
- migration: Make multifd_bytes atomic (Juan Quintela) [Orabug: 35636284]
- migration: Update atomic stats out of the mutex (Juan Quintela) [Orabug: 35636284]
- migration: Merge ram_counters and ram_atomic_counters (Juan Quintela) [Orabug: 35636284]
- migration/multifd: correct multifd_send_thread to trace the flags (Wei Wang) [Orabug: 35636284]
- ram: Document migration ram flags (Juan Quintela) [Orabug: 35636284]
- migration: Calculate ram size once (Juan Quintela) [Orabug: 35636284]
- multifd: Fix a race on reading MultiFDPages_t.block (Zhenzhong Duan) [Orabug: 35636284]
- migration: Use atomic ops properly for page accountings (Peter Xu) [Orabug: 35636284]
- migration: Export ram_release_page() (Juan Quintela) [Orabug: 35636284]
- migration: Export ram_transferred_ram() (Juan Quintela) [Orabug: 35636284]
- multifd: Create page_count fields into both MultiFD{Recv,Send}Params (Juan Quintela) [Orabug: 35636284]
- multifd: Create page_size fields into both MultiFD{Recv,Send}Params (Juan Quintela) [Orabug: 35636284]
- migration: Fix migration_channel_read_peek() error path () (Avihai Horon) [Orabug: 36726827]
- migration/multifd: Remove error_setg() in migration_ioc_process_incoming() (Avihai Horon) [Orabug: 36726827]
- migration: Refactor migration_incoming_setup() (Avihai Horon) [Orabug: 36726827]
- migration: check magic value for deciding the mapping of channels (manish.mishra) [Orabug: 36726827]
- io: Add support for MSG_PEEK for socket channel (manish.mishra) [Orabug: 36726827]
- hw/sd/sdhci: Do not update TRNMOD when Command Inhibit (DAT) is set (hilippe Mathieu-Daudé) [Orabug: 36575206] {CVE-2024-3447}
- block: lock AioContext in bdrv_replace_child_noperm() when in non-coroutine context (Mark Kanda) [Orabug: 36514180]
- hw/scsi/scsi-generic: Fix io_timeout property not applying (Lorenz Brun) [Orabug: 36637684]
- target/i386/monitor: synchronize cpu state for lapic info (Dongli Zhang) [Orabug: 36607747]
- qemu_init: increase NOFILE soft limit on POSIX (Fiona Ebner) [Orabug: 36416389]

* Thu Mar 7 2024 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-11.el9
- vfio/migration: Add a note about migration rate limiting (Avihai Horon) [Orabug: 36329758]
- vfio/migration: Refactor vfio_save_state() return value (Avihai Horon) [Orabug: 36329758]
- migration: Don't serialize devices in qemu_savevm_state_iterate() (Avihai Horon) [Orabug: 36329758]
- ui/clipboard: add asserts for update and request (Fiona Ebner) [Orabug: 36323175] {CVE-2023-6683}
- ui/clipboard: mark type as not available when there is no data (Fiona Ebner) [Orabug: 36323175] {CVE-2023-6683}
- virtio-net: correctly copy vnet header when flushing TX (Jason Wang) [Orabug: 36154459] {CVE-2023-6693}
- esp: restrict non-DMA transfer length to that of available data (Mark Cave-Ayland) [Orabug: 36322141] {CVE-2024-24474}
- vhost: Perform memory section dirty scans once per iteration (Si-Wei Liu)
- vhost: dirty log should be per backend type (Si-Wei Liu)
- net: Update MemReentrancyGuard for NIC (Akihiko Odaki) [Orabug: 35644197] {CVE-2023-3019}
- net: Provide MemReentrancyGuard * to qemu_new_nic() (Akihiko Odaki) [Orabug: 35644197] {CVE-2023-3019}
- lsi53c895a: disable reentrancy detection for MMIO region, too (Thomas Huth) [Orabug: 33774027] {CVE-2021-3750}
- memory: stricter checks prior to unsetting engaged_in_io (Alexander Bulekov) [Orabug: 33774027] {CVE-2021-3750}
- async: avoid use-after-free on re-entrancy guard (Alexander Bulekov) [Orabug: 33774027] {CVE-2021-3750}
- apic: disable reentrancy detection for apic-msi (Alexander Bulekov) [Orabug: 33774027] {CVE-2021-3750}
- raven: disable reentrancy detection for iomem (Alexander Bulekov) [Orabug: 33774027] {CVE-2021-3750}
- bcm2835_property: disable reentrancy detection for iomem (Alexander Bulekov) [Orabug: 33774027] {CVE-2021-3750}
- lsi53c895a: disable reentrancy detection for script RAM (Alexander Bulekov) [Orabug: 33774027] {CVE-2021-3750}
- hw: replace most qemu_bh_new calls with qemu_bh_new_guarded (Alexander Bulekov) [Orabug: 33774027] {CVE-2021-3750}
- checkpatch: add qemu_bh_new/aio_bh_new checks (Alexander Bulekov) [Orabug: 33774027] {CVE-2021-3750}
- async: Add an optional reentrancy guard to the BH API (Alexander Bulekov) [Orabug: 33774027] {CVE-2021-3750}
- memory: prevent dma-reentracy issues (Alexander Bulekov) [Orabug: 33774027] {CVE-2021-3750}
- hw/acpi: propagate vcpu hotplug after switch to modern interface (Aaron Young)
- migration: Fix use-after-free of migration state object (Fabiano Rosas) [Orabug: 36242218]
- kvm: Fix crash due to access uninitialized kvm_state (Gavin Shan) [Orabug: 36269244]
- migration: Avoid usage of static variable inside tracepoint (Joao Martins)
- migration: Add tracepoints for downtime checkpoints (Peter Xu)
- migration: migration_stop_vm() helper (Peter Xu)
- migration: Add per vmstate downtime tracepoints (Peter Xu)
- migration: Add migration_downtime_start|end() helpers (Peter Xu)
- migration: Set downtime_start even for postcopy (Peter Xu)
- hv-balloon: implement pre-Glib 2.68 compatibility (Maciej S. Szmigiero)
- hw/i386/pc: Support hv-balloon (Maciej S. Szmigiero)
- qapi: Add HV_BALLOON_STATUS_REPORT event and its QMP query command (Maciej S. Szmigiero)
- qapi: Add query-memory-devices support to hv-balloon (Maciej S. Szmigiero)
- Add Hyper-V Dynamic Memory Protocol driver (hv-balloon) hot-add support (Maciej S. Szmigiero)
- Add Hyper-V Dynamic Memory Protocol driver (hv-balloon) base (Maciej S. Szmigiero)
- Add Hyper-V Dynamic Memory Protocol definitions (Maciej S. Szmigiero)
- memory-device: Drop size alignment check (David Hildenbrand)
- memory-device: Support empty memory devices (David Hildenbrand)
- memory,vhost: Allow for marking memory device memory regions unmergeable (David Hildenbrand)
- memory: Clarify mapping requirements for RamDiscardManager (David Hildenbrand)
- memory-device,vhost: Support automatic decision on the number of memslots (David Hildenbrand)
- vhost: Add vhost_get_max_memslots() (David Hildenbrand)
- kvm: Add stub for kvm_get_max_memslots() (David Hildenbrand)
- memory-device,vhost: Support memory devices that dynamically consume memslots (David Hildenbrand)
- memory-device: Track required and actually used memslots in DeviceMemoryState (David Hildenbrand)
- stubs: Rename qmp_memory_device.c to memory_device.c (David Hildenbrand)
- memory-device: Support memory devices with multiple memslots (David Hildenbrand)
- vhost: Return number of free memslots (David Hildenbrand)
- kvm: Return number of free memslots (David Hildenbrand)
- vhost: Remove vhost_backend_can_merge() callback (David Hildenbrand)
- vhost: Rework memslot filtering and fix "used_memslot" tracking (David Hildenbrand)
- virtio-md-pci: New parent type for virtio-mem-pci and virtio-pmem-pci (David Hildenbrand)
- migration/ram: Expose ramblock_is_ignored() as migrate_ram_is_ignored() (David Hildenbrand)
- virtio-mem: Skip most of virtio_mem_unplug_all() without plugged memory (David Hildenbrand)
- softmmu/physmem: Warn with ram_block_discard_range() on MAP_PRIVATE file mapping (David Hildenbrand)
- memory-device: Track used region size in DeviceMemoryState (David Hildenbrand)
- memory-device: Refactor memory_device_pre_plug() (David Hildenbrand)
- hw/i386/pc: Remove PC_MACHINE_DEVMEM_REGION_SIZE (David Hildenbrand)
- hw/i386/acpi-build: Rely on machine->device_memory when building SRAT (David Hildenbrand)
- hw/i386/pc: Use machine_memory_devices_init() (David Hildenbrand)
- hw/loongarch/virt: Use machine_memory_devices_init() (David Hildenbrand)
- hw/ppc/spapr: Use machine_memory_devices_init() (David Hildenbrand)
- hw/arm/virt: Use machine_memory_devices_init() (David Hildenbrand)
- memory-device: Introduce machine_memory_devices_init() (David Hildenbrand)
- memory-device: Unify enabled vs. supported error messages (David Hildenbrand)
- hw/scsi/scsi-disk: Disallow block sizes smaller than 512 [CVE-2023-42467] (Thomas Huth) [Orabug: 35808564] {CVE-2023-42467}
- tests/qtest: ahci-test: add test exposing reset issue with pending callback (Fiona Ebner) [Orabug: 35977245] {CVE-2023-5088}
- hw/ide: reset: cancel async DMA operation before resetting state (Fiona Ebner) [Orabug: 35977245] {CVE-2023-5088}

* Thu Dec 7 2023 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-7.el9
- vfio/common: Probe type1 iommu dirty tracking support (Joao Martins) [Orabug: 36024839]
- vfio/common: Allow disabling device dirty page tracking (Joao Martins) [Orabug: 36024839]

* Wed Oct 18 2023 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-6.el9
- hw/smbios: Fix core count in type4 (Zhao Liu) [Orabug: 35869694]
- hw/smbios: Fix thread count in type4 (Zhao Liu) [Orabug: 35869694]
- hw/smbios: Fix smbios_smp_sockets caculation (Zhao Liu) [Orabug: 35869694]
- machine: Add helpers to get cores/threads per socket (Zhao Liu) [Orabug: 35869694]
- migration/multifd: Move load_cleanup inside incoming_state_destroy (Leonardo Bras) [Orabug: 35829153]
- migration/multifd: Join all multifd threads in order to avoid leaks (Leonardo Bras) [Orabug: 35829153]
- migration/multifd: Remove unnecessary assignment on multifd_load_cleanup() (Leonardo Bras) [Orabug: 35829153]
- migration/multifd: Change multifd_load_cleanup() signature and usage (Leonardo Bras) [Orabug: 35829153]
- vfio/migration: Block VFIO migration with background snapshot (Avihai Horon)
- vfio/migration: Block VFIO migration with postcopy migration (Avihai Horon)
- migration: Add .save_prepare() handler to struct SaveVMHandlers (Avihai Horon)
- migration: Move more initializations to migrate_init() (Avihai Horon)
- vfio/migration: Fail adding device with enable-migration=on and existing blocker (Avihai Horon)
- migration: Add migration prefix to functions in target.c (Avihai Horon)
- vfio/migration: Allow migration of multiple P2P supporting devices (Avihai Horon)
- vfio/migration: Add P2P support for VFIO migration (Avihai Horon)
- vfio/migration: Refactor PRE_COPY and RUNNING state checks (Joao Martins)
- qdev: Add qdev_add_vm_change_state_handler_full() (Avihai Horon)
- sysemu: Add prepare callback to struct VMChangeStateEntry (Avihai Horon)
- vfio/migration: Move from STOP_COPY to STOP in vfio_save_cleanup() (Avihai Horon)
- hw/vfio: Add number of dirty pages to vfio_get_dirty_bitmap tracepoint (Joao Martins)
- exec/ram_addr: Return number of dirty pages in cpu_physical_memory_set_dirty_lebitmap() (Joao Martins)
- migration: fix populate_vfio_info (Steve Sistare)
- vfio/migration: Revert out of tree P2P support (Joao Martins)
- async: clarify usage of barriers in the polling case (Paolo Bonzini) [Orabug: 35871058]
- async: update documentation of the memory barriers (Paolo Bonzini) [Orabug: 35871058]
- physmem: add missing memory barrier (Paolo Bonzini) [Orabug: 35871058]
- qemu-coroutine-lock: add smp_mb__after_rmw() (Paolo Bonzini) [Orabug: 35871058]
- aio-wait: switch to smp_mb__after_rmw() (Paolo Bonzini) [Orabug: 35871058]
- edu: add smp_mb__after_rmw() (Paolo Bonzini) [Orabug: 35871058]
- qemu-thread-win32: cleanup, fix, document QemuEvent (Paolo Bonzini) [Orabug: 35871058]
- qemu-thread-posix: cleanup, fix, document QemuEvent (Paolo Bonzini) [Orabug: 35871058]
- qatomic: add smp_mb__before/after_rmw() (Paolo Bonzini) [Orabug: 35871058]
- dump: kdump-zlib data pages not dumped with pvtime/aarch64 (Dongli Zhang) [Orabug: 35777876]
- hw/smbios: fix field corruption in type 4 table (Julia Suvorova) [Orabug: 35756216]
- kvm: Atomic memslot updates (David Hildenbrand) [Orabug: 35728782]
- KVM: keep track of running ioctls (Emanuele Giuseppe Esposito) [Orabug: 35728782]
- accel: introduce accelerator blocker API (Emanuele Giuseppe Esposito) [Orabug: 35728782]

* Fri Aug 18 2023 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-5.el9
- virtio-crypto: verify src&dst buffer length for sym request (zhenwei pi) [Orabug: 35683774] {CVE-2023-3180}
- io: remove io watch if TLS channel is closed during handshake (Daniel P. Berrangé) [Orabug: 35683826] {CVE-2023-3354}
- ui/vnc-clipboard: fix infinite loop in inflate_buffer (CVE-2023-3255) (Mauro Matteo Cascella) [Orabug: 35683770] {CVE-2023-3255}
- hw/scsi/lsi53c895a: Fix reentrancy issues in the LSI controller (CVE-2023-0330) (Thomas Huth) [Orabug: 35683817] {CVE-2023-0330}
- vhost-vdpa: do not cleanup the vdpa/vhost-net structures if peer nic is present (Ani Sinha) [Orabug: 35649138] {CVE-2023-3301}
- qmp-regdump: use QMP command 'query-cpus-fast' (Mark Kanda)

* Thu Jul 13 2023 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-4.el9
- vfio/migration: Allow migration of multiple P2P supporting devices (Avihai Horon)
- vfio/migration: Add P2P support for VFIO migration (Avihai Horon)
- sysemu: Add pre VM state change callback (Avihai Horon)
- vfio/migration: Refactor PRE_COPY and RUNNING state checks (Joao Martins)
- vfio/common: Add an option to relax vIOMMU usage (Joao Martins)
- virtio-rng-pci: fix transitional migration compat for vectors (David Alan Gilbert) [Orabug: 35595177]
- virtio-rng-pci: fix migration compat for vectors (David Alan Gilbert) [Orabug: 35595177]
- vfio: Fix null pointer dereference bug in vfio_bars_finalize() (Avihai Horon)
- vfio/migration: Return bool type for vfio_migration_realize() (Zhenzhong Duan)
- vfio/migration: Remove print of "Migration disabled" (Zhenzhong Duan)
- vfio/migration: Free resources when vfio_migration_realize fails (Zhenzhong Duan)
- vfio/migration: Change vIOMMU blocker from global to per device (Zhenzhong Duan)
- vfio/pci: Disable INTx in vfio_realize error path (Zhenzhong Duan)
- vfio/pci: Free leaked timer in vfio_realize error path (Zhenzhong Duan)
- vfio/pci: Fix a segfault in vfio_realize (Zhenzhong Duan)
- vfio/migration: Make VFIO migration non-experimental (Avihai Horon)
- vfio/migration: Reset bytes_transferred properly (Avihai Horon)
- vfio/pci: Call vfio_prepare_kvm_msi_virq_batch() in MSI retry path (Shameer Kolothum)
- vfio/migration: Add support for switchover ack capability (Avihai Horon)
- vfio/migration: Add VFIO migration pre-copy support (Avihai Horon)
- vfio/migration: Store VFIO migration flags in VFIOMigration (Avihai Horon)
- vfio/migration: Refactor vfio_save_block() to return saved data size (Avihai Horon)
- tests: Add migration switchover ack capability test (Avihai Horon)
- migration: Enable switchover ack capability (Avihai Horon)
- migration: Implement switchover ack logic (Avihai Horon)
- migration: Add switchover ack capability (Avihai Horon)
- target/i386: Add EPYC-Genoa model to support Zen 4 processor series (Babu Moger) [Orabug: 35555649]
- target/i386: Add VNMI and automatic IBRS feature bits (Babu Moger) [Orabug: 35555649]
- target/i386: Add missing feature bits in EPYC-Milan model (Babu Moger) [Orabug: 35555649]
- target/i386: Add feature bits for CPUID_Fn80000021_EAX (Babu Moger) [Orabug: 35555649]
- target/i386: Add a couple of feature bits in 8000_0008_EBX (Babu Moger) [Orabug: 35555649]
- target/i386: Add new EPYC CPU versions with updated cache_info (Michael Roth) [Orabug: 35555649]
- target/i386: allow versioned CPUs to specify new cache_info (Michael Roth) [Orabug: 35555649]
- target/i386/kvm: get and put AMD pmu registers (Dongli Zhang) [Orabug: 35562155]
- Makefile: qemu-bundle is a directory (Juan Quintela)
- 9pfs: prevent opening special files (CVE-2023-2861) (Christian Schoenebeck) [Orabug: 35570017] {CVE-2023-2861}
- pcie: Do not update hotplugged device power in RUN_STATE_INMIGRATE state (Annie Li) [Orabug: 33642532]
- pcie: Do not set power state for some hot-plugged devices (Annie Li) [Orabug: 33642532]
- pc: q35: Bump max_cpus to 1024 (Suravee Suthikulpanit) [Orabug: 35425619]

* Thu May 18 2023 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-3.el9
- vfio/migration: Skip log_sync during migration SETUP state (Avihai Horon) [Orabug: 35384144]
- migration: fix ram_state_pending_exact() (Juan Quintela) [Orabug: 35384144]

* Mon May 8 2023 Karl Heubaum <karl.heubaum@oracle.com> - 7.2.0-2.el9
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
