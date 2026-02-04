import os

import textwrap

import asyncio
import subprocess
import tempfile

from .i18n import _

__all__ = ["dialog", "dialog_checklist", "dialog_menu", "dialog_msgbox", "dialog_yesno", "dialog_password"]


async def dialog(args, check=False):
    args = ["dialog"] + args

    process = await asyncio.create_subprocess_exec(*args, stderr=subprocess.PIPE)
    _, stderr = await process.communicate()

    stderr = stderr.decode("utf-8", "ignore")

    if check:
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, args, stderr=stderr)

    return subprocess.CompletedProcess(args, process.returncode, stderr=stderr)


async def dialog_checklist(title, text, items):
    result = await dialog(
        [
            "--clear",
            "--title", title,
            "--checklist", text, "20", "60", "0"
        ] +
        sum(
            [
                [k, v, "off"]
                for k, v in items.items()
            ],
            [],
        )
    )

    if result.returncode == 0:
        return result.stderr.split()
    else:
        return None


async def dialog_menu(title, items):
    result = await dialog(
        [
            "--clear",
            "--title", title,
            "--menu", "", "12", "73", "6"
        ] +
        sum(
            [
                [str(i), title]
                for i, title in enumerate(items.keys(), start=1)
            ],
            [],
        )
    )

    if result.returncode == 0:
        selected_index = int(result.stderr) - 1
        handlers = list(items.values())
        return await handlers[selected_index]()
    else:
        return None


async def dialog_msgbox(title, text):
    # 计算合适的窗口高度
    lines = text.rstrip().splitlines()
    height = min(20, max(8, 4 + len(lines)))
    # 计算合适的窗口宽度（考虑中文字符）
    max_line_len = max(len(line) for line in lines) if lines else 0
    width = min(80, max(60, max_line_len + 10))
    
    await dialog([
        "--clear",
        "--title", title,
        "--msgbox", text,
        str(height), str(width),
    ])


async def dialog_password(title, password_label=None, confirm_label=None):
    """
    显示密码输入对话框
    
    Args:
        title: 对话框标题
        password_label: 密码标签（使用翻译后的文本）
        confirm_label: 确认密码标签（使用翻译后的文本）
    """
    # 使用翻译的默认值
    password_label = password_label or _("password")
    confirm_label = confirm_label or _("confirm_password")
    
    with tempfile.NamedTemporaryFile("w") as dialogrc:
        dialogrc.write(textwrap.dedent("""\
            bindkey formfield TAB FORM_NEXT
            bindkey formfield DOWN FORM_NEXT
            bindkey formfield UP FORM_PREV
            bindkey formbox DOWN FORM_NEXT
            bindkey formbox TAB FORM_NEXT
            bindkey formbox UP FORM_PREV
        """))
        dialogrc.flush()

        while True:
            with tempfile.NamedTemporaryFile("r+") as output:
                fd = os.open(output.name, os.O_WRONLY)
                os.set_inheritable(fd, True)

                process = await asyncio.create_subprocess_exec(
                    *(
                        [
                            "dialog",
                            "--insecure",
                            "--output-fd", f"{fd}",
                            "--visit-items",
                            "--passwordform", title,
                            "10", "70", "0",
                            password_label + ":", "1", "10", "", "0", "30", "25", "50",
                            confirm_label + ":", "2", "10", "", "2", "30", "25", "50",
                        ]
                    ),
                    env=dict(os.environ, DIALOGRC=dialogrc.name),
                    pass_fds=(fd,),
                )
                await process.communicate()
                if process.returncode != 0:
                    return None

                passwords = [p.strip() for p in output.read().splitlines()]
                if len(passwords) != 2 or not passwords[0] or not passwords[1]:
                    await dialog_msgbox(_("error"), _("empty_password"))
                    continue
                elif passwords[0] != passwords[1]:
                    await dialog_msgbox(_("error"), _("password_mismatch"))
                    continue

                return passwords[0]


async def dialog_yesno(title, text) -> bool:
    result = await dialog([
        "--clear",
        "--title", title,
        "--yesno", text,
        "13", "74",
    ])
    return result.returncode == 0
