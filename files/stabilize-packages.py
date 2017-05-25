#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import subprocess
import shelve

print ('Number of arguments:', len(sys.argv), 'arguments.')
print ('Argument List:', str(sys.argv))

packages = sys.argv[1:]
gentoo_repo = '../gentoo/'

def command(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    for line in proc.stdout:
        a=(line.strip(''))
        print(a)

conf_var = "shelve"
d= shelve.open(conf_var)
d["version"] = []

for package in packages: 
    ebuild_location = gentoo_repo + package  
    ebuild_full = '/usr/bin/ebuild ' + ebuild_location
    ebuild_manifest = ebuild_full + ' manifest'
    ebuild_merge = ebuild_full + ' merge '

    command('echo "'+ebuild_manifest+'" > ebuild_manifest.sh && chmod +x ebuild_manifest.sh')
    command('echo "'+ebuild_merge+'" > ebuild_merge.sh && chmod +x ebuild_merge.sh')
    command('./ebuild_merge.sh')
    command('./ebuild_manifest.sh')
    package_version = package.replace("sys-kernel/gentoo-sources/gentoo-sources-","")
    package_version = package_version.replace(".ebuild","")
    print(package_version)
    d["version"].append(package_version)

d.close()
