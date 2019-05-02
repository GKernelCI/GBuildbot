#!/bin/sh

set -e

cd(){ command cd "$1" ; }

cd linux-*

if [ $# -lt 1 ]; then
	echo "Usage: $(basename $0) arch"
	exit 1
fi

make menuconfig

MAKEOPTS="-j$(( $(getconf _NPROCESSORS_ONLN) + 1 ))"


case "$1" in
	"amd64")
		;;
	"arm")
		MAKEOPTS="ARCH=arm CROSS_COMPILE=armv7a-hardfloat-linux-gnueabi- $MAKEOPTS"
		;;
	*)
		echo "Unsupported arch: $1"
		exit 1
		;;
esac

shift

make $MAKEOPTS

/bin/bash $(pwd)/../$(basename $0) $1
