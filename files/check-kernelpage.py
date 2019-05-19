#!/usr/bin/env python
from __future__ import print_function

import argparse
import shelve
import shutil
import subprocess
import sys
import tarfile

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
from os import walk
import re
import requests
from bs4 import BeautifulSoup

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

r = requests.get('https://www.kernel.org/')

# print r.status_code
soup = BeautifulSoup(r.content, "lxml")
# print soup
tables = soup.findChildren('table')

# This will get the first (and only) table. Your page may have more.
my_table = tables[2]
# print my_table
tr_table = my_table.findChildren('tr')


def get_version_number(tr_html):
    # get list of td
    tr_html = tr_html.findChildren('td')
    # td 1 contains the kernel number
    tr_html = tr_html[1]
    # get the kernel number inside strong tag
    for node in tr_html.findAll('strong'):
        tr_html_number = ''.join(node.findAll(text=True))
    return tr_html_number


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

for i in tr_table:
    version_number = get_version_number(i)
    new_version_revision = find_new_version(version_number, args.version)
    if new_version_revision is not None:
        break
conf_var = "shelve"
d = shelve.open(conf_var)
d["version"] = [new_version_revision]
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

print("new_version_split"+str(new_version_split))
major_ver = new_version_split[0]
revision = new_version_split[-1]
if "[EOL]" in revision:
    revision = revision[:-6]
print(revision)
old_revision = int(revision)-1
print(old_revision)
# incremental patch
incremental_patch_version = new_version + "." + str(old_revision) + \
    "-" + revision
incremental_patch_name = "patch-" + incremental_patch_version + ".xz"
# non incremental patch
patch_version = new_version + "." + revision
patch_name = "patch-" + patch_version + ".xz"
if int(revision) > 1:
    print("# is incremental version")
    print("revision: " + str(revision))
    patch_url = "http://cdn.kernel.org/pub/linux/kernel/v" + \
        major_ver + ".x/incr/" + incremental_patch_name
    print(patch_url)
    urlretrieve(patch_url, incremental_patch_name)
    with lzma.open(incremental_patch_name) as f, open(
            incremental_patch_name[:-3], 'wb') as fout:
        file_content = f.read()
        fout.write(file_content)
else:
    print("# not incremental version")
    print("revision: " + str(revision))
    patch_url = "http://cdn.kernel.org/pub/linux/kernel/v" + \
        major_ver + ".x/" + patch_name
    print(patch_url)
    urlretrieve(patch_url, patch_name)
    with lzma.open(patch_name) as f, open(patch_name[:-3], 'wb') as fout:
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

if new_version != 1:
    if patch_found == 0:
        shutil.move(incremental_patch_name[:-3], '../linux-patches/' +
                    incremental_patch_name[:-3] + '.patch')
else:
    if patch_found == 0:
        shutil.move(patch_name[:-3], '../linux-patches/' + patch_name[:-3] +
                    '.patch')

os.chdir(mypath)

base = []
extra = []
experimental = []
for i in filenames:
    if re.match(r'^[012]', i):
        base.append(i)
    if re.match(r'^[34]', i):
        extra.append(i)
    if re.match(r'^50', i):
        #experimental.append(i)
        os.unlink(i)
# remove 0000_README file from the list
base.pop(1)
print("base patch")
print(sorted(base))
print("extra patch")
print(extra)
print("experimental patch")
print(experimental)

cwd = os.getcwd()

bashCommand = "chmod +x patch-kernel.sh"
print(bashCommand)
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
output, error = process.communicate()
print(output)
eprint(error)

bashCommand = "chmod +x ../clean.sh"
print(bashCommand)
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
output, error = process.communicate()
print(output)
eprint(error)

bashCommand = "chmod +x find.sh"
print(bashCommand)
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
output, error = process.communicate()
print(output)
eprint(error)
