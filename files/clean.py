#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import shelve


def command(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    for line in proc.stdout:
        a = line.strip('')
        print(a)

conf_var = "files/shelve"
d = shelve.open(conf_var)
packages = d["version"]
d.close()

# filter manifest files
packages = [v for v in packages if not "Manifest" in v]
gentoo_repo = 'gentoo/'

for package in packages:
    ebuild_location = gentoo_repo + package
    ebuild_full = '/usr/bin/ebuild ' + ebuild_location
    ebuild_unmerge = ebuild_full + ' unmerge '
    command('echo "'+ebuild_unmerge+'" > ebuild_unmerge.sh && chmod +x ebuild_unmerge.sh')
    command('./ebuild_unmerge.sh')