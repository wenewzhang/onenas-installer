"""
测试程序：显示多语言支持
运行：python -m pytest tests/test_display_languages.py -v -s
或：python tests/test_display_languages.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from onenas_installer.i18n import _, set_language, get_available_languages, get_language


def test_language_switching():
    """测试语言切换功能"""
    print("\n" + "=" * 70)
    print("测试语言切换 / Language Switching Test")
    print("=" * 70)
    
    # 显示可用语言
    print("\n可用语言 / Available Languages:")
    for code, name in get_available_languages().items():
        print(f"  [{code}] {name}")
    
    # 测试英文
    print("\n" + "-" * 70)
    print("测试英文 / Testing English:")
    print("-" * 70)
    set_language("en")
    print(f"  当前语言 / Current: {get_language()}")
    print(f"  主菜单标题 / Main Menu: {_('main_menu_title', vendor='OneNAS', version='25.04')}")
    print(f"  安装/升级 / Install: {_('install_upgrade')}")
    print(f"  选择目标设备 / Choose Destination: {_('choose_destination')}")
    print(f"  安装成功 / Install Success: {_('installation_succeeded')}")
    
    # 测试中文
    print("\n" + "-" * 70)
    print("测试中文 / Testing Chinese:")
    print("-" * 70)
    set_language("zh")
    print(f"  当前语言 / Current: {get_language()}")
    print(f"  主菜单标题 / Main Menu: {_('main_menu_title', vendor='OneNAS', version='25.04')}")
    print(f"  安装/升级 / Install: {_('install_upgrade')}")
    print(f"  选择目标设备 / Choose Destination: {_('choose_destination')}")
    print(f"  安装成功 / Install Success: {_('installation_succeeded')}")
    
    # 测试格式化参数
    print("\n" + "-" * 70)
    print("测试格式化参数 / Testing Format Parameters:")
    print("-" * 70)
    
    set_language("en")
    print(f"  [EN] {_('erase_partitions', disks='sda, sdb')}")
    print(f"  [EN] {_('installation_succeeded_msg', vendor='OneNAS', disks='sda')}")
    
    set_language("zh")
    print(f"  [ZH] {_('erase_partitions', disks='sda, sdb')}")
    print(f"  [ZH] {_('installation_succeeded_msg', vendor='OneNAS', disks='sda')}")
    
    return True


def test_all_translations():
    """测试所有翻译键"""
    print("\n" + "=" * 70)
    print("测试所有翻译键 / Testing All Translation Keys")
    print("=" * 70)
    
    # 主要翻译键列表
    keys = [
        "main_menu_title",
        "install_upgrade",
        "shell",
        "reboot_system",
        "shutdown_system",
        "select_language",
        "choose_destination",
        "no_drives",
        "installation",
        "installation_error",
        "installation_succeeded",
        "warning",
        "note",
        "proceed_installation",
        "web_ui_auth_method",
        "auth_truenas_admin",
        "auth_webui",
        "password",
        "confirm_password",
        "error",
        "empty_password",
        "password_mismatch",
        "legacy_boot",
        "yes",
        "no",
        "ok",
        "cancel",
    ]
    
    print("\n{:<30} {:<35} {:<35}".format("Key", "English", "中文"))
    print("-" * 100)
    
    for key in keys:
        set_language("en")
        en_text = _(key)
        set_language("zh")
        zh_text = _(key)
        
        # 截断长文本
        en_display = en_text[:32] + "..." if len(en_text) > 35 else en_text
        zh_display = zh_text[:32] + "..." if len(zh_text) > 35 else zh_text
        
        print(f"{key:<30} {en_display:<35} {zh_display:<35}")
    
    return True


def main():
    """主函数 - 运行所有测试"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "TrueNAS Installer 多语言测试程序" + " " * 18 + "║")
    print("║" + " " * 15 + "TrueNAS Installer i18n Test Program" + " " * 14 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        test_language_switching()
        test_all_translations()
        
        print("\n")
        print("╔" + "=" * 68 + "╗")
        print("║" + " " * 22 + "🎉 所有测试通过!" + " " * 23 + "║")
        print("║" + " " * 20 + "All tests passed!" + " " * 26 + "║")
        print("╚" + "=" * 68 + "╝")
        print()
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n💥 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
