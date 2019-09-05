#!/usr/bin/env bash
python clean.py
rm -rf files/
rm -rf gentoo/
rm -rf linux-patches/
find /tmp -maxdepth 1 -name "gentoo*.qcow2" -mtime +2 -size -100M -delete
