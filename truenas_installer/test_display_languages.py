"""
测试程序：显示18种语言支持
运行：python -m pytest tests/test_display_languages.py -v -s
或：python tests/test_display_languages.py
"""
import locale
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from truenas_installer.i18n import LANGUAGES, set_language, get_language_name, _


def display_all_languages():
    """显示所有18种语言及其示例翻译"""
    print("=" * 70)
    print("🌍 TrueNAS Installer - 18种语言支持测试")
    print("=" * 70)
    print()
    
    # 示例翻译键
    sample_keys = [
        "menu_install_upgrade",
        "menu_language", 
        "title_error",
        "msg_no_drives",
        "label_password"
    ]
    
    # 保存原始语言
    original_lang = "en"
    
    for idx, (code, name) in enumerate(LANGUAGES.items(), 1):
        print(f"{idx:2d}. {code:3s} - {name}")
        
        # 设置当前语言
        set_language(code)
        
        # 显示该语言的示例翻译
        print("    示例翻译:")
        for key in sample_keys:
            translation = _(key)
            # 截断长文本以便显示
            if len(translation) > 50:
                translation = translation[:47] + "..."
            print(f"      • {key:25s} → {translation}")
        
        print()
    
    # 恢复原始语言
    set_language(original_lang)
    
    print("=" * 70)
    print(f"✅ 成功显示 {len(LANGUAGES)} 种语言")
    print("=" * 70)


def test_language_count():
    """测试语言数量是否为18"""
    print("\n📊 语言数量测试")
    print("-" * 40)
    count = len(LANGUAGES)
    print(f"定义的语言数量: {count}")
    assert count == 18, f"期望18种语言，但找到了{count}种"
    print("✅ 语言数量正确: 18")
    return True


def test_all_languages_can_be_set():
    """测试所有语言都可以被设置"""
    print("\n🔧 语言设置测试")
    print("-" * 40)
    
    original_lang = get_language_name()
    
    for code in LANGUAGES.keys():
        result = set_language(code)
        assert result is True, f"无法设置语言: {code}"
        current = get_language_name()
        print(f"  ✅ {code:3s} → {current}")
    
    # 恢复
    set_language("en")
    print("✅ 所有语言设置成功")
    return True


def test_unicode_display():
    """测试各种语言的Unicode字符显示"""
    print("\n🔤 Unicode字符显示测试")
    print("-" * 40)
    
    test_cases = [
        ("zh", "中文"),
        ("ja", "日本語"),
        ("ko", "한국어"),
        ("ar", "العربية"),
        ("hi", "हिन्दी"),
        ("bn", "বাংলা"),
        ("ru", "Русский"),
        ("ur", "اردو"),
        ("th", "ไทย"),
    ]
    
    for code, expected_native in test_cases:
        set_language(code)
        name = get_language_name(code)
        assert expected_native in name, f"{code} 应该包含 {expected_native}"
        print(f"  ✅ {code}: {name}")
    
    set_language("en")
    print("✅ Unicode显示测试通过")
    return True



def test_show_locale_call():
    # 强制设置 LC_ALL 环境变量
    try:
        locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
    except locale.Error:
        print("系统仍未识别 zh_CN.UTF-8，请检查 locale -a 的输出")

    # 检查 Python 默认的文件系统和终端编码
    print(f"文件系统编码: {sys.getfilesystemencoding()}")
    print(f"标准输出编码: {sys.stdout.encoding}")

def test_translation_samples():
    """测试各种语言的翻译样本"""
    print("\n📝 翻译样本测试")
    print("-" * 40)
    
    samples = [
        ("en", "menu_install_upgrade", "Install/Upgrade"),
        ("zh", "menu_install_upgrade", "安装/升级"),
        ("es", "menu_install_upgrade", "Instalar/Actualizar"),
        ("fr", "menu_install_upgrade", "Installer/Mettre"),
        ("de", "menu_install_upgrade", "Installieren/Upgrade"),
        ("ja", "menu_language", "言語"),
        ("ko", "menu_language", "언어"),
    ]
    
    for code, key, expected in samples:
        set_language(code)
        result = _(key)
        assert expected in result, f"{code}.{key} 应该包含 '{expected}', 但得到 '{result}'"
        print(f"  ✅ {code}: {result}")
    
    set_language("en")
    print("✅ 翻译样本测试通过")
    return True


def main():
    """主函数 - 运行所有测试"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "TrueNAS Installer 语言测试程序" + " " * 18 + "║")
    print("║" + " " * 15 + "TrueNAS Installer Language Test Program" + " " * 14 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    test_show_locale_call()
    try:
        # 运行显示测试
        display_all_languages()
        
        # 运行功能测试
        test_language_count()
        test_all_languages_can_be_set()
        test_unicode_display()
        test_translation_samples()
        
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
