#!/usr/bin/env bash
python3 clean.py
rm -rf files/
rm -rf gentoo/
rm -rf linux-patches/
find /tmp -name "gentoo*.qcow2" -mtime +2 -delete
