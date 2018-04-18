#!/usr/bin/env python
from __future__ import print_function

import argparse
import shelve
import shutil
import subprocess
import sys
import tarfile
import json

if sys.version_info.major == 3:
    from urllib.request import urlretrieve
    import lzma

    def extract(filename):
        with tarfile.open(filename) as tar:
            tar.extractall()

else:
    from urllib import urlretrieve
    from backports import lzma

    def extract(filename):
        with lzma.open(filename) as f, open(filename[:-3], 'wb') as fout:
            file_content = f.read()
            fout.write(file_content)
        with tarfile.open(filename[:-3]) as tar:
            tar.extractall()

from configparser import ConfigParser
import os
import stat
from os import walk
import re
import requests

conf_parser = argparse.ArgumentParser(
    # Turn off help, so we print all options in response to -h
    add_help=False
)
conf_parser.add_argument("-c", "--conf_file",
                         help="Specify config file", metavar="FILE")
args, remaining_argv = conf_parser.parse_known_args()
defaults = {
    "version": "4.9",
}
if args.conf_file:
    config = ConfigParser()
    config.read([args.conf_file])
    defaults = dict(config.items("Defaults"))

# Don't suppress add_help here so it will handle -h
parser = argparse.ArgumentParser(
    # Inherit options from config_parser
    parents=[conf_parser],
    # print script description with -h/--help
    description=__doc__,
    # Don't mess with format of description
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.set_defaults(**defaults)
parser.add_argument("-version", "--version", help="version number",
                    required=True)
args = parser.parse_args(remaining_argv)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def find_new_version(version_number, argument_version):
    version = version_number.split('.', 2)
    try:
        version = version[0] + '.' + version[1]
        if version == argument_version:
            return version_number
        else:
            pass
    except:
        pass


def chmod_ixusr(filename):
    print("chmod +x %s" % (filename))
    try:
        os.chmod(filename, stat.S_IXUSR)
    except OSError as err:
        print("%s: %s" % (err.filename, err.strerror))


urlretrieve("https://www.kernel.org/releases.json", "releases.json")
config = json.load(open("releases.json", 'r'))
all_releases = config['releases']

for release in all_releases:
    version_number = release['version']
    new_version_revision = find_new_version(version_number, args.version)
    if new_version_revision is not None:
        break

conf_var = "shelve"
d = shelve.open(conf_var)
d["version"] = new_version_revision
d.close()
print(new_version_revision)
new_version_split = new_version_revision.split('.', 2)
new_version = new_version_split[0] + '.' + new_version_split[1]
print("new version: " + new_version)


kernel_tarxz = "linux-" + new_version + ".tar.xz"
if os.path.exists(kernel_tarxz):
    if os.path.exists("linux-" + new_version):
        pass
    else:
        extract(kernel_tarxz)
else:
    urlretrieve("http://distfiles.gentoo.org/distfiles/" +
                kernel_tarxz, kernel_tarxz)
    extract(kernel_tarxz)

incremental = release["patch"]["incremental"] is not None
print("# %s incremental version" % ("is" if incremental else "not"))
patch_url = release["patch"]["incremental" if incremental else "full"]
patch_name = patch_url.split("/")[-1]
print(patch_url)
urlretrieve(patch_url, patch_name)
with lzma.open(patch_name) as f, open(
        patch_name[:-3], 'wb') as fout:
    file_content = f.read()
    fout.write(file_content)


mypath = "../linux-patches/"

f = []
for (dirpath, dirnames, filenames) in walk(mypath):
    f.extend(filenames)
    break

patch_found = 0
for i in filenames:
    if new_version in i:
        print("we already have last patch: " + i)
        patch_found = 1

if patch_found == 0:
    shutil.move(patch_name[:-3], '../linux-patches/' +
                patch_name[:-3] + '.patch')

base = []
extra = []
experimental = []
for i in filenames:
    if re.match(r'^[012]', i):
        base.append(i)
    if re.match(r'^[34]', i):
        extra.append(i)
    if re.match(r'^50', i):
        experimental.append(i)
# remove 0000_README file from the list
base.pop(1)
print("base patch")
print(sorted(base))
print("extra patch")
print(extra)
print("experimental patch")
print(experimental)

cwd = os.getcwd()

chmod_ixusr("patch-kernel.sh")
chmod_ixusr("../clean.sh")
chmod_ixusr("find.sh")
