#!/usr/bin/env python
# -*- coding: utf-8 -*-
from buildbot.plugins import *
from twisted.internet import defer
from buildbot.plugins import reporters, util
from buildbot.process.properties import Interpolate
from buildbot.steps.shell import ShellCommand
from buildbot.process import results
from buildbot.process.buildstep import LogLineObserver
import re
import pprint
import os

@util.renderer
def BuildStatus(props):
    step = props.getBuild().executedSteps[-1]
    for i in step.build.executedSteps:
        if i.name == "Building kernel":
            if i.results == results.FAILURE:
                return "failed"
        if i.name == "Building modules":
            if i.results == results.FAILURE:
                return "failed"
        if i.name == "Run Gentoo kernel tests":
            if i.results == results.FAILURE:
                return "failed"
    return "success"

@util.renderer
def PatchStatus(props):
    step = props.getBuild().executedSteps[-1]
    for i in step.build.executedSteps:
        if i.name == "Patching kernel":
            if i.results == results.FAILURE:
                return "failed"
        if i.name == "Listing rejected files":
            if i.results == results.FAILURE:
                return "failed"
    return "success"

@util.renderer
@defer.inlineCallbacks
def stepLogsID(props):
    step = props.getBuild().executedSteps[-1]
    logs = yield step.master.data.get(('steps', step.stepid, 'logs'))
    print(logs)
    for l in logs:
        print(l['logid'])

def test_linux_patches(version, arch):
    factory = util.BuildFactory()
    factory.addStep(steps.ShellCommand(description="Cleaning enviroment",
                                 descriptionDone='Cleaned enviroment',
                                 name='Clean enviroment',
                                 command=["/bin/bash", "-c", "umask 022; rm -rf *"],
                                 alwaysRun=True,
                                 logEnviron=False,
                                 timeout=2400))

    factory.addStep(steps.SetPropertyFromCommand(
                                 logEnviron=False,
                                 name="date",
                                 command="date --iso-8601=ns",
                                 property="discoverytime"))

    factory.addStep(steps.GitHub(name="Fetching linux-patches",
                                 repourl='https://anongit.gentoo.org/git/proj/linux-patches.git',
                                 mode='incremental',
                                 logEnviron=False,
                                 workdir="build/linux-patches", branch=version))
    
    factory.addStep(steps.GitHub(name="Fetching Ghelper",
                                 repourl=os.getenv("GHELPER_REPOURL"),
                                 branch=os.getenv("GHELPER_BRANCH"),
                                 mode='incremental',
                                 alwaysRun=True,
                                 alwaysUseLatest=True,
                                 logEnviron=False,
                                 workdir="build/ghelper"))

    factory.addStep(steps.ShellCommand(name="Looking for new upstream release",
                                       command=["/usr/bin/python3",
                                                "check-kernelpage.py",
                                                "--version", version],
                                       workdir="build/ghelper/",
                                       logEnviron=False,
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Patching kernel",
                                       command=["/bin/bash", "patch-kernel.sh",
                                                "-a", arch, "-k", version, stepLogsID],
                                       workdir="build/ghelper/",
                                       logEnviron=False,
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Listing rejected files",
                                       command=["/bin/bash", "find.sh"],
                                       logEnviron=False,
                                       workdir="build/ghelper/"))

    factory.addStep(steps.ShellCommand(name="Building kernel",
                                       command=["/bin/bash", "../build-kernel.sh", arch,
                                                util.Property('buildername'),
                                                util.Property('buildnumber'),
                                                "build/ghelper/linux-" + version + "/"],
                                       workdir="build/ghelper/linux-" + version + "/",
                                       logEnviron=False,
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Building modules",
                                       command=["/bin/bash", "../build-kernel.sh", arch,
                                                util.Property('buildername'),
                                                util.Property('buildnumber'),
                                                "build/ghelper/linux-" + version + "/",
                                                "modules"],
                                       workdir="build/ghelper/linux-" + version + "/",
                                       logEnviron=False,
                                       haltOnFailure=True))

    factory.addStep(steps.ShellCommand(name="Move kernel to fileserver",
                                       command=["/bin/bash", "to_fileserver.sh", arch,
                                                util.Property('buildername'), util.Property('buildnumber')],
                                       logEnviron=False,
                                       workdir="build/ghelper/", timeout=3600))
    
    factory.addStep(steps.ShellCommand(name="Run Gentoo kernel tests",
                                       command=["/bin/bash", "run_tests.sh", arch,
                                                util.Property('buildername'), util.Property('buildnumber')],
                                       logEnviron=False,
                                       workdir="build/ghelper/", timeout=3600))
    factory.addStep(steps.ShellCommand(name="Send report to KCIDB",
                                       command=["/bin/bash", "kcidb/sendtokcidb", version,
                                                util.Property('buildername'), util.Property('buildnumber'),
                                                PatchStatus, arch, BuildStatus, util.Property('discoverytime')],
                                       logEnviron=False,
                                       alwaysRun=True,
                                       workdir="build/ghelper/", timeout=3600))
    factory.addStep(steps.ShellCommand(description="Cleaning enviroment2",
                                 descriptionDone='Cleaned environment',
                                 name='Clean environment end',
                                 command=["/bin/bash", "-c", "umask 022; rm -rf *"],
                                 alwaysRun=True,
                                 logEnviron=False,
                                 timeout=2400))
    return factory


@util.renderer
def filterFiles(props):
    files = props.getBuild().allFiles()
    print(files)
    build_files = [s for s in files if "sys-kernel/" in s]
    command = ["/bin/bash",
               "docker_emerge.sh",
               util.Property('arch'),
               util.Property('discoverytime')
               ]
    for file in build_files:
        if ".ebuild" in file: 
            if "sources" in file: 
                command.append(file)
    print(str(command))
    return command

@util.renderer
def run_stabilization_files(props):
    files = props.getBuild().allFiles()
    print(files)
    build_files = [s for s in files if "sys-kernel/" in s]
    command = ["/bin/bash", 
               "run_stabilization.sh", 
               util.Property('arch'),
               util.Property('buildername'),
               util.Property('buildnumber'),
               util.Property('discoverytime')
               ]
    for file in build_files:
        if ".ebuild" in file: 
            if "sources" in file: 
                command.append(file)
    print(str(command))
    return command

@util.renderer
def get_package_name(props):
    files = props.getBuild().allFiles()
    build_files = [s for s in files if "sys-kernel/" in s]
    for package in build_files:
        if ".ebuild" in package: 
            if "sources" in package: 
                return package.split("/")[1]
    return "None"

@util.renderer
def get_package_versions(props):
    files = props.getBuild().allFiles()
    build_files = [s for s in files if "sys-kernel/" in s]
    package_versions_list=[]
    for package in build_files:
        if ".ebuild" in package: 
            if "sources" in package: 
                package_filename=package.split("/")[2]
                package_version=package_filename.split(".ebuild")[0]
                package_versions_list.append(package_version)
    package_versions_string=" ".join(str(package) for package in package_versions_list)
    return package_versions_string
    

@util.renderer
def pull_repourl(props):
    pull_repourl = props.getProperty('repository')
    return pull_repourl

def test_source_packages(arch):
    factory = util.BuildFactory()
    factory.addStep(steps.ShellCommand(description="Cleaning enviroment",
                                 descriptionDone='Cleaned enviroment',
                                 name='Clean enviroment',
                                 command=["/bin/bash", "-c", "umask 022; rm -rf *"],
                                 logEnviron=False,
                                 timeout=2400))
    factory.addStep(steps.SetPropertyFromCommand(
                                 logEnviron=False,
                                 name="set date",
                                 command="date --iso-8601=ns",
                                 property="discoverytime"))
    factory.addStep(steps.SetProperty(
                                 property="arch",
                                 value=arch))
    factory.addStep(steps.SetProperty(
                                 property="package_name",
                                 value=get_package_name))
    factory.addStep(steps.SetProperty(
                                 property="package_versions",
                                 value=get_package_versions))
    factory.addStep(steps.GitHub(name="Fetching repository",
                                 repourl=pull_repourl,
                                 logEnviron=False,
                                 mode='incremental', workdir="build/gentoo", shallow=50))
    factory.addStep(steps.GitHub(name="Fetching Ghelper",
                                 repourl=os.getenv("GHELPER_REPOURL"),
                                 branch=os.getenv("GHELPER_BRANCH"),
                                 mode='incremental',
                                 logEnviron=False,
                                 alwaysUseLatest=True,
                                 workdir="build/ghelper"))
    factory.addStep(steps.ShellCommand(name=Interpolate("Building %(prop:package_versions)s"),
                                 command=filterFiles,
                                 logEnviron=False,
                                 workdir="build/ghelper/"))
    factory.addStep(steps.ShellCommand(name=Interpolate("Stabilize %(prop:package_versions)s"),
                                 command=run_stabilization_files,
                                 logEnviron=False,
                                 workdir="build/ghelper/", timeout=3600))
    factory.addStep(steps.ShellCommand(description="Cleaning enviroment",
                                 descriptionDone='Cleaned enviroment',
                                 name='Clean enviroment',
                                 command=["/bin/bash", "-c", "umask 022; rm -rf *"],
                                 logEnviron=False,
                                 timeout=2400))
    return factory

def test_eclass_changes(arch):
    factory = util.BuildFactory()
    factory.addStep(steps.ShellCommand(description="Cleaning enviroment",
                                 descriptionDone='Cleaned enviroment',
                                 name='Clean enviroment',
                                 command=["/bin/bash", "-c", "umask 022; rm -rf *"],
                                 logEnviron=False,
                                 timeout=2400))
    factory.addStep(steps.SetPropertyFromCommand(
                                 logEnviron=False,
                                 name="set date",
                                 command="date --iso-8601=ns",
                                 property="discoverytime"))
    factory.addStep(steps.SetProperty(
                                 property="arch",
                                 value=arch))
    factory.addStep(steps.GitHub(name="Fetching repository",
                                 repourl=pull_repourl,
                                 logEnviron=False,
                                 mode='incremental', workdir="build/gentoo", shallow=50))
    factory.addStep(steps.GitHub(name="Fetching Ghelper",
                                 repourl=os.getenv("GHELPER_REPOURL"),
                                 branch=os.getenv("GHELPER_BRANCH"),
                                 mode='incremental',
                                 logEnviron=False,
                                 alwaysUseLatest=True,
                                 workdir="build/ghelper"))
    factory.addStep(steps.ShellCommand(name=Interpolate("Building kernel-2.eclass"),
                                 command=filterFiles,
                                 logEnviron=False,
                                 workdir="build/ghelper/"))
    factory.addStep(steps.ShellCommand(name=Interpolate("Stabilize kernel-2.eclass"),
                                 command=run_stabilization_files,
                                 logEnviron=False,
                                 workdir="build/ghelper/", timeout=3600))
    factory.addStep(steps.ShellCommand(description="Cleaning enviroment",
                                 descriptionDone='Cleaned enviroment',
                                 name='Clean enviroment',
                                 command=["/bin/bash", "-c", "umask 022; rm -rf *"],
                                 logEnviron=False,
                                 timeout=2400))
    return factory

