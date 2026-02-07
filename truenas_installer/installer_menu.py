import asyncio
import os
import sys

import humanfriendly

from .dialog import (
    dialog_checklist,
    dialog_menu,
    dialog_msgbox,
    dialog_password,
    dialog_yesno,
)
from .disks import Disk, list_disks
from .exception import InstallError
from .install import install
from .i18n import _, set_language, get_available_languages, get_language


class InstallerMenu:
    def __init__(self, installer):
        self.installer = installer

    async def run(self):
        await self._main_menu()

    async def _main_menu(self):
        """显示主菜单"""
        # 使用 lambda 来确保每次菜单显示时都使用当前语言的翻译
        menu_items = {
            _("install_upgrade"): self._install_upgrade,
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

    async def _install_upgrade(self):
        while True:
            await self._install_upgrade_internal()
            await self._main_menu()

    async def _install_upgrade_internal(self):
        disks = await list_disks()
        vendor = self.installer.vendor

        if not disks:
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

            if destination_disks is None:
                # Installation cancelled
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
            return False


        try:
            await install(
                self._select_disks(disks, destination_disks),
                self._select_disks(disks, wipe_disks),
                self._callback,
            )
        except InstallError as e:
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
        os._exit(1)

    async def _reboot(self):
        process = await asyncio.create_subprocess_exec("reboot")
        await process.communicate()

    async def _shutdown(self):
        process = await asyncio.create_subprocess_exec("shutdown", "now")
        await process.communicate()

    def _callback(self, progress, message):
        sys.stdout.write(f"[{int(progress * 100)}%] {message}\n")
        sys.stdout.flush()
