import asyncio
import os
import sys

import humanfriendly

from .dialog import (
    dialog_checklist,
    dialog_inputbox,
    dialog_menu,
    dialog_msgbox,
    dialog_password,
    dialog_radiolist,
    dialog_yesno,
)
from .disks import Disk, list_disks
from .exception import InstallError
from .install import install, upgrade
from .i18n import _, set_language, get_available_languages, get_language
from .logger import logger


class InstallerMenu:
    def __init__(self, installer):
        self.installer = installer

    async def run(self):
        await self._main_menu()

    async def _main_menu(self):
        """显示主菜单"""
        logger.info("Displaying main menu")
        # 使用 lambda 来确保每次菜单显示时都使用当前语言的翻译
        menu_items = {
            _("install"): self._install,
            _("upgrade"): self._upgrade,
            _("shell"): self._shell,
            _("reboot_system"): self._reboot,
            _("shutdown_system"): self._shutdown,
            _("select_language"): self._select_language,
        }
        
        await dialog_menu(
            _("main_menu_title", vendor=self.installer.vendor, version=self.installer.version),
            menu_items,
        )
        
        # 菜单返回后重新显示（支持语言切换后立即刷新）
        await self._main_menu()

    async def _select_language(self):
        """语言选择菜单"""
        logger.info("Displaying language selection menu")
        languages = get_available_languages()
        
        # 构建语言选择菜单项
        lang_items = {}
        for lang_code, lang_name in languages.items():
            # 使用闭包保存 lang_code
            async def make_select_lang(code):
                async def select_lang():
                    old_lang = get_language()
                    set_language(code)
                    if old_lang != code:
                        await dialog_msgbox(
                            _("language_changed"),
                            _("language_changed_msg", lang=languages[code])
                        )
                    # 返回 True 表示需要刷新菜单
                    return True
                return select_lang
            lang_items[lang_name] = await make_select_lang(lang_code)
        
        result = await dialog_menu(
            _("language_selection_title"),
            lang_items,
        )
        
        # 如果选择了语言，result 会是 True（表示需要刷新）
        if result:
            # 返回主菜单以刷新显示
            return

    async def _install(self):
        while True:
            await self._install_internal()
            await self._main_menu()

    async def _upgrade(self):
        """系统升级功能（待实现）"""
        logger.info("Upgrade feature not implemented yet")
        await dialog_msgbox(
            _("upgrade"),
            _("upgrade_not_implemented")
        )

    async def _install_internal(self):
        logger.info("Starting install/upgrade process")
        disks = await list_disks()
        vendor = self.installer.vendor
        logger.info(f"Detected disks: {[d.name for d in disks]}")

        if not disks:
            logger.warning("No drives detected")
            await dialog_msgbox(_("choose_destination"), _("no_drives"))
            return False

        while True:
            destination_disks = await dialog_checklist(
                _("choose_destination"),
                _("install_to_drive", vendor=vendor),
                {
                    disk.name: " ".join(
                        [
                            disk.model[:15].ljust(15, " "),
                            disk.label[:15].ljust(15, " "),
                            "--",
                            humanfriendly.format_size(disk.size, binary=True),
                        ]
                    )
                    for disk in disks
                },
            )

            if destination_disks is not None:
                logger.info(f"User selected destination disks: {destination_disks}")

            if destination_disks is None:
                # Installation cancelled
                logger.info("Installation cancelled by user")
                return False

            if not destination_disks:
                await dialog_msgbox(
                    _("choose_destination"),
                    _("select_at_least_one_disk"),
                )
                continue

            wipe_disks = [
                disk.name
                for disk in disks
                if (
                    any(
                        zfs_member.pool == "one-pool"
                        for zfs_member in disk.zfs_members
                    )
                    and disk.name not in destination_disks
                )
            ]
            if wipe_disks:
                # The presence of multiple `boot-pool` disks with different guids leads to boot pool import error
                text = "\n".join(
                    [
                        _("existing_one_pool", disks=", ".join(wipe_disks), vendor=vendor),
                        "",
                        _("proceed_erase", disks=", ".join(wipe_disks)),
                    ]
                )
                if not await dialog_yesno(_("installation", vendor=vendor), text):
                    continue

            break

        text = "\n".join(
            [
                _("warning"),
                _("erase_partitions", disks=", ".join(sorted(wipe_disks + destination_disks))),
                _("unavailable_for_pools", disks=", ".join(destination_disks)),
                "",
                _("note"),
                _("recommended_media"),
                "",
                _("proceed_installation"),
            ]
        )
        if not await dialog_yesno(_("installation", vendor=self.installer.vendor), text):
            logger.info("Installation cancelled by user at confirmation dialog")
            return False

        # 根据 disk 大小，让用户选择分区方式
        # 获取选中磁盘的总容量
        selected_disks = [d for d in disks if d.name in destination_disks]
        total_size = sum(d.size for d in selected_disks)
        total_size_str = humanfriendly.format_size(total_size, binary=True)
        # 获取最小容量硬盘并按百分比计算
        min_disk = min(selected_disks, key=lambda d: d.size)
        min_disk_size = min_disk.size
        min_disk_size_str = humanfriendly.format_size(min_disk_size, binary=True)

        # 让用户选择分区方式
        partition_choice = await dialog_radiolist(
            _("partition_title"),
            _("partition_choice_text", total_size=total_size_str),
            {
                "full": (_("use_full_disk"), True),
                "percentage": (_("use_percentage"), False),
            },
        )

        if partition_choice is None:
            return False  # 用户取消

        # 存储用户的选择和系统分区大小
        use_full_disk = (partition_choice == "full")
        system_partition_percentage = 100  # 默认使用全部
        min_disk_system_size = min_disk_size * system_partition_percentage // 100
        min_disk_system_size_str = humanfriendly.format_size(min_disk_system_size, binary=True)
        
        if not use_full_disk:
            # 用户选择按百分比，询问百分比
            while True:
                percentage_input = await dialog_inputbox(
                    _("partition_percentage_title"),
                    _("enter_percentage", total_size=total_size_str),
                    "50",
                )
                
                if percentage_input is None:
                    return False  # 用户取消
                
                try:
                    percentage = int(percentage_input)
                    if 1 <= percentage <= 100:
                        # 计算分区容量
                        system_size = total_size * percentage // 100
                        system_size_str = humanfriendly.format_size(system_size, binary=True)
                        remaining_size = total_size - system_size
                        remaining_size_str = humanfriendly.format_size(remaining_size, binary=True)
                        
                        min_disk_system_size = min_disk_size * percentage // 100
                        min_disk_system_size_str = humanfriendly.format_size(min_disk_system_size, binary=True)                        
                                                
                        # 显示计算结果并让用户确认
                        confirm_text = _(
                            "partition_size_preview",
                            total_size=total_size_str,
                            percentage=percentage,
                            system_size=system_size_str,
                            remaining_size=remaining_size_str,
                            min_disk_name=min_disk.name,
                            min_disk_size=min_disk_size_str,
                            min_disk_system_size=min_disk_system_size_str,
                        )
                        
                        if await dialog_yesno(_("confirm_partition_size"), confirm_text):
                            system_partition_percentage = percentage
                            break
                        # 用户选择重新输入，继续循环
                    else:
                        await dialog_msgbox(_("error"), _("percentage_range_error"))
                except ValueError:
                    await dialog_msgbox(_("error"), _("percentage_invalid_error"))

        # 将选择存入变量（供后续安装使用）
        # use_full_disk: 是否使用整个磁盘
        # system_partition_percentage: 系统分区占用的百分比

        try:
            logger.info(f"Starting installation to disks: {destination_disks}")
            logger.info(f"Starting installation wipe_disks: {wipe_disks}")
            await install(
                self._select_disks(disks, destination_disks),
                self._select_disks(disks, wipe_disks),
                system_partition_percentage,
                min_disk_system_size,
                self._callback,
                self.installer.version,
                get_language(),
            )
            logger.info("Installation completed successfully")
        except InstallError as e:
            logger.error(f"Installation failed: {e.message}")
            await dialog_msgbox(_("installation_error"), e.message)
            return False

        await dialog_msgbox(
            _("installation_succeeded"),
            _(
                "installation_succeeded_msg",
                vendor=self.installer.vendor,
                disks=", ".join(destination_disks)
            ),
        )
        return True

    def _select_disks(self, disks: list[Disk], disks_names: list[str]):
        disks_dict = {disk.name: disk for disk in disks}
        return [disks_dict[disk_name] for disk_name in disks_names]

    async def _authentication_truenas_admin(self):
        return await self._authentication_password(
            "truenas_admin",
            _("enter_password", username="truenas_admin"),
        )

    async def _authentication_password(self, username, title):
        password = await dialog_password(title)
        if password is None:
            return False

        return {"username": username, "password": password}

    async def _authentication_webui(self):
        return None

    async def _shell(self):
        logger.info("User exited to shell")
        os._exit(1)

    async def _reboot(self):
        logger.info("System reboot requested")
        process = await asyncio.create_subprocess_exec("reboot")
        await process.communicate()

    async def _shutdown(self):
        logger.info("System shutdown requested")
        process = await asyncio.create_subprocess_exec("shutdown", "now")
        await process.communicate()

    def _callback(self, progress, message):
        logger.info(f"[{int(progress * 100)}%] {message}")
        sys.stdout.write(f"[{int(progress * 100)}%] {message}\n")
        sys.stdout.flush()
