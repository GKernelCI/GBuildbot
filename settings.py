#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml

# Define branch to build
branches_list = [
    '6.2',
    '6.1',
    '6.0',
    '5.15', 
    '5.10', 
    '5.4', 
    '4.19',
    '4.14', 
    '4.9', 
]

def get_arches():
    config = yaml.safe_load(open("config/config.yaml"))
    architecture_testing_list = config["architecture_testing_list"]
    return architecture_testing_list

def get_arches_stabilization():
    config = yaml.safe_load(open("config/config_stabilization.yaml"))
    architecture_stabilization_list = config["architecture_stabilization_list"]
    return architecture_stabilization_list

# get a list of all workers
def get_workers():
    try:
        cf = open("buildbot-config.yaml")
        cy = yaml.safe_load(cf)
    except IOError:
        return []
    if "workers" not in cy:
        print("ERROR: no workers list")
        return []
    return cy["workers"]

# get a list of all workers who can work arch+toolchain
def get_workers_for(arch, toolchain):
    fwl = []
    wl = get_workers()
    for wkr in wl:
        if arch == "gentoo_sources":
            if "gentoo_sources" in wkr:
                fwl.append(wkr["name"])
            continue
        if arch == "other_sources":
            if "other_sources" in wkr:
                fwl.append(wkr["name"])
            continue
        if arch == "eclass_change":
            if "eclass_change" in wkr:
                fwl.append(wkr["name"])
            continue
        if "toolchains" not in wkr:
            fwl.append(wkr["name"])
            continue
        if arch not in wkr["toolchains"]:
            continue
        if toolchain not in wkr["toolchains"][arch]:
            continue
        fwl.append(wkr["name"])
    print("DEBUG: get_workers_for %s %s is %s" % (arch, toolchain, str(fwl)))
    return fwl
