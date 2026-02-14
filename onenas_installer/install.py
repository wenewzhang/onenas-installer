import asyncio
import json
import os
import subprocess
import tempfile
from typing import Callable

from .disks import Disk
from .exception import InstallError
from .i18n import _
from .lock import installation_lock
from .logger import logger
from .utils import get_partitions, run

__all__ = ["InstallError", "install"]

ONE_POOL = "one-pool"


async def install(destination_disks: list[Disk], wipe_disks: list[Disk], system_pct: int, min_system_size: int, callback: Callable, version: str | None = None, language: str | None = None):
    boot_mode = check_boot_mode()
    min_system_size_mib = min_system_size // (1024 * 1024)
    min_system_size_str = f"{min_system_size_mib}m"  # 例如: "+8192m"
                  
    logger.info(f"boot mode: {boot_mode} system percent: {system_pct} system disk size: {min_system_size_str}")                     
    with installation_lock:
        try:
            if not os.path.exists("/etc/hostid"):
                await run(["zgenhostid"])

            for disk in destination_disks:
                callback(0, _("wiping_disk", disk=disk.name))
                await wipe_disk(disk, callback)

            for disk in destination_disks:
                callback(0, _("formatting_disk", disk=disk.name))
                if boot_mode == "UEFI":
                    await format_disk_uefi(disk, system_pct, min_system_size_str, callback)
                else:
                    await format_disk_bios2(disk, system_pct, min_system_size_str, callback)

            # for disk in wipe_disks:
            #     callback(0, f"Wiping disk {disk.name}")
            #     await wipe_disk(disk, callback)

            disk_parts = list()
            
            part_num = 2 if system_pct == 100 else 3

            for disk in destination_disks:
                found = (await get_partitions(disk.device, [part_num]))[part_num]
                if found is None:
                    raise InstallError(f"Failed to find data partition on {disk.name}")
                else:
                    disk_parts.append(found)

            callback(0, _("creating_boot_pool"))
            await create_one_pool(disk_parts)
            try:
                await run_installer(
                    [disk.name for disk in destination_disks],
                    callback,
                    version,
                    language,
                    boot_mode,
                )
            finally:
                await run(["zpool", "export", "-f", ONE_POOL])
        except subprocess.CalledProcessError as e:
            raise InstallError(f"Command {' '.join(e.cmd)} failed:\n{e.stderr.rstrip()}")


async def wipe_disk(disk: Disk, callback: Callable):
    for zfs_member in disk.zfs_members:
        if (result := await run(["zpool", "labelclear", "-f", f"/dev/{zfs_member.name}"],
                                check=False)).returncode != 0:
            callback(0, _("warning_wipe_zfs_label", device=zfs_member.name, error=result.stderr.rstrip()))
        pass

    if (result := await run(["wipefs", "-a", disk.device], check=False)).returncode != 0:
        callback(0, _("warning_wipe_partition_table", disk=disk.name, error=result.stderr.rstrip()))

    await run(["sgdisk", "-Z", disk.device], check=False)

async def format_disk_uefi(disk: Disk, system_pct: int, min_system_size:str, callback: Callable):
    await wipe_disk(disk, callback)

    await run(["sgdisk", "-n1:1m:+512m", "-t", "1:ef00", disk.device])
    if system_pct == 100:
        await run(["sgdisk", "-n2:0:0", "-t2:BF01", disk.device])
        part_nums = [1, 2]        
    else:
        await run(["sgdisk", f"-n2:0:+{min_system_size}", "-t2:BF00", disk.device])        
        await run(["sgdisk", "-n3:0:0", "-t3:BF01", disk.device])
        part_nums = [1, 2, 3]
        
    # Bad hardware is bad, but we've seen a few users
    # state that by the time we run `parted` command
    # down below OR the caller of this function tries
    # to do something with the partition(s), they won't
    # be present. This is almost _exclusively_ related
    # to bad hardware, but we will wait up to 30 seconds
    # for the partitions to show up in sysfs.
    disk_parts = await get_partitions(disk.device, part_nums, tries=30)
    for partnum, part_device in disk_parts.items():
        logger.info("format_disk_uefi disk_parts:%s",disk_parts)
        if part_device is None:
            raise InstallError(f"Failed to find partition number {partnum} on {disk.name}")
        

async def format_disk_bios(disk: Disk, system_pct: int, min_system_size:str, callback: Callable):
    await wipe_disk(disk, callback)

    # await run(["sgdisk", "-n1:1m:+512m", "-t", "1:ef00", disk.device])
    # 对应原始指令: sgdisk -n 1:2048:+512MiB -t 1:8300 -A 1:set:2
    await run(["sgdisk","-n1:2048:+512m","-t1:8300","-A1:set:2",disk.device])
    # sgdisk -n 1:2048:+512MiB -t 1:8300 -A 1:set:2 "${POOL_DISK}"
    if system_pct == 100:
        await run(["sgdisk", "-n2:0:0", "-t2:8300", disk.device])        
    else:
        await run(["sgdisk", f"-n2:0:+{min_system_size}", "-t2:8300", disk.device])        
        await run(["sgdisk", "-n3:0:0", "-t3:BF01", disk.device])
        

    # Bad hardware is bad, but we've seen a few users
    # state that by the time we run `parted` command
    # down below OR the caller of this function tries
    # to do something with the partition(s), they won't
    # be present. This is almost _exclusively_ related
    # to bad hardware, but we will wait up to 30 seconds
    # for the partitions to show up in sysfs.
    disk_parts = await get_partitions(disk.device, [1, 2, 3], tries=30)
    for partnum, part_device in disk_parts.items():
        logger.info("format_disk_bios disk_parts:%s",disk_parts)
        if part_device is None:
            raise InstallError(f"Failed to find partition number {partnum} on {disk.name}")

async def format_disk_bios2(disk: Disk, system_pct: int, min_system_size: str, callback: Callable):
    await wipe_disk(disk, callback)

    if system_pct == 100:
        bash_cmd = f"""cat <<'EOF' | sfdisk "{disk.device}"
label: dos
start=1MiB, size=512MiB, type=83, bootable
start=513MiB, size=+, type=83
EOF"""
        part_nums = [1, 2]
    else:
        # 计算第三个分区的起始位置 (513MiB + min_system_size)
        # min_system_size 格式如 "8192m"，提取数值部分
        min_size_num = int(''.join(filter(str.isdigit, min_system_size)))
        third_start = 513 + min_size_num
        bash_cmd = f"""cat <<'EOF' | sfdisk "{disk.device}"
label: dos
start=1MiB, size=512MiB, type=83, bootable
start=513MiB, size={min_system_size}, type=83
start={third_start}MiB, size=+, type=83
EOF"""
        part_nums = [1, 2, 3]

    await run(["bash", "-c", bash_cmd])

    # 等待分区出现在 sysfs 中（最多等待 30 秒）
    disk_parts = await get_partitions(disk.device, part_nums, tries=30)
    for partnum, part_device in disk_parts.items():
        logger.info("format_disk_bios2 disk_parts:%s", disk_parts)
        if part_device is None:
            raise InstallError(f"Failed to find partition number {partnum} on {disk.name}")

async def format_disk(disk: Disk, callback: Callable):
    await wipe_disk(disk, callback)

    # Create BIOS boot partition
    await run(["sgdisk", "-a4096", "-n1:0:+1024K", "-t1:EF02", "-A1:set:2", disk.device])

    # Create EFI partition (Even if not used, allows user to switch to UEFI later)
    await run(["sgdisk", "-n2:0:+524288K", "-t2:EF00", disk.device])

    # Create data partition
    await run(["sgdisk", "-n3:0:0", "-t3:BF01", disk.device])

    # Bad hardware is bad, but we've seen a few users
    # state that by the time we run `parted` command
    # down below OR the caller of this function tries
    # to do something with the partition(s), they won't
    # be present. This is almost _exclusively_ related
    # to bad hardware, but we will wait up to 30 seconds
    # for the partitions to show up in sysfs.
    disk_parts = await get_partitions(disk.device, [1, 2, 3], tries=30)
    for partnum, part_device in disk_parts.items():
        if part_device is None:
            raise InstallError(f"Failed to find partition number {partnum} on {disk.name}")

    # if set_pmbr:
    #     await run(["parted", "-s", disk.device, "disk_set", "pmbr_boot", "on"], check=False)


async def create_one_pool(devices):
    await run(
        [
            "zpool", "create", "-f",
            "-o", "ashift=12",
            "-o", "autotrim=on",
            "-o", "compatibility=openzfs-2.3-linux",
            "-O", "acltype=posixacl",
            "-O", "compression=lz4",
            "-O", "relatime=on",
            "-O", "xattr=sa",
            "-m", "none",
            ONE_POOL,
        ] +
        (["mirror"] if len(devices) > 1 else []) +
        devices
    )
    await run(["zfs", "create", "-o", "mountpoint=none", f"{ONE_POOL}/ROOT"])
    # await run(["zfs", "create", "-o", "canmount=noauto", "-o", "mountpoint=/", f"{ONE_POOL}/ROOT/{bootpool}"])
    # await run(["zpool", "set", f"bootfs={ONE_POOL}/ROOT/{bootpool}", ONE_POOL])



async def run_installer(disks, callback, version: str | None = None, language: str | None = None, boot_mode: str | None = None):
    with tempfile.TemporaryDirectory() as src:
        logger.info(f"run_installer: src = {src}")
        await run(["mount", "/cdrom/OneNAS-SCALE.update", src, "-t", "squashfs", "-o", "loop"])
        try:
            params = {
                "disks": disks,
                "json": True,
                "pool_name": ONE_POOL,
                "src": src,
                "version": version,
                "language": language,
                "boot_mode": boot_mode,
            }
            process = await asyncio.create_subprocess_exec(
                "python3", "-m", "onenas_install",
                cwd=src,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if process.stdin:
                process.stdin.write(json.dumps(params).encode("utf-8"))
                process.stdin.close()
            error = None
            stderr = ""
            while True:
                line = await process.stdout.readline() if process.stdout else b""
                if not line:
                    break

                line = line.decode("utf-8", "ignore")

                try:
                    data = json.loads(line)
                except ValueError:
                    stderr += line
                else:
                    if "progress" in data and "message" in data:
                        callback(data["progress"], data["message"])
                    elif "error" in data:
                        error = data["error"]
                    else:
                        raise ValueError(f"Invalid onenas_install JSON: {data!r}")
            await process.wait()

            if error is not None:
                result = error
            else:
                result = stderr

            if process.returncode != 0:
                raise InstallError(result or f"Abnormal installer process termination with code {process.returncode}")
        finally:
            await run(["umount", "-f", src])

def check_boot_mode():
    if os.path.exists("/sys/firmware/efi"):
        return "UEFI"
    else:
        return "BIOS"
