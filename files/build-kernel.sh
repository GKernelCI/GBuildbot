#!/bin/sh

set -e

MAKEOPTS="-j$(( $(getconf _NPROCESSORS_ONLN) + 1 ))"

if [ $# -lt 1 ]; then
	echo "Usage: $(basename $0) arch"
	exit 1
fi

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

MAKEOPTS="$MAKEOPTS O=$(dirname $(realpath $0))/linux-$1-build"

shift

make $MAKEOPTS $*
