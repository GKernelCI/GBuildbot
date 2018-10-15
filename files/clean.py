#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shelve
import subprocess


def command(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True,
                            universal_newlines=True)
    for line in proc.stdout:
        a = line.strip('')
        print(a)

conf_var = "files/shelve"
d = shelve.open(conf_var)
packages = d["version"]
d.close()

# filter for Manifest files
packages = [v for v in packages if "Manifest" not in v]
gentoo_repo = 'gentoo/'

# remove any existing script
if os.path.isfile('ebuild_unmerge.sh'):
    os.unlink('ebuild_unmerge.sh')

# write script header shebang
cmd_echo = 'echo "#!/bin/sh" > ebuild_unmerge.sh'
command(cmd_echo)

# Do the Thing ...
# 1) build the ebuild script
for package in packages:
    print("Cleaning package: {0}".format(package))
    ebuild_location = gentoo_repo + package
    ebuild_full = "ROOT=kernel_sources/ /usr/bin/ebuild " + ebuild_location
    ebuild_unmerge = ebuild_full + ' unmerge '
    print("  {0}".format(ebuild_unmerge))
    cmd_echo = 'echo "' + ebuild_unmerge + '" >> ebuild_unmerge.sh'
    command(cmd_echo)

# 2) execute it
cmd_echo = 'chmod +x ebuild_unmerge.sh'
command(cmd_echo)
command('./ebuild_unmerge.sh')
