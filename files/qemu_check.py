#!/usr/bin/env python
import subprocess
import sys
from threading import Timer
import os.path
import shelve

conf_var = "shelve"
d= shelve.open(conf_var)
vmlinuz_list = d["version"]
d.close()

vmimage = '/tmp/gentoo.qcow2'

def command(cmd, timeout_sec):
    work = False
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    kill_proc = lambda p: p.kill()
    timer = Timer(timeout_sec, kill_proc, [proc])
    try:
        timer.start()
        for line in proc.stdout:
            a=(line.strip())
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
    proc2 = subprocess.Popen('wget -N http://gentoo.osuosl.org/experimental/amd64/openstack/gentoo-openstack-amd64-defa\
ult-20170521.qcow2 -O '+ vmimage , stdout=subprocess.PIPE, shell=True)
    for line in proc2.stdout:
        a=(line.strip())
        print(a)
else:
    print("vmimage present: " + vmimage)

if isinstance(vmlinuz_list, str):
    vmlinuz_list = [vmlinuz_list]

for vmlinuz in vmlinuz_list:
    print(vmlinuz)
    work = command('qemu-system-x86_64 -m 128M -kernel /boot/vmlinuz-'+ vmlinuz +' -nographic -serial mon:stdio -hda '+ vmimage +' -append "root=/dev/sda1 console=ttyS0,115200n8 console=tty0"', 120)
    time.sleep(600)
    if work:
        print("worked")
    else:
        print("failed")
        sys.exit(1)
