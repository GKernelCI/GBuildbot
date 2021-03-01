#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml

# Define branch to build
branches_list = ['5.11', '5.10', '5.4', '4.19',
                 '4.14', '4.9', '4.4']

def get_arches():
    config = yaml.safe_load(open("config/config.yaml"))
    architecture_testing_list = config["architecture_testing_list"]
    return architecture_testing_list
