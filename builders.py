#!/usr/bin/env python
# -*- coding: utf-8 -*-

####### BUILDERS

# The 'builders' list defines the Builders, which tell Buildbot how to perform a build:
# what steps, and which workers can execute them.  Note that any particular build will
# only take place on one worker.
from buildbot.plugins import *
from buildbot.plugins import reporters, util
from buildbot.process.properties import Interpolate
import os


def download_new_patch_and_build_kernel(version, arch):
    factory = util.BuildFactory()
    factory.addStep(steps.GitHub(name="Fetching linux-patches repository",
                                 repourl='https://github.com/gentoo/linux-patches',
                                 mode='incremental',
                                 workdir="build/linux-patches", branch=version))

    factory.addStep(steps.FileDownload(mastersrc="config/files/check-kernelpage.py",
                                       workerdest="files/check-kernelpage.py"))

    factory.addStep(steps.FileDownload(mastersrc="config/files/qemu_check.py",
                                       workerdest="files/qemu_check.py"))

    factory.addStep(steps.FileDownload(mastersrc="config/files/patch-kernel.sh",
                                       workerdest="files/patch-kernel.sh"))

    factory.addStep(steps.FileDownload(mastersrc="config/files/build-kernel.sh",
                                       workerdest="files/build-kernel.sh"))

    factory.addStep(steps.FileDownload(mastersrc="config/files/clean.sh",
                                       workerdest="clean.sh",
                                       alwaysRun=True))

    factory.addStep(steps.FileDownload(mastersrc="config/files/clean.py",
                                       workerdest="clean.py",
                                       alwaysRun=True))

    factory.addStep(steps.FileDownload(mastersrc="config/files/find.sh",
                                       workerdest="files/find.sh"))

    factory.addStep(steps.ShellCommand(name="Looking for new upstream release",
                                       command=["/usr/bin/python",
                                                "check-kernelpage.py",
                                                "--version", version],
                                       workdir="build/files/",
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Patching kernel",
                                       command=["/bin/sh", "patch-kernel.sh",
                                                "-a", arch, "-k", version],
                                       workdir="build/files/",
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Listing rejected files",
                                       command=["/bin/sh", "find.sh"],
                                       workdir="build/files/"))

    factory.addStep(steps.ShellCommand(name="Building kernel",
                                       command=["/bin/sh", "../build-kernel.sh", arch],
                                       workdir="build/files/linux-" + version + "/",
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Building modules",
                                       command=["/bin/sh", "../build-kernel.sh", arch, "modules"],
                                       workdir="build/files/linux-" + version + "/",
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Booting with QEMU",
                                       command=["/usr/bin/python", "qemu_check.py", arch,
                                                util.Property('buildername'), util.Property('buildnumber')],
                                       workdir="build/files/", timeout=3600))

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
    factory.addStep(steps.FileDownload(mastersrc="config/files/qemu_check.py",
                                       workerdest="files/qemu_check.py"))
    factory.addStep(steps.FileDownload(mastersrc="config/files/stabilize-packages.py",
                                       workerdest="files/stabilize-packages.py"))
    factory.addStep(steps.FileDownload(mastersrc="config/files/clean.sh",
                                       workerdest="clean.sh",
                                       alwaysRun=True))
    factory.addStep(steps.FileDownload(mastersrc="config/files/clean.py",
                                       workerdest="clean.py",
                                       alwaysRun=True))
    factory.addStep(steps.ShellCommand(name="Stabilizing package",
                                       command=filterFiles,
                                       workdir="build/files/"))
    # factory.addStep(steps.ShellCommand(command=["/usr/bin/python", "qemu_check.py"],
    #                                workdir="build/files/"))
    factory.addStep(steps.ShellCommand(name="Cleanup",
                                       command=["/bin/sh", "clean.sh"],
                                       workdir="build/", 
                                       alwaysRun=True))
    return factory

architecture_testing_list = ['amd64']
branches_list = ['5.4', '5.3', '4.20', '4.19', '4.18',
                 '4.14', '4.9', '4.8', '4.4', '4.1']

builders = []

for kernel_branch in branches_list:
    for arch in architecture_testing_list:
        builders.append(
              util.BuilderConfig(name=kernel_branch + ':' + arch,
                                 workernames=["kernelci"],
                        factory=download_new_patch_and_build_kernel(kernel_branch, arch)))

builders.append(
    util.BuilderConfig(name='gentoo_sources',
                       workernames=["kernelci"],
                       factory=test_gentoo_sources()))

builders.append(
    util.BuilderConfig(name='other_sources',
                       workernames=["kernelci"],
                       factory=test_gentoo_sources()))

builders.append(
    util.BuilderConfig(name='eclass_change',
                       workernames=["kernelci"],
                       factory=test_gentoo_sources()))

