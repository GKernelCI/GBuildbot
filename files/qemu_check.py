#!/usr/bin/env python
import sys
import os.path
import shelve
import subprocess
from threading import Timer

if len(sys.argv) < 4:
    print("Usage: qemu_check.py <arch> <builder> <build#>")
    sys.exit(1)
# arch = "amd64" if len(sys.argv) < 4 else sys.argv[1]

arch = sys.argv[1]
build_id = sys.argv[3]
if (arch in sys.argv[2]):
    builder = sys.argv[2].split(':')[0]
else:
    builder = sys.argv[2]


conf_var = "shelve"
d = shelve.open(conf_var)
vmlinuz_list = d["version"]
d.close()

qemu_timeout = 360
SnapshotDate = 'latest'
BaseURIamd64 = 'http://gentoo.osuosl.org/experimental/amd64/openstack/'
amd64img = 'gentoo-openstack-amd64-default-' + SnapshotDate + '.qcow2'
BaseURIarm32 = ''
arm32img = ''
BaseURIarm64 = ''
arm64img = ''


def command(cmd, timeout_sec):
    work = False
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    kill_proc = lambda p: p.kill()
    timer = Timer(timeout_sec, kill_proc, [proc])
    try:
        timer.start()
        for line in proc.stdout:
            print(line.strip())
            if 'This is localhost' in str(line.strip()):
                work = True
                # break
    finally:
        timer.cancel()
    proc.kill()
    return work

# Set up some variables depending on arch
if arch == 'amd64':
    ImageURI = BaseURIamd64 + amd64img
    vmimage_src = amd64img
    vmimage_dest = "gentoo-amd64-" + builder + "-b" + build_id + ".qcow2"
    cmd_qemu = 'qemu-system-x86_64 -m 128M -kernel ' \
        'linux-amd64-build/arch/x86/boot/bzImage' \
        ' -nographic -serial mon:stdio -hda /tmp/' + vmimage_dest + \
        ' -append "root=/dev/sda1 console=ttyS0,115200n8 console=tty0"'
elif arch == 'arm':
    ImageURI = BaseURIarm + arm32img
    vmimage_src = arm32img
    vmimage_dest = "gentoo-arm-" + builder + "-b" + build_id + ".qcow2"
    cmd_qemu = 'qemu-system-arm -M vexpress-a9 -smp 2 -m 1G -kernel ' \
        'linux-arm-build/arch/arm/boot/zImage' \
        ' -dtb linux-arm-build/arch/arm/boot/dts/vexpress-v2p-ca9.dtb' \
        ' -sd /tmp/' + vmimage_dest + ' -nographic -append ' \
        '"console=ttyAMA0,115200 root=/dev/mmcblk0 rootwait"'

# Check for existing base image, download if needed
if not os.path.isfile('/tmp/' + vmimage_src):
    cmd_wget = 'wget -Nc ' + ImageURI + ' -P /tmp'
    proc2 = subprocess.Popen(cmd_wget, stdout=subprocess.PIPE, shell=True)
    for line in proc2.stdout:
        print(line.strip())
    if not os.path.isfile('/tmp/' + vmimage_src):
        print("Cannot download file: " + ImageURI)
        sys.exit(1)
else:
    print("vmimage present: " + vmimage_src)

# Create snapshot of base image for build
cmd_clone_qemu_img = 'qemu-img create -f qcow2 -b /tmp/' + vmimage_src + \
                     ' /tmp/' + vmimage_dest
proc2 = subprocess.Popen(cmd_clone_qemu_img, stdout=subprocess.PIPE,
                         shell=True)
for line in proc2.stdout:
    print(line.strip())

# Print [imported] list of kernels to build
print(vmlinuz_list)

if isinstance(vmlinuz_list, str):
    vmlinuz_list = [vmlinuz_list]

# Build the kernels...
for vmlinuz in vmlinuz_list:
    print(vmlinuz)
    work = command(cmd_qemu, qemu_timeout)
    if work:
        print("worked")
    else:
        print("failed")
        sys.exit(1)
