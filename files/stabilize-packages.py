#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import shelve
import subprocess

packages = sys.argv[1:]
# filter out Manifest files
packages = [v for v in packages if "Manifest" not in v]

gentoo_repo = '../gentoo/'
versions = []


def run_command(cmd, trigger_text):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True,
                            universal_newlines=True)
    not_found = True
    for line in proc.stdout:
        a = line.strip()
        print(a)
        if trigger_text in str(a):
            not_found = False
    return not_found


# write script headers
with open('ebuild_merge.sh', 'w') as ebuild_merge:
    ebuild_merge.write("#!/bin/sh\n")
    ebuild_merge.write("set -e\n")

with open('ebuild_manifest.sh', 'w') as ebuild_manifest:
    ebuild_manifest.write("#!/bin/sh\n")
    ebuild_manifest.write("set -e\n")


ebuild_manifest = open("ebuild_manifest.sh", 'a')
ebuild_merge = open("ebuild_merge.sh", 'a')
for package in packages:
    # .sort(key=lambda s: [int(u) for u in s.split('.')]):
    print("Processing: {0}".format(package))
    ebuild_location = gentoo_repo + package
    ebuild_full = 'ROOT=kernel_sources/ /usr/bin/ebuild ' + ebuild_location
    print("  {0}".format(ebuild_full))

    ebuild_manifest.write(ebuild_full + ' clean manifest\n')
    ebuild_merge.write(ebuild_full + ' install\n')

    versions.append(package)
ebuild_manifest.close()
ebuild_merge.close()

# make scripts executable
os.chmod('ebuild_merge.sh', 0o755)
os.chmod('ebuild_manifest.sh', 0o755)

# run the built scripts ...
result = run_command('./ebuild_manifest.sh', 'Error')
if result is False:
    print("Manifest generation failed")
    sys.exit(1)

result = run_command('./ebuild_merge.sh', 'Error')
if result is False:
    print("Emerging failed")
    sys.exit(1)

conf_var = "shelve"
d = shelve.open(conf_var)
d["version"] = versions
d.close()
