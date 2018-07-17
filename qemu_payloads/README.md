## build instructions ##

"it's mostly just busybox"

```
armpayload-initramfs.gz

(or)

amd64payload-initramfs.gz
```

/bin/ is made with crossdev-style emerge:

```
emerge-armv7a-hardfloat-linux-gnueabi
emerge-x86_64-pc-linux-musl
```

copy busybox into respective staging directory:

```
cp -P /usr/$FLAVOR/bin/* /$STAGING/bin/
```

[re]build corresponding qemu payload using:

```
cd armpayload-qemu
find . | cpio -R root:root -H newc -o | gzip > ../armpayload-initramfs.gz

(or)

cd amd64payload-qemu  
find . | cpio -R root:root -H newc -o | gzip > ../amd64payload-initramfs.gz

```

---

note: /init script & empty /proc/ and /etc/mtab  
found in "proof of concept" staging directories.

.gitignore file in /proc/ might cause issue,  
so removing it might be required (untested)

crosscompiled busybox binary may be rebuilt  
(busybox_canary.txt for "proof of concept")
