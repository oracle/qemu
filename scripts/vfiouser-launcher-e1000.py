#!/usr/bin/env python3
import socket
import os
import subprocess
import time

PROC_QEMU='/home/qemu-separation/qemu-split/build/x86_64-softmmu/qemu-system-x86_64'

if os.path.exists("/tmp/remotesock"):
    os.remove("/tmp/remotesock")

remote_cmd = [ PROC_QEMU,                                                                                \
               '-machine', 'x-remote,vfio-user=on',                                                      \
               '-device', 'e1000,netdev=net0,mac=C0:C0:C0:C1:2A:C7,id=ether1',                           \
               '-netdev', 'tap,id=net0',                                                                 \
               '-nographic',                                                                             \
               '-monitor', 'unix:/home/rem-sock,server,nowait',                                          \
               '-object', 'x-vfio-user-server,id=vfioobj1,type=unix,path=/tmp/remotesock,device=ether1', \
             ]

proxy_cmd = [ PROC_QEMU,                                                                                \
              '-name', 'OL7.4',                                                                         \
              '-machine', 'pc,accel=kvm',                                                               \
              '-smp', 'sockets=1,cores=1,threads=1',                                                    \
              '-m', '2048',                                                                             \
              '-object', 'memory-backend-memfd,id=sysmem-file,size=2G',                                 \
              '-numa', 'node,memdev=sysmem-file',                                                       \
              '-device', 'virtio-scsi-pci,id=virtio_scsi_pci0',                                         \
              '-drive', 'id=drive_image1,if=none,format=qcow2,'                                         \
                            'file=/home/ol7-hdd-1.qcow2',                                               \
              '-device', 'scsi-hd,id=image1,drive=drive_image1,'                                        \
                             'bus=virtio_scsi_pci0.0',                                                  \
              '-boot', 'd',                                                                             \
              '-vnc', ':0',                                                                             \
              '-device', 'vfio-user-pci,socket=/tmp/remotesock',                                        \
              '-monitor', 'unix:/home/qemu-sock,server,nowait',                                         \
            ]

pid = os.fork();

if pid:
    # In Proxy
    time.sleep(3)
    print('Launching QEMU with Proxy object');
    process = subprocess.Popen(proxy_cmd)
else:
    # In remote
    print('Launching Remote process');
    process = subprocess.Popen(remote_cmd)
