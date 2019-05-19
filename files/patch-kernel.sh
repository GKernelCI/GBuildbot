#!/bin/sh
set -eu

# Usage info
show_help() {
cat << EOF
Usage: ${0##*/} [-hv] [-k] [KERNEL VERSION]
Do stuff with FILE and write the result to standard output. With no FILE
or when FILE is -, read standard input.

    -a          kernel architecture to use for search configuration file.
    -h          display this help and exit
    -k          use the kernel version for search configuration file.
    -v          verbose mode. Can be used multiple times for increased
                verbosity.
EOF
}

# Initialize our own variables:
kernel_version=""
kernel_arch="amd64"
verbose=0

OPTIND=1
# Resetting OPTIND is necessary if getopts was used previously in the script.
# It is a good idea to make OPTIND local if you process options in a function.

while getopts a:hvk: opt; do
    case $opt in
        a)
            kernel_arch=$OPTARG
            ;;
        h)
            show_help
            exit 0
            ;;
        v)  verbose=$((verbose+1))
            ;;
        k)  kernel_version=$OPTARG
            ;;
        *)
            show_help >&2
            exit 1
            ;;
    esac
done
shift "$((OPTIND-1))" # Shift off the options and optional --.

kernel_arch_target="x86_64"
if [ $kernel_arch = "arm" ]; then
	kernel_arch_target="arm"
fi

# End of file
for i in ../linux-patches/*.patch; do
	echo "${i}"
	yes "" | patch -p1 --no-backup-if-mismatch -f -N -s -d linux-*/ < "${i}";
done
kernel_builddir="$(dirname $(realpath $0))/linux-${kernel_arch}-build"
cd linux-*/ || exit 1
test -d $kernel_builddir | mkdir $kernel_builddir
if [ ! -z "${kernel_version}" ]; then
	version="${kernel_version}-${kernel_arch}"
	if [ -f ~/kernel-config/config-${version}_defconfig ]; then
		defconfig=$(cat ~/kernel-config/config-${version}_defconfig)
		echo "Using defconfig ${defconfig}"
		make ARCH=${kernel_arch_target} O=${kernel_builddir} ${defconfig}
	elif [ ! -f ~/kernel-config/config-"${version}" ]; then
		echo "Kernel config-${version} not found!"
		#echo "Trying configuration in /proc/config.gz.."
		if [ ! -f ~/kernel-config ] && [ -r /proc/config.gz ]; then
			echo "Using /proc/config.gz"
			zcat /proc/config.gz > .config
		else
			echo "Using defconfig"
			make ARCH=${kernel_arch_target} O=${kernel_builddir} defconfig
		fi
		make mrproper
		yes "" | make ARCH=${kernel_arch_target} O=${kernel_builddir} defconfig
	else
		echo "Using ~/kernel-config/config-${version}"
		make mrproper
		cp ~/kernel-config/config-"${version}" .config
		yes "" | make ARCH=${kernel_arch_target} O=${kernel_builddir} oldconfig
	fi
fi
head Makefile
