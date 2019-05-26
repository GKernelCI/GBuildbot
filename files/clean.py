#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import shelve
import subprocess


def run_command(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True,
                            stderr=subprocess.PIPE, universal_newlines=True)
    for line in proc.stdout:
        a = line.strip()
        print(a)

conf_var = "files/shelve"
d = shelve.open(conf_var)
packages = d["version"]
d.close()

# filter for Manifest files
packages = [v for v in packages if "Manifest" not in v]

# remove any existing script
if os.path.isfile('ebuild_unmerge.sh'):
    os.unlink('ebuild_unmerge.sh')

# write script headers
with open('ebuild_unmerge.sh', 'w') as ebuild_unmerge:
    ebuild_unmerge.write("#!/bin/sh\n")
    ebuild_unmerge.write("set -e\n")

# Do the Thing ...
# 1) build the ebuild script
ebuild_unmerge = open("ebuild_unmerge.sh", 'a')
for package in packages:
    ebuild_location = "gentoo/" + package
    print ("Checking for: {0}".format(ebuild_location))
    if not os.path.exists(ebuild_location):
        print("Skipping: {0}".format(package))
        continue
    print("Cleaning package: {0}".format(package))
    ebuild_full = "ROOT=kernel_sources /usr/bin/ebuild " + ebuild_location
    ebuild_cmd = ebuild_full + ' unmerge clean'
    print("  {0}".format(ebuild_cmd))
    ebuild_unmerge.write(ebuild_cmd)
ebuild_unmerge.close()

# 2) make script executable
os.chmod('ebuild_unmerge.sh', 0o755)

# 3) execute it
run_command('./ebuild_unmerge.sh')
