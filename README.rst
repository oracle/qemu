==========================
Out-of-process QEMU README
==========================

This a clone of QEMU project: https://www.qemu.org/download/

This repo currently develops Out-of-process QEMU. Out-of-process QEMU
allows QEMU to attach device running remotely on a separate process.

The QEMU which runs the CPU and executes KVM ioctls is called the
client QEMU. The QEMU which emulates the devices remotely is called
the server. The server is also a QEMU instance which is a machine of
type 'TYPE_REMOTE_MACHINE'. The server exclusively emulates devices
and does not emulate CPUs.

The client and server interact using the vfio-user protocol. Please
refer to the following for the vfio-user protocol specification:
https://patchew.org/QEMU/20210414114122.236193-1-thanos.makatos@nutanix.com/

This repo. has both the client and server code. The server extends the
following vfio-user library implemented by Nutanix:
https://github.com/nutanix/libvfio-user.git

Please checkout scripts/vfiouser-launcher.py for a sample Orchestrator
which demonstrates how to use vfio-user with QEMU.
