#!/usr/bin/env python
# -*- coding: utf-8 -*-

####### BUILDERS

# The 'builders' list defines the Builders, which tell Buildbot how to perform a build:
# what steps, and which workers can execute them.  Note that any particular build will
# only take place on one worker.
import config.factory
from config.factory.images_builder import *
from buildbot.plugins import *
from buildbot.plugins import reporters, util
from buildbot.process.properties import Interpolate
from config.settings import (
    branches_list,
    get_arches,
    get_arches_stabilization,
    get_workers_for,
)
import os

builders = []
architecture_testing_list = get_arches()
#architecture_stabilization_list = get_arches_stabilization()

for kernel_branch in branches_list:
    for arch in architecture_testing_list:
        for toolchain in arch["toolchain"]:
            tags = []
            tags.append(toolchain["name"])
            tags.append(arch["name"])
            tags.append(kernel_branch)
            builders.append(
                util.BuilderConfig(
                    name=kernel_branch + ":" + arch["name"] + ":" + toolchain["name"],
                    tags=tags,
                    workernames=get_workers_for(arch["name"], toolchain["name"]),
                    factory=test_linux_patches(kernel_branch, arch["name"]),
                )
            )

#for arch in architecture_stabilization_list:
#    builders.append(
#        util.BuilderConfig(
#            name="gentoo_sources" + ":" + arch["name"],
#            workernames=get_workers_for("gentoo_sources", None),
#            factory=test_source_packages(arch["name"]),
#        )
#    )
#
#for arch in architecture_stabilization_list:
#    builders.append(
#        util.BuilderConfig(
#            name="other_sources" + ":" + arch["name"],
#            workernames=get_workers_for("other_sources", None),
#            factory=test_source_packages(arch["name"]),
#        )
#    )

builders.append(
    util.BuilderConfig(
        name="eclass_change",
        workernames=get_workers_for("eclass_change", None),
        factory=test_eclass_changes("x86_64"),
    )
)
