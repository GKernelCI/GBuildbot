#!/usr/bin/env python
# -*- coding: utf-8 -*-
from buildbot.plugins import *
from buildbot.plugins import reporters, util
from buildbot.process.properties import Interpolate
import os

def download_new_patch_and_build_kernel(version, arch):
    factory = util.BuildFactory()
    factory.addStep(steps.GitHub(name="Fetching linux-patches",
                                 repourl='https://github.com/gentoo/linux-patches',
                                 mode='incremental',
                                 workdir="build/linux-patches", branch=version))
    
    factory.addStep(steps.GitHub(name="Fetching Ghelper",
                                 repourl='https://github.com/GKernelCI/Ghelper.git',
                                 mode='incremental',
                                 alwaysUseLatest=True,
                                 workdir="build/ghelper", branch='master'))

    factory.addStep(steps.ShellCommand(name="Looking for new upstream release",
                                       command=["/usr/bin/python",
                                                "check-kernelpage.py",
                                                "--version", version],
                                       workdir="build/ghelper/files/",
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Patching kernel",
                                       command=["/bin/sh", "patch-kernel.sh",
                                                "-a", arch, "-k", version],
                                       workdir="build/ghelper/files/",
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Listing rejected files",
                                       command=["/bin/sh", "find.sh"],
                                       workdir="build/ghelper/files/"))

    factory.addStep(steps.ShellCommand(name="Building kernel",
                                       command=["/bin/sh", "../build-kernel.sh", arch],
                                       workdir="build/ghelper/files/linux-" + version + "/",
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Building modules",
                                       command=["/bin/sh", "../build-kernel.sh", arch, "modules"],
                                       workdir="build/ghelper/linux-" + version + "/",
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Booting with QEMU",
                                       command=["/usr/bin/python", "qemu_check.py", arch,
                                                util.Property('buildername'), util.Property('buildnumber')],
                                       workdir="build/ghelper/files/", timeout=3600))

    factory.addStep(steps.ShellCommand(name="Cleanup",
                                       command=["/bin/sh", "clean.sh"],
                                       workdir="build/", 
                                       alwaysRun=True))

    return factory


@util.renderer
def filterFiles(props):
    files = props.getBuild().allFiles()
    print(files)
    build_files = [s for s in files if "sys-kernel/" in s]
    command = ["/usr/bin/python", "stabilize-packages.py"]
    for file in build_files:
        command.append(file)
    print(str(command))
    return command

@util.renderer
def pull_repourl(props):
    pull_repourl = props.getProperty('repository')
    return pull_repourl

def test_gentoo_sources():
    factory = util.BuildFactory()
    factory.addStep(steps.GitHub(name="Fetching repository",
                                 repourl=pull_repourl,
                                 mode='incremental', workdir="build/gentoo", shallow=50))
    factory.addStep(steps.GitHub(name="Fetching Ghelper",
                                 repourl='https://github.com/GKernelCI/Ghelper.git',
                                 mode='incremental',
                                 alwaysUseLatest=True,
                                 workdir="build/ghelper", branch='master'))

    factory.addStep(steps.ShellCommand(name="Stabilizing package",
                                       command=filterFiles,
                                       workdir="build/ghelper/files/"))
    # factory.addStep(steps.ShellCommand(command=["/usr/bin/python", "qemu_check.py"],
    #                                workdir="build/files/"))
    factory.addStep(steps.ShellCommand(name="Cleanup",
                                       command=["/bin/sh", "clean.sh"],
                                       workdir="build/", 
                                       alwaysRun=True))
    return factory

