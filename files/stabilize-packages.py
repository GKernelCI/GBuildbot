#!/usr/bin/env python
import sys
import subprocess

print ('Number of arguments:', len(sys.argv), 'arguments.')
print ('Argument List:', str(sys.argv))

packages = sys.argv[1:]
gentoo_repo = '../gentoo/'

def command(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    for line in proc.stdout:
        a=(line.strip('\n'))
        print(a)


for package in packages: 
    ebuild_location = gentoo_repo + package  
    ebuild_full = 'ebuild ' + ebuild_location
    ebuild_manifest = ebuild_full + ' manifest'
    ebuild_merge = ebuild_full + ' merge '

    command(ebuild_manifest)
    command(ebuild_merge)
