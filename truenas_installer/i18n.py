"""
Internationalization (i18n) module for TrueNAS Installer
支持多语言切换，目前支持英语和中文
"""

from typing import Dict, Callable

# 当前语言设置
_current_language = "en"

# 翻译字典
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # 主菜单
        "main_menu_title": "{vendor} {version} Console Setup",
        "install_upgrade": "Install/Upgrade",
        "shell": "Shell",
        "reboot_system": "Reboot System",
        "shutdown_system": "Shutdown System",
        "select_language": "Select Language / 选择语言",
        
        # 语言选择
        "language_selection_title": "Select Language / 选择语言",
        "lang_english": "English",
        "lang_chinese": "中文 (Chinese)",
        "language_changed": "Language Changed / 语言已更改",
        "language_changed_msg": "Language has been changed to {lang}. / 语言已更改为 {lang}。",
        
        # 安装相关
        "choose_destination": "Choose Destination Media",
        "no_drives": "No drives available",
        "install_to_drive": "Install {vendor} to a drive. If desired, select multiple drives to provide redundancy. {vendor} installation drive(s) are not available for use in storage pools. Use arrow keys to navigate options. Press spacebar to select.",
        "select_at_least_one_disk": "Select at least one disk to proceed with the installation.",
        "installation": "{vendor} Installation",
        "installation_error": "Installation Error",
        "installation_succeeded": "Installation Succeeded",
        "installation_succeeded_msg": "The {vendor} installation on {disks} succeeded!\\nPlease reboot and remove the installation media.",
        
        # 磁盘相关
        "existing_boot_pool": "Disk(s) {disks} contain existing TrueNAS boot pool, but they were not selected for TrueNAS installation. This configuration will not work unless these disks are erased.",
        "proceed_erase": "Proceed with erasing {disks}?",
        
        # 警告和提示
        "warning": "WARNING:",
        "erase_partitions": "- This erases ALL partitions and data on {disks}.",
        "unavailable_for_pools": "- {disks} will be unavailable for use in storage pools.",
        "note": "NOTE:",
        "recommended_media": "- Installing on SATA, SAS, or NVMe flash media is recommended.\\n  USB flash sticks are discouraged.",
        "proceed_installation": "Proceed with the installation?",
        
        # 认证
        "web_ui_auth_method": "Web UI Authentication Method",
        "auth_truenas_admin": "Administrative user (truenas_admin)",
        "auth_webui": "Configure using Web UI",
        "enter_password": "Enter your \"{username}\" user password. Root password login will be disabled.",
        
        # 密码
        "password": "Password",
        "confirm_password": "Confirm Password",
        "error": "Error",
        "empty_password": "Empty passwords are not allowed.",
        "password_mismatch": "Passwords do not match.",
        
        # 启动相关
        "legacy_boot": "Legacy Boot",
        "allow_efi": "Allow EFI boot? Enter Yes for systems with newer components such as NVMe devices. Enter No when system hardware requires legacy BIOS boot workaround.",
        
        # 按钮和通用
        "yes": "Yes",
        "no": "No",
        "ok": "OK",
        "cancel": "Cancel",
        "back": "Back",
        "next": "Next",
    },
    "zh": {
        # 主菜单
        "main_menu_title": "{vendor} {version} 控制台设置",
        "install_upgrade": "安装/升级",
        "shell": "命令行",
        "reboot_system": "重启系统",
        "shutdown_system": "关闭系统",
        "select_language": "选择语言 / Select Language",
        
        # 语言选择
        "language_selection_title": "选择语言 / Select Language",
        "lang_english": "English (英语)",
        "lang_chinese": "中文 (Chinese)",
        "language_changed": "语言已更改 / Language Changed",
        "language_changed_msg": "语言已更改为 {lang}。 / Language has been changed to {lang}.",
        
        # 安装相关
        "choose_destination": "选择目标设备",
        "no_drives": "没有可用的驱动器",
        "install_to_drive": "安装 {vendor} 到驱动器。如需冗余，可选择多个驱动器。{vendor} 安装驱动器不能用于存储池。使用方向键导航，按空格键选择。",
        "select_at_least_one_disk": "请至少选择一个磁盘以继续安装。",
        "installation": "{vendor} 安装",
        "installation_error": "安装错误",
        "installation_succeeded": "安装成功",
        "installation_succeeded_msg": "{vendor} 已成功安装到 {disks}！\\n请重启并移除安装介质。",
        
        # 磁盘相关
        "existing_boot_pool": "磁盘 {disks} 包含现有的 TrueNAS 启动池，但未选择用于 TrueNAS 安装。除非擦除这些磁盘，否则此配置将无法工作。",
        "proceed_erase": "是否继续擦除 {disks}？",
        
        # 警告和提示
        "warning": "警告：",
        "erase_partitions": "- 这将擦除 {disks} 上的所有分区和数据。",
        "unavailable_for_pools": "- {disks} 将无法用于存储池。",
        "note": "注意：",
        "recommended_media": "- 建议安装在 SATA、SAS 或 NVMe 闪存介质上。\\n  不推荐使用 USB 闪存盘。",
        "proceed_installation": "是否继续安装？",
        
        # 认证
        "web_ui_auth_method": "Web UI 认证方式",
        "auth_truenas_admin": "管理员用户 (truenas_admin)",
        "auth_webui": "使用 Web UI 配置",
        "enter_password": '请输入 "{username}" 用户密码。Root 密码登录将被禁用。',
        
        # 密码
        "password": "密码",
        "confirm_password": "确认密码",
        "error": "错误",
        "empty_password": "不允许使用空密码。",
        "password_mismatch": "密码不匹配。",
        
        # 启动相关
        "legacy_boot": "传统启动",
        "allow_efi": "允许 EFI 启动？对于具有 NVMe 设备等较新组件的系统，请选择是。当系统硬件需要传统 BIOS 启动解决方案时，请选择否。",
        
        # 按钮和通用
        "yes": "是",
        "no": "否",
        "ok": "确定",
        "cancel": "取消",
        "back": "返回",
        "next": "下一步",
    }
}


def set_language(lang: str) -> bool:
    """
    设置当前语言
    
    Args:
        lang: 语言代码，如 "en", "zh"
    
    Returns:
        是否设置成功
    """
    global _current_language
    if lang in TRANSLATIONS:
        _current_language = lang
        return True
    return False


def get_language() -> str:
    """获取当前语言代码"""
    return _current_language


def get_available_languages() -> Dict[str, str]:
    """获取可用语言列表"""
    return {
        "en": TRANSLATIONS["en"]["lang_english"],
        "zh": TRANSLATIONS["zh"]["lang_chinese"],
    }


def _(key: str, **kwargs) -> str:
    """
    翻译函数
    
    Args:
        key: 翻译键
        **kwargs: 格式化参数
    
    Returns:
        翻译后的字符串
    """
    # 获取当前语言的翻译
    translation = TRANSLATIONS.get(_current_language, TRANSLATIONS["en"])
    
    # 获取翻译文本，如果不存在则返回键名
    text = translation.get(key, TRANSLATIONS["en"].get(key, key))
    
    # 格式化参数
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            # 如果格式化失败，返回原始文本
            pass
    
    return text


# 便捷函数，用于创建带翻译的菜单项
def get_menu_items() -> Dict[str, Callable]:
    """
    获取主菜单项（用于动态生成）
    注意：这个函数返回的是键名，实际显示文本需要通过 _() 转换
    """
    return {
        "install_upgrade": None,
        "shell": None,
        "reboot_system": None,
        "shutdown_system": None,
        "select_language": None,
    }
