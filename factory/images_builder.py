#!/usr/bin/env python
# -*- coding: utf-8 -*-
from buildbot.plugins import *
from buildbot.plugins import reporters, util
from buildbot.process.properties import Interpolate
import os

def download_new_patch_and_build_kernel(version, arch):
    factory = util.BuildFactory()
    factory.addStep(steps.ShellCommand(description="Cleaning enviroment",
                                 descriptionDone='Cleaned enviroment',
                                 name='Clean enviroment',
                                 command=["/bin/bash", "-c", "umask 022; rm -rf *"],
                                 timeout=2400))

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
                                       command=["/usr/bin/python3",
                                                "check-kernelpage.py",
                                                "--version", version],
                                       workdir="build/ghelper/",
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Patching kernel",
                                       command=["/bin/sh", "patch-kernel.sh",
                                                "-a", arch, "-k", version],
                                       workdir="build/ghelper/",
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Listing rejected files",
                                       command=["/bin/sh", "find.sh"],
                                       workdir="build/ghelper/"))

    factory.addStep(steps.ShellCommand(name="Building kernel",
                                       command=["/bin/sh", "../build-kernel.sh", arch],
                                       workdir="build/ghelper/linux-" + version + "/",
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Building modules",
                                       command=["/bin/sh", "../build-kernel.sh", arch, "modules"],
                                       workdir="build/ghelper/linux-" + version + "/",
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Move kernel to fileserver",
                                       command=["/bin/sh", "to_fileserver.sh", arch,
                                                util.Property('buildername'), util.Property('buildnumber')],
                                       workdir="build/ghelper/", timeout=3600))
    
    factory.addStep(steps.ShellCommand(name="Run Gentoo kernel tests",
                                       command=["/bin/sh", "run_tests.sh", arch,
                                                util.Property('buildername'), util.Property('buildnumber')],
                                       workdir="build/ghelper/", timeout=3600))
    return factory


@util.renderer
def filterFiles(props):
    files = props.getBuild().allFiles()
    print(files)
    build_files = [s for s in files if "sys-kernel/" in s]
    command = ["/usr/bin/python3", "stabilize-packages.py"]
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
    factory.addStep(steps.ShellCommand(description="Cleaning enviroment",
                                 descriptionDone='Cleaned enviroment',
                                 name='Clean enviroment',
                                 command=["/bin/bash", "-c", "umask 022; rm -rf *"],
                                 timeout=2400))
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
                                       workdir="build/ghelper/"))
    return factory

