#!/usr/bin/env python3
#
# qemu_regdump.py
#
# sosreport plugin to invoke qmp-regdump on QEMU virtual machines
#
# Copyright (C) 2017, Oracle and/or its affiliates. All rights reserved.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms and conditions of the GNU General Public
# License, version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; If not, see <http://www.gnu.org/licenses/>.


import os
import re
import platform


try:
    # Try to load SOS 3 API
    from sos.plugins import Plugin, RedHatPlugin
except ImportError:
    # Failed import, revert to 1.x/2.2 SOS API: alias the Plugin and
    # RedHatPlugin classes to the old PluginBase class
    import sos.plugintools
    Plugin = RedHatPlugin = sos.plugintools.PluginBase


class qemu_regdump(Plugin, RedHatPlugin):
    """
    QEMU monitor VM register dump

    """
    plugin_name = 'qemu_regdump'
    version = '1.0'

    option_list = [
        ('path', 'path to QMP dump script', '', '/usr/bin/qmp-regdump'),
        ('socket', 'QMP socket (unix or TCP)', '', ''),
        ('kernel', 'location of VM vmlinux kernel file', '', ''),
        ('mapfile', 'location of VM System.map file', '', ''),
    ]

    def setup(self):
        path = self.get_option('path')
        socket = self.get_option('socket')
        kernel = self.get_option('kernel')
        mapfile = self.get_option('mapfile')

        if platform.machine() == 'x86_64':
            qemu_paths = ['/usr/libexec/qemu-kvm',
                          '/usr/bin/qemu-system-x86_64']
        elif platform.machine() == 'aarch64':
            qemu_paths = ['/usr/libexec/qemu-kvm',
                          '/usr/bin/qemu-system-aarch64']
        else:
            self.add_custom_text('Unsupported platform: %s\n'
                                 % platform.machine())
            return

        for qemu_bin in qemu_paths:
            if os.path.exists(qemu_bin):
                break
        else:
            self.add_custom_text('No QEMU binary found')
            return

        # capture QEMU version
        self.add_cmd_output(qemu_bin + ' --version',
                            suggest_filename='qemu-version')

        # check if QMP regdump script exists
        if not os.path.isfile(path):
            self.add_alert('qmp-regdump tool \'%s\' not found' % path)
            return

        # a user might symlink one of the 'qemu_paths' to another, so when
        # parsing the cmdline, check for all
        qemu_bin_regex = '|'.join(qemu_paths)

        if socket:
            sockets = [socket]
        else:
            # find all QMP sockets
            sockets = []
            pids = []

            for proc_file in os.listdir('/proc'):
                if proc_file.isdigit():
                    pids.append(proc_file)

            for pid in pids:
                try:
                    with open(os.path.join('/proc', pid, 'cmdline')) as fd:
                        cmdline = fd.read()
                        qmp = re.search(
                            r'(%s).*-qmp.*(unix|tcp):([^\0,]*)'
                            % qemu_bin_regex, cmdline)
                        if qmp:
                            sockets.append(qmp.group(3))
                        if not qmp:
                            # -mon [chardev=]name,mode=control
                            mon = re.search(
                                r'(%s).*-mon\0(.*mode=control[^\0]*)'
                                % qemu_bin_regex, cmdline)
                            if mon:
                                mon_dev = re.search(r'.*chardev=([^\0,]*)',
                                                    mon.group(2))
                                if mon_dev:
                                    mon_dev = mon_dev.group(1)
                                else:
                                    mon_dev = mon.group(2).split(',')[0]

                                # find the corresponding chardev
                                # -chardev socket,id=id,path=path..
                                # -chardev socket,id=id,host=host,port=port..
                                chardev = re.search(
                                    r'.*(-chardev\0socket(?=.*id=%s)'
                                    '[^\0]*(path=|host=)([^\0,]*)[^\0]*)'
                                    % mon_dev, cmdline)

                                if chardev and chardev.group(2) == 'path=':
                                    sockets.append(chardev.group(3))
                                elif chardev and chardev.group(2) == 'host=':
                                    host = chardev.group(3)
                                    port = re.search(r'.*port=([^\0,]*)',
                                                     chardev.group(1))
                                    if port:
                                        sockets.append(host + ':' +
                                                       port.group(1))
                except IOError:
                    # process has already terminated
                    continue

        if not sockets:
            self.add_custom_text('No QEMU processes with QMP sockets found')
            return

        cmd = path

        if kernel:
            cmd += ' -k %s ' % kernel
        if mapfile:
            cmd += ' -m %s ' % mapfile

        for socket in sockets:
            sockcmd = cmd + ' -s ' + socket
            self.add_cmd_output(sockcmd,
                                suggest_filename='qmp-regdump-%s' % socket)
