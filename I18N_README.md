# TrueNAS Installer 多语言支持

## 概述

TrueNAS Installer 现在支持多语言切换功能，目前支持：
- **English** (英语)
- **中文** (Chinese)

## 功能特性

1. **菜单语言选择**: 在主菜单中添加了"选择语言 / Select Language"选项
2. **即时切换**: 选择语言后，界面会立即显示新的语言
3. **双语显示**: 语言选择菜单同时显示中英文，方便识别

## 使用方式

### 在菜单中选择语言

1. 启动安装程序后，在主菜单中可以看到最后一个选项：**"选择语言 / Select Language"**
2. 选择该选项进入语言选择菜单
3. 选择 **"English"** 或 **"中文 (Chinese)"**
4. 选择后，会自动返回主菜单，所有文本将显示为新选择的语言

### 在代码中使用翻译

```python
from onenas_installer.i18n import _, set_language, get_language

# 设置语言
set_language("zh")  # 切换到中文
set_language("en")  # 切换到英文

# 获取当前语言
current_lang = get_language()  # 返回 "zh" 或 "en"

# 使用翻译
title = _("main_menu_title", vendor="OneNAS", version="25.04")
message = _("installation_succeeded")
```

## 文件结构

```
onenas_installer/
├── i18n.py              # 国际化模块，包含所有翻译
├── installer_menu.py    # 主菜单（已添加语言选择功能）
├── dialog.py            # 对话框（支持国际化）
└── test_display_languages.py  # 多语言测试程序
```

## 添加新语言

要添加新的语言支持，请编辑 `i18n.py` 文件：

1. 在 `TRANSLATIONS` 字典中添加新的语言代码和翻译
2. 在 `get_available_languages()` 中添加新语言

示例：

```python
TRANSLATIONS = {
    "en": { ... },
    "zh": { ... },
    "es": {  # 添加西班牙语
        "main_menu_title": "{vendor} {version} Configuración de Consola",
        "install_upgrade": "Instalar/Actualizar",
        # ... 更多翻译
    }
}
```

## 测试

运行测试程序验证多语言功能：

```bash
# 方法1: 直接运行测试脚本
python onenas_installer/test_display_languages.py

# 方法2: 使用 pytest
python -m pytest onenas_installer/test_display_languages.py -v -s
```

## 技术说明

- 翻译系统使用简单的键值对存储
- 使用 Python 的 `str.format()` 支持动态参数
- 如果当前语言的翻译不存在，会回退到英文
- 所有菜单文本在显示时动态翻译，确保语言切换立即生效
