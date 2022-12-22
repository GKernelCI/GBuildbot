#!/usr/bin/env python
# -*- coding: utf-8 -*-

from buildbot.plugins import *
from buildbot.schedulers.basic import AnyBranchScheduler, SingleBranchScheduler
from buildbot.schedulers.forcesched import ForceScheduler
from buildbot.scheduler import Try_Userpass
from buildbot.plugins import reporters, util
from buildbot.process.properties import Interpolate
from config.settings import branches_list, get_arches, get_arches_stabilization
import os

####### SCHEDULERS

# Configure the Schedulers, which decide how to react to incoming changes.
# In this case, just kick off a 'runtests' build

# looks for gentoo-sources changes
def change_files_json_push(change):
    print("Change111: "+str(change.files))
    if any("sys-kernel/gentoo-sources" in s for s in change.files):
        print("sys-kernel ebuild to test")
        return True

# looks for sys-kernel changes but excluding gentoo-sources
def syskernel_change(change):
    print("Change111: "+str(change.files))
    syskernel_package_found=False
    for package in change.files:
        if "sys-kernel/" in package:
            if "sys-kernel/gentoo-sources" not in package:
                if "gentoo-kernel" not in package: 
                    if"vanilla-kernel" not in package:
                        if "gentoo-kernel-bin" not in package:
                            if "genkernel" not in package:
                                syskernel_package_found = True
    if syskernel_package_found == True:
        return True

# looks for eclass/kernel-2.eclass changes only
def eclass_change(change):
    print("Change111: "+str(change.files))
    if any("eclass/kernel-2.eclass" in s for s in change.files):
        print("sys-kernel ebuild to test")
        return True

architecture_testing_list = get_arches()
architecture_stabilization_list = get_arches_stabilization()

def builderNames(branch):
    builders = set()

    for arch in architecture_testing_list:
        for toolchain in arch["toolchain"]:
            builders.add(branch + ':' + arch["name"] + ':' + toolchain["name"])

    return list(builders)

schedulers = []
builder_names = []


for branch in branches_list:
    # Get builder names for Try schedule
    for i in range(len(builderNames(branch))):
        builder_names.append(builderNames(branch)[i])

    schedulers.append(SingleBranchScheduler(
                                name=branch,
                                change_filter=util.ChangeFilter(branch=branch),
                                treeStableTimer=None,
                                builderNames=builderNames(branch)))
    # add a changefilter for the pull requests
    cf = util.ChangeFilter(category='pull', branch=branch)
    # but only those that are targeted for that branch
    cf.filters["prop:github.base.ref"] = cf.filters['branch']
    del cf.filters['branch']
    schedulers.append(SingleBranchScheduler(
                                name="pull" + branch,
                                change_filter=cf,
                                treeStableTimer=None,
                                builderNames=builderNames(branch)))

    stab_cf = util.ChangeFilter(category='pull', branch=branch)
    schedulers.append(SingleBranchScheduler(
                                name="stabilize" + branch,
                                change_filter=stab_cf,
                                treeStableTimer=None,
                                builderNames=builderNames(branch)))

    # add a changefilter for the pull requests
    gcf = util.ChangeFilter(category='gentoo-git', branch_re=branch+"\..*")
    schedulers.append(SingleBranchScheduler(
        name="git_pull" + branch,
        change_filter=gcf,
        treeStableTimer=None,
        builderNames=builderNames(branch)))

    stab_gcf = util.ChangeFilter(category='gentoo-tags-git',
                                 branch_re="refs/tags/" + branch + "_stabilize")
    schedulers.append(SingleBranchScheduler(
        name="git_stabilize" + branch,
        change_filter=stab_gcf,
        treeStableTimer=None,
        builderNames=builderNames(branch)))

gpcf = util.ChangeFilter(category='gentoo-pull', filter_fn=change_files_json_push)
for arch in architecture_stabilization_list:
    schedulers.append(SingleBranchScheduler(
            name="gentoo_sources"+":"+ arch['name'],
            change_filter=gpcf,
            treeStableTimer=None,
            builderNames=["gentoo_sources"+":"+ arch['name']]))
    schedulers.append(SingleBranchScheduler(
            name="other_sources"+":"+ arch['name'],
            change_filter=gpcf,
            treeStableTimer=None,
            builderNames=["other_sources"+":"+ arch['name']]))
    builder_names.append('gentoo_sources'+":"+ arch['name'])
    builder_names.append('other_sources'+":"+ arch['name'])

schedulers.append(SingleBranchScheduler(
        name="eclass_change",
        change_filter=gpcf,
        treeStableTimer=None,
        builderNames=["eclass_change"]))

# append static builder name
builder_names.append('eclass_change')

# Add try schedule for buildbot try command
schedulers.append(Try_Userpass(
        name='try',
        builderNames=builder_names,
        port=5555,
        userpass=[('Developer',os.environ.get('TRY_PASSWD'))]))
