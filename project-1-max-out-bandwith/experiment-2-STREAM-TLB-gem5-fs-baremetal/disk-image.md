## Downloading the disk image
```sh
wget http://dist.gem5.org/dist/v22-0/images/riscv/busybox/riscv-disk.img.gz
gunzip riscv-disk.img.gz
# Resizing the disk image to 3GiB
e2fsck -f riscv-disk.img
resize2fs ./riscv-disk.img 3G
```

## Compiling STREAM statically
```sh
ln -s ../utils utils
python3 utils/generate_riscv_n_elements.py riscv_n_elements.txt
python3 utils/compile_STREAM.py riscv_n_elements.txt
```

## Copying the binary to the disk image
```sh
mkdir mnt
sudo mount riscv-disk.img mnt
sudo mkdir mnt/home/
sudo cp -r build/binaries/riscv/* mnt/home/
sudo rm mnt/sbin/init
sudo cp disk-image-scripts/init mnt/sbin
sudo chmod 777 mnt/sbin/init
```
