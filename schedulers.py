#!/usr/bin/env python
# -*- coding: utf-8 -*-

from buildbot.plugins import *
from buildbot.schedulers.basic import AnyBranchScheduler, SingleBranchScheduler
from buildbot.schedulers.forcesched import ForceScheduler
from buildbot.plugins import reporters, util
from buildbot.process.properties import Interpolate
from config.settings import branches_list, get_arches
import os

####### SCHEDULERS

# Configure the Schedulers, which decide how to react to incoming changes.
# In this case, just kick off a 'runtests' build

def change_files_json_push(change):
    print("Change111: "+str(change.files))
    if any("sys-kernel/gentoo-sources" in s for s in change.files):
        print("sys-kernel ebuild to test")
        return True
    else:
        return False

def syskernel_change(change):
    print("Change111: "+str(change.files))
    if any("sys-kernel/" in s for s in change.files):
        print("sys-kernel ebuild to test")
        return True
    else:
        return False

def eclass_change(change):
    print("Change111: "+str(change.files))
    if any("eclass/kernel-2.eclass" in s for s in change.files):
        print("sys-kernel ebuild to test")
        return True
    else:
        return False

architecture_testing_list = get_arches()

def builderNames(branch):
    builders = set()

    for arch in architecture_testing_list:
        builders.add(branch + ':' + arch["name"])

    return list(builders)

schedulers = []


for branch in branches_list:
    schedulers.append(SingleBranchScheduler(
                                name=branch,
                                change_filter=util.ChangeFilter(branch=branch),
                                treeStableTimer=None,
                                builderNames=builderNames(branch)))
    for arch in architecture_testing_list:
        schedulers.append(ForceScheduler(
                                name="Force_%s_%s" % (branch.replace(".", "_"), arch["name"]),
                                builderNames=["%s:%s" % (branch, arch["name"])]
                                ))
    # add a changefilter for the pull requests
    cf = util.ChangeFilter(category='pull', branch=branch)
    # but only those that are targeted for that branch
    cf.checks["prop:github.base.ref"] = cf.checks['branch']
    del cf.checks['branch']
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
schedulers.append(SingleBranchScheduler(
        name="gentoo_sources",
        change_filter=gpcf,
        treeStableTimer=None,
        builderNames=["gentoo_sources"]))
schedulers.append(ForceScheduler(
        name="force_gentoo_sources",
        builderNames=["gentoo_sources"]))

gpcf = util.ChangeFilter(category='gentoo-pull', filter_fn=syskernel_change)
schedulers.append(SingleBranchScheduler(
        name="other_sources",
        change_filter=gpcf,
        treeStableTimer=None,
        builderNames=["other_sources"]))
schedulers.append(ForceScheduler(
        name="force_other_sources",
        builderNames=["other_sources"]))

gpcf = util.ChangeFilter(category='gentoo-pull', filter_fn=eclass_change)
schedulers.append(SingleBranchScheduler(
        name="eclass_change",
        change_filter=gpcf,
        treeStableTimer=None,
        builderNames=["eclass_change"]))
schedulers.append(ForceScheduler(
        name="force_eclass_change",
        builderNames=["eclass_change"]))
