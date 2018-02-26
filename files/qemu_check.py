#!/usr/bin/env python
import subprocess
import sys
from threading import Timer
import os.path
import shelve

conf_var = "shelve"
d = shelve.open(conf_var)
vmlinuz_list = d["version"]
d.close()

qemu_timeout = 120
vmimage = '/tmp/gentoo.qcow2'
BaseURI = 'http://gentoo.osuosl.org/experimental/amd64/openstack/'\
          'gentoo-openstack-amd64-default-'
SnapshotDate = 'latest'


def command(cmd, timeout_sec):
    work = False
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    kill_proc = lambda p: p.kill()
    timer = Timer(timeout_sec, kill_proc, [proc])
    try:
        timer.start()
        for line in proc.stdout:
            a = line.strip()
            print(a)
            if 'This is localhost' in str(a):
                work = True
                break
    finally:
        timer.cancel()
    proc.kill()
    return work

isfile = os.path.isfile(vmimage)
if not isfile:
    ImageURI = BaseURI + SnapshotDate + '.qcow2'
    cmd_wget = 'wget -N ' + ImageURI + ' -O ' + vmimage
    proc2 = subprocess.Popen(cmd_wget, stdout=subprocess.PIPE, shell=True)
    for line in proc2.stdout:
        a = line.strip()
        print(a)
else:
    print("vmimage present: " + vmimage)

print(vmlinuz_list)

if isinstance(vmlinuz_list, str):
    vmlinuz_list = [vmlinuz_list]

for vmlinuz in vmlinuz_list:
    print(vmlinuz)
    cmd_qemu = 'qemu-system-x86_64 -m 128M -kernel ' \
        'linux-*/arch/x86/boot/bzImage' \
        ' -nographic -serial mon:stdio -hda ' + vmimage + \
        ' -append "root=/dev/sda1 console=ttyS0,115200n8 console=tty0"'
    work = command(cmd_qemu, qemu_timeout)
    if work:
        print("worked")
    else:
        print("failed")
        sys.exit(1)
