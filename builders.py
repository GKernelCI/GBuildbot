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
from config.settings import branches_list, get_arches
import os

builders = []
architecture_testing_list = get_arches()

for kernel_branch in branches_list:
    for arch in architecture_testing_list:
        for toolchain in arch["toolchain"]:
            builders.append(
              util.BuilderConfig(name=kernel_branch + ':' + arch["name"] + ':' + toolchain,
                                 workernames=[os.environ.get('WORKER_NAME')],
                        factory=download_new_patch_and_build_kernel(kernel_branch, arch["name"])))

builders.append(
    util.BuilderConfig(name='gentoo_sources',
                       workernames=[os.environ.get('WORKER_NAME')],
                       factory=test_gentoo_sources()))

builders.append(
    util.BuilderConfig(name='other_sources',
                       workernames=[os.environ.get('WORKER_NAME')],
                       factory=test_gentoo_sources()))

builders.append(
    util.BuilderConfig(name='eclass_change',
                       workernames=[os.environ.get('WORKER_NAME')],
                       factory=test_gentoo_sources()))

