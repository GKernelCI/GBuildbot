# GKernelCI
Automated build and testing for Gentoo Kernel packages and eclasses

[![Build Status](https://travis-ci.com/GKernelCI/GBuildbot.svg?branch=master)](https://travis-ci.com/GKernelCI/GBuildbot)

## quick start

GKernelCI is currently working with [docker-compose](https://github.com/aliceinwire/GkernelCI_docker)

Clone GKernelCI_docker repository  
`git clone https://github.com/aliceinwire/GkernelCI_docker`  
Change the *docker-compose.yml* and start docker-compose   
`docker-compose up -d`

## Gentoo kernel stabilization

### how Gentoo kernel stabilization work
```
Kernel ebuilds referenced in the Handbook have certain exemptions from the usual stabilization policy, so stabilization requests are normally only filed for the first version in a long term stable branch (subsequent versions can be stabilized at the discretion of the maintainer).

First, test all available kernel options:
user $cd /usr/src/example-sources-1.2.3
user $make allyesconfig
user $make # add '-j' as appropriate for the hardware

If that succeeds, build with a normal kernel configuration:
user $make distclean
user $make menuconfig
user $make
user $make modules_install # if you use modules

After reboot, check dmesg for anything strange and use the system as normal, trying to get a bit of uptime.

If stabilizing a special feature variant, try to test relevant features. 
```
## Code
Any contribute is welcome

Please check the [issues](https://github.com/gentoo/Gentoo_kernelCI/issues) for contributing
