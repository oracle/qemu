#!/usr/bin/env python3
import socket
import os
import subprocess
import time
import platform
import uuid
import getopt
import sys

boot_image = ''
test_image = ''

try:
    opts, args = getopt.getopt(sys.argv[1:], "hb:t:",["boot-image", "test-image"])
except getopt.GetoptError:
    print ('vfiouser-launcher.py -b <boot-image> -t <test-image>')
    sys.exit('error parting arguments')

for opt, arg in opts:
    if opt == '-h':
        print ('vfiouser-launcher.py -b <boot-image> -t <test-image>')
        sys.exit()
    elif opt in ("-b", "--boot-image"):
        boot_image = arg
    elif opt in ("-t", "--test-image"):
        test_image = arg

if boot_image == '':
    print('Please specify boot-image to launch the VM')
    sys.exit('usage: vfiouser-launcher.py -b <boot-image> -t <test-image>')

if test_image == '':
    print('Please specify test-image for the remote process')
    sys.exit('usage: vfiouser-launcher.py -b <boot-image> -t <test-image>')

proc_qemu = os.path.join(os.getcwd(), '../build/qemu-system-'+platform.machine())
if not os.path.exists(proc_qemu):
    sys.exit('unable to find QEMU binary '+proc_qemu)

sock_path = '/tmp/remotesock-'+str(uuid.uuid4())

if os.path.exists(sock_path):
    os.remove(sock_path)

server_cmd = [ proc_qemu,                                                             \
               '-machine', 'x-remote,vfio-user=on',                                   \
               '-device', 'megasas,id=sas1',                                          \
               '-drive', 'id=drive_image1,file='+test_image,                          \
               '-device', 'scsi-hd,id=drive1,drive=drive_image1,bus=sas1.0,'          \
                              'scsi-id=0',                                            \
               '-nographic',                                                          \
               '-monitor', 'unix:/home/rem-sock,server,nowait',                       \
               '-object', 'x-vfio-user-server,id=vfioobj1,'                           \
                              'type=unix,path='+sock_path+',device=sas1',             \
             ]

client_cmd = [ proc_qemu,                                                             \
              '-name', 'OL7.4',                                                       \
              '-machine', 'pc,accel=kvm',                                             \
              '-smp', '4',                                                            \
              '-m', '2048',                                                           \
              '-object', 'memory-backend-memfd,id=sysmem-file,size=2G',               \
              '-numa', 'node,memdev=sysmem-file',                                     \
              '-hda', boot_image,                                                     \
              '-vnc', ':0',                                                           \
              '-device', 'vfio-user-pci,socket='+sock_path,                           \
            ]


print('Launching QEMU server using libvfio-user library');
server = subprocess.Popen(server_cmd)
time.sleep(3)
print('Launching QEMU client using vfio-user protocol');
client = subprocess.Popen(client_cmd)
client.wait()
os.remove(sock_path)
