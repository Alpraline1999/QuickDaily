import ctypes
import os
import re
import sys
import json
from PIL import Image
from datetime import datetime
import tkinter as tk
import tkinter.font as tkFont
from customtkinter import (
    CTk,
    CTkLabel,
    CTkFont,
    CTkFrame,
    CTkButton,
    CTkEntry,
    CTkTextbox,
    CTkImage,
    set_appearance_mode,
    set_default_color_theme,
    filedialog,
)


def resource_path(relative_path):
    """
    获取资源的绝对路径：开发环境用正常路径，打包后用临时目录路径
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)  # type: ignore
    return os.path.join(os.path.abspath("."), relative_path)


class ToolTip:
    def __init__(self, widget, tipFont, text, scale, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay  # 延迟显示（毫秒）
        self.tipwindow = None
        self.id = None
        self.tipFont = tipFont
        self.scale = scale

        widget.bind("<Enter>", self.schedule)
        widget.bind("<Leave>", self.hide)
        widget.bind("<Motion>", self.move)

    def schedule(self, event=None):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show(self, event=None):
        if self.tipwindow or not self.text:
            return

        # 获取鼠标全局位置
        x = self.widget.winfo_pointerx() + int(10 * self.scale)
        y = self.widget.winfo_pointery() + int(20 * self.scale)

        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.attributes("-topmost", True)
        tw.configure(bg="#808080")  # 设置一个将被当作透明的颜色
        tw.wm_attributes("-transparentcolor", "#808080")  # 让 pink 变成透明
        tw.wm_overrideredirect(True)  # 无边框
        tw.wm_geometry(f"+{x}+{y}")

        label = CTkLabel(
            master=tw,
            text=self.text,
            compound="top",
            anchor="center",
            justify="left",
            text_color=("#030303", "#ffffff"),
            fg_color=("#f5f5f5", "#555759"),
            bg_color="transparent",
            pady=0,
            padx=0,
            wraplength=0,
            corner_radius=8,
            font=CTkFont(
                family=self.tipFont,
                slant="roman",
                underline=False,
                overstrike=False,
                size=13,
                weight="normal",
            ),
        )
        label.pack(ipadx=0, ipady=0)

    def hide(self, event=None):
        self.unschedule()
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

    def move(self, event):
        if self.tipwindow:
            self.hide()
            self.schedule()

    def setText(self, text):
        self.text = text


class App(CTk):
    def get_available_fonts(self):
        root = tk.Tk()
        root.withdraw()
        fonts = list(tkFont.families())
        root.destroy()
        return fonts

    def select_font(self, preferred_fonts):
        available = self.get_available_fonts()
        for f in preferred_fonts:
            if f in available:
                return f
        return "Arial"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ----------------------------------#
        #               常量
        # ----------------------------------#
        self.fontFamily = self.select_font(
            [
                "霞鹜文楷等宽 Medium",
                "霞鹜文楷等宽",
                "微软雅黑",
                "宋体",
                "Segoe UI",
                "Arial",
            ]
        )
        self.btnThemeIcons = {
            "light": "./assets/sun.png",
            "dark": "./assets/moon.png",
        }
        self.btnThemeToolTips = {
            "light": "切换至深色模式",
            "dark": "切换至浅色模式",
        }
        self.btnTimeStampIcons = {
            True: "./assets/timer.png",
            False: "./assets/timer-off.png",
        }
        self.btnTimeStampToolTips = {
            True: "关闭时间戳",
            False: "开启时间戳",
        }
        self.initDir = "./init.json"
        self.scale = self.get_dpi()
        self.DailyName = ""
        self.DailyPath = ""

        # ----------------------------------#
        #             可保存变量
        # ----------------------------------#
        if os.path.exists(self.initDir):
            with open(self.initDir, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.theme = (
                data["theme"]
                if ("theme" in data) and (data["theme"] in ["light", "dark"])
                else "light"
            )
            self.ifTimeStamp = (
                data["ifTimeStamp"]
                if ("ifTimeStamp" in data) and (data["ifTimeStamp"] in [True, False])
                else False
            )
            self.ifCollapsed = (
                data["ifCollapsed"]
                if ("ifCollapsed" in data) and (data["ifCollapsed"] in [True, False])
                else False
            )
            self.VaultDir = data["VaultDir"] if "VaultDir" in data else ""
            self.DailyFormat = data["DailyFormat"] if "DailyFormat" in data else ""
            self.BlockName = data["BlockName"] if "BlockName" in data else ""
            self.QuickAddText = data["QuickAddText"] if "QuickAddText" in data else ""
        else:
            self.theme = "light"
            self.ifTimeStamp = False
            self.ifCollapsed = False
            self.VaultDir = ""
            self.DailyFormat = ""
            self.BlockName = ""
            self.QuickAddText = ""

        # ----------------------------------#
        #             窗口布局
        # ----------------------------------#
        self.FrameQuickAdd = CTkFrame(
            master=self,
            bg_color="transparent",
            fg_color=("#dcdcdc", "#2b2b2b"),
            corner_radius=10,
            border_width=0,
        )
        self.FrameQuickAdd.pack(pady=(5, 5), expand=1, fill="both", padx=5)
        self.TextBoxQuickAdd = CTkTextbox(
            master=self.FrameQuickAdd,
            border_spacing=3,
            corner_radius=10,
            bg_color="transparent",
            fg_color=("#F9F9FA", "#46484a"),
            font=CTkFont(family=self.fontFamily, size=15),
        )
        self.TextBoxQuickAdd._textbox.config(undo=True, maxundo=100)
        self.TextBoxQuickAdd.pack(pady=(5, 0), expand=1, fill="both", padx=5)
        self.FrameQuickAddButton = CTkFrame(
            master=self.FrameQuickAdd,
            bg_color="transparent",
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
        )
        self.FrameQuickAddButton.pack(fill="both", padx=5, pady=(5, 5), side="bottom")
        self.LabelDailyName = CTkLabel(
            master=self.FrameQuickAddButton,
            text=self.DailyName,
            compound="top",
            anchor="w",
            justify="left",
            width=60,
            height=28,
            fg_color="transparent",
            bg_color="transparent",
            pady=0,
            padx=0,
            wraplength=0,
            corner_radius=0,
            font=CTkFont(
                family=self.fontFamily,
                slant="roman",
                underline=False,
                overstrike=False,
                size=15,
                weight="normal",
            ),
        )
        self.LabelDailyName.pack(padx=(20, 5), fill="y", pady=2, side="left")
        self.ButtonQuickAdd = CTkButton(
            master=self.FrameQuickAddButton,
            text="随手记",
            compound="top",
            anchor="center",
            hover=True,
            state="normal",
            corner_radius=15,
            border_width=0,
            border_spacing=0,
            width=60,
            height=30,
            fg_color=("#24aca9", "#29c7c2"),
            text_color=("gray98", "#46484a"),
            hover_color=("#29c7c2", "#24aca9"),
            font=CTkFont(family=self.fontFamily, size=15),
            command=self.on_click_ButtonQuickAdd,
        )
        self.ButtonQuickAdd.pack(fill="y", padx=(5, 20), pady=(6, 5), side="right")
        self.FrameCollapse = CTkFrame(
            master=self,
            corner_radius=5,
            height=12,
            fg_color=("gray86", "#2b2b2b"),
            bg_color="transparent",
        )
        self.FrameCollapse.pack(pady=(0, 5), fill="x", padx=5)
        self.ButtonCollapse = CTkButton(
            master=self.FrameCollapse,
            text=" ",
            compound="top",
            anchor="center",
            hover=True,
            state="normal",
            corner_radius=5,
            border_width=0,
            border_spacing=0,
            width=80,
            height=10,
            fg_color=("gray86", "#2b2b2b"),
            text_color=("#000000", "#ffffff"),
            hover_color=("#29c7c2", "#24aca9"),
            bg_color="transparent",
            font=CTkFont(family=self.fontFamily, size=2, weight='bold'),
            command=lambda: self.on_click_ButtonCollapse(),
        )
        self.ButtonCollapse.pack(pady=(0, 0), fill="both", padx=10)
        self.FrameSetting = CTkFrame(
            master=self,
            corner_radius=10,
            fg_color=("gray86", "#2b2b2b"),
            bg_color="transparent",
        )
        self.FrameSetting.pack(pady=(0, 5), fill="both", padx=5)
        self.FrameVaultDir = CTkFrame(
            master=self.FrameSetting,
            bg_color="transparent",
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
        )
        self.FrameVaultDir.pack(pady=(7, 0), fill="x")
        self.LabelVaultDir = CTkLabel(
            master=self.FrameVaultDir,
            text="日记路径",
            compound="top",
            anchor="w",
            justify="left",
            width=60,
            height=28,
            fg_color="transparent",
            bg_color="transparent",
            pady=0,
            padx=0,
            wraplength=0,
            corner_radius=0,
            font=CTkFont(
                family=self.fontFamily,
                slant="roman",
                underline=False,
                overstrike=False,
                size=15,
                weight="normal",
            ),
        )
        self.LabelVaultDir.pack(padx=(8, 5), fill="y", pady=2, side="left")
        self.EntryVaultDir = CTkEntry(
            master=self.FrameVaultDir,
            placeholder_text="Obsidian 日记文件夹",
            justify="left",
            width=340,
            corner_radius=15,
            border_width=0,
            height=30,
            fg_color=("#F9F9FA", "#46484a"),
            font=CTkFont(family=self.fontFamily, size=15),
        )
        self.EntryVaultDir.pack(pady=(2, 2), fill="y", padx=5, side="left")
        self.ButtonVaultDir = CTkButton(
            master=self.FrameVaultDir,
            text="选择",
            compound="top",
            anchor="center",
            hover=True,
            state="normal",
            corner_radius=15,
            border_width=0,
            border_spacing=0,
            width=60,
            height=30,
            fg_color=("#24aca9", "#29c7c2"),
            text_color=("gray98", "#46484a"),
            hover_color=("#29c7c2", "#24aca9"),
            font=CTkFont(family=self.fontFamily, size=15),
            command=self.on_click_ButtonVaultDir,
        )
        self.ButtonVaultDir.pack(side="left", fill="y", padx=5, pady=2)
        self.ButtonTheme = CTkButton(
            master=self.FrameVaultDir,
            width=30,
            height=30,
            image=CTkImage(
                Image.open(resource_path(self.btnThemeIcons[self.theme])),
                size=(16, 16),
            ),
            anchor="center",
            text="",
            corner_radius=8,
            fg_color=("#dcdcdc", "#A1A1A1"),
            text_color=("#ffffff", "#030303"),
            hover_color=("#bebebe", "#818181"),
            border_color=("#c3c3c3", "#818181"),
            border_width=2,
            text_color_disabled=("gray78", "gray68"),
            font=CTkFont(family=self.fontFamily),
            command=self.on_click_ButtonTheme,
        )
        self.ButtonTheme.pack(fill="both", padx=(0, 10), pady=2, side="right")
        self.ButtonTimeStamp = CTkButton(
            master=self.FrameVaultDir,
            width=30,
            height=30,
            image=CTkImage(
                Image.open(resource_path(self.btnTimeStampIcons[self.ifTimeStamp])),
                size=(16, 16),
            ),
            anchor="center",
            text="",
            corner_radius=8,
            fg_color=("#dcdcdc", "#A1A1A1"),
            text_color=("#ffffff", "#030303"),
            hover_color=("#bebebe", "#818181"),
            border_color=("#c3c3c3", "#818181"),
            border_width=2,
            text_color_disabled=("gray78", "gray68"),
            font=CTkFont(family=self.fontFamily),
            command=self.on_click_ButtonTimeStamp,
        )
        self.ButtonTimeStamp.pack(fill="both", padx=(0, 10), pady=2, side="right")
        self.FrameDailyFormat = CTkFrame(
            master=self.FrameSetting,
            bg_color="transparent",
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
        )
        self.FrameDailyFormat.pack(pady=(2, 2), fill="x")
        self.LabelDailyFormat = CTkLabel(
            master=self.FrameDailyFormat,
            text="日记格式",
            compound="top",
            anchor="w",
            justify="left",
            width=60,
            height=28,
            fg_color="transparent",
            bg_color="transparent",
            pady=0,
            padx=0,
            wraplength=0,
            corner_radius=0,
            font=CTkFont(
                family=self.fontFamily,
                slant="roman",
                underline=False,
                overstrike=False,
                size=15,
                weight="normal",
            ),
        )
        self.LabelDailyFormat.pack(padx=(8, 5), fill="y", pady=2, side="left")
        self.EntryDailyFormat = CTkEntry(
            master=self.FrameDailyFormat,
            placeholder_text=r"如：“{YYYY}-{MM}-{DD}”",
            justify="left",
            width=240,
            corner_radius=15,
            border_width=0,
            height=30,
            fg_color=("#F9F9FA", "#46484a"),
            font=CTkFont(family=self.fontFamily, size=15),
        )
        self.EntryDailyFormat.pack(pady=(2, 2), fill="y", padx=5, side="left")
        self.ButtonDailyName = CTkButton(
            master=self.FrameDailyFormat,
            text="确定",
            compound="top",
            anchor="center",
            hover=True,
            state="normal",
            corner_radius=15,
            border_width=0,
            border_spacing=0,
            width=60,
            height=30,
            fg_color=("#24aca9", "#29c7c2"),
            text_color=("gray98", "#46484a"),
            hover_color=("#29c7c2", "#24aca9"),
            font=CTkFont(family=self.fontFamily, size=15),
            command=self.on_click_ButtonDailyFormat,
        )
        self.ButtonDailyName.pack(side="left", fill="y", padx=5, pady=2)
        self.FrameBlockName = CTkFrame(
            master=self.FrameSetting,
            bg_color="transparent",
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
        )
        self.FrameBlockName.pack(pady=(0, 7), fill="x")
        self.LabelBlockName = CTkLabel(
            master=self.FrameBlockName,
            text="块标题",
            compound="top",
            anchor="w",
            justify="left",
            width=60,
            height=28,
            fg_color="transparent",
            bg_color="transparent",
            pady=0,
            padx=0,
            wraplength=0,
            corner_radius=0,
            font=CTkFont(
                family=self.fontFamily,
                slant="roman",
                underline=False,
                overstrike=False,
                size=15,
                weight="normal",
            ),
        )
        self.LabelBlockName.pack(padx=(8, 5), fill="y", pady=2, side="left")
        self.EntryBlockName = CTkEntry(
            master=self.FrameBlockName,
            placeholder_text="如：“###  日常记录”",
            justify="left",
            width=240,
            corner_radius=15,
            border_width=0,
            height=30,
            fg_color=("#F9F9FA", "#46484a"),
            font=CTkFont(family=self.fontFamily, size=15),
        )
        self.EntryBlockName.pack(pady=(2, 2), fill="y", padx=5, side="left")
        self.ButtonBlockName = CTkButton(
            master=self.FrameBlockName,
            text="确定",
            compound="top",
            anchor="center",
            hover=True,
            state="normal",
            corner_radius=15,
            border_width=0,
            border_spacing=0,
            width=60,
            height=30,
            fg_color=("#24aca9", "#29c7c2"),
            text_color=("gray98", "#46484a"),
            hover_color=("#29c7c2", "#24aca9"),
            font=CTkFont(family=self.fontFamily, size=15),
            command=self.on_click_ButtonBlockName,
        )
        self.ButtonBlockName.pack(side="left", fill="y", padx=5, pady=2)

        # ----------------------------------#
        #             控件样式
        # ----------------------------------#
        self.ToolTipButtonQuickAdd = ToolTip(
            self.ButtonQuickAdd,
            self.fontFamily,
            "Ctrl + S",
            self.scale,
        )
        self.ToolTipButtonTimeStamp = ToolTip(
            self.ButtonTimeStamp,
            self.fontFamily,
            self.btnTimeStampToolTips[self.ifTimeStamp],
            self.scale,
        )
        self.ToolTipButtonTheme = ToolTip(
            self.ButtonTheme,
            self.fontFamily,
            self.btnThemeToolTips[self.theme],
            self.scale,
        )
        self.ToolTipButtonCollapse = ToolTip(
            self.ButtonCollapse,
            self.fontFamily,
            "折叠/展开设置区",
            self.scale,
        )
        if self.VaultDir != "":
            self.EntryVaultDir.insert(0, self.VaultDir)
            self.EntryVaultDir.configure(state="disabled")
        if self.DailyFormat != "":
            self.EntryDailyFormat.insert(0, self.DailyFormat)
        if self.BlockName != "":
            self.EntryBlockName.insert(0, self.BlockName)
            self.parseDailyPath()
        self.set_collapse_state()  # 初始化折叠状态
        if self.ifTimeStamp:  # 初始化时间戳状态
            self.set_time_stamp()
        if self.theme == "dark":  # 初始化主题状态
            self.set_theme()

        self.TextBoxQuickAdd.bind(
            "<Control-s>",
            lambda event: self.on_click_ButtonQuickAdd(),
        )
        self.EntryDailyFormat.bind(
            "<Return>",
            lambda event: self.on_click_ButtonDailyFormat(),
        )
        self.EntryBlockName.bind(
            "<Return>",
            lambda event: self.on_click_ButtonBlockName(),
        )

    def show_info_popup(
        self, message: str = "", type: str = "info", duration: int = 1500
    ):
        # if type == "info":
        text_light_color = "#000000"
        text_dark_color = "#ffffff"
        # elif type == "error":
        #     text_light_color = "#ff7d7d"
        #     text_dark_color = "#ff7a7a"
        # elif type == "warning":
        #     text_light_color = "#ffea8e"
        #     text_dark_color = "#ffe056"
        # else:
        #     text_light_color = "#005ec2"
        #     text_dark_color = "#469fff"

        # 创建独立窗口
        popup = tk.Toplevel()
        popup.title("")
        popup_x = 160
        popup_y = 30
        popup.geometry(f"{popup_x}x{popup_y}")
        popup.resizable(False, False)
        popup.attributes("-topmost", True)
        popup.configure(bg="#808080")  # 设置一个将被当作透明的颜色
        popup.wm_attributes("-transparentcolor", "#808080")  # 让 pink 变成透明
        popup.wm_overrideredirect(True)  # 无边框
        # 更新几何信息
        self.update_idletasks()
        popup.update_idletasks()
        root_x = self.winfo_rootx()
        root_y = self.winfo_rooty()
        root_w = self.winfo_width()
        root_h = self.winfo_height()
        scale = self.tk.call("tk", "scaling")
        # 计算相对 root 的靠上居中位置
        x = root_x + (root_w - int(popup_x * self.scale)) // 2
        y = root_y + int(30 * self.scale)

        popup.geometry(f"+{x}+{y}")
        popup.wm_geometry(f"+{x}+{y}")

        # 信息标签
        label = CTkLabel(
            master=popup,
            text=message,
            compound="top",
            anchor="center",
            justify="left",
            text_color=(text_light_color, text_dark_color),
            fg_color=("#dcdcdc", "#2b2b2b"),
            bg_color="transparent",
            pady=0,
            padx=0,
            wraplength=0,
            corner_radius=8,
            font=CTkFont(
                family=self.fontFamily,
                slant="roman",
                underline=False,
                overstrike=False,
                size=15,
                weight="bold",
            ),
        )
        label.pack(ipadx=0, ipady=0, expand=True)

        popup.after(duration, popup.destroy)  # 自动销毁

    def saveSetting(self):
        data = {
            "theme": self.theme,
            "ifTimeStamp": self.ifTimeStamp,
            "ifCollapsed": self.ifCollapsed,
            "VaultDir": self.VaultDir,
            "DailyFormat": self.DailyFormat,
            "BlockName": self.BlockName,
            "QuickAddText": self.QuickAddText,
        }
        with open(self.initDir, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def on_click_ButtonCollapse(self):
        self.ifCollapsed = not self.ifCollapsed
        self.set_collapse_state()
        self.update_idletasks()
        self.saveSetting()  # 保存折叠状态

    def set_collapse_state(self):
        if self.ifCollapsed:
            self.FrameSetting.pack_forget()
        else:
            self.FrameSetting.pack(fill="x", pady=(5, 5), padx=5)

    def on_click_ButtonTheme(self):
        if self.theme == "light":
            self.theme = "dark"
        elif self.theme == "dark":
            self.theme = "light"
        else:
            self.show_info_popup("主题配置错误", "error")

        self.set_theme()
        self.saveSetting()

    def set_theme(self):
        set_appearance_mode(self.theme)
        self.ButtonTheme.configure(
            image=CTkImage(
                Image.open(resource_path(self.btnThemeIcons[self.theme])),
                size=(16, 16),
            )
        )
        self.ToolTipButtonTheme.setText(self.btnThemeToolTips[self.theme])

    def on_click_ButtonTimeStamp(self):
        self.ifTimeStamp = not self.ifTimeStamp
        self.set_time_stamp()
        self.saveSetting()

    def set_time_stamp(self):
        self.ButtonTimeStamp.configure(
            image=CTkImage(
                Image.open(resource_path(self.btnTimeStampIcons[self.ifTimeStamp])),
                size=(16, 16),
            )
        )
        self.ToolTipButtonTimeStamp.setText(self.btnTimeStampToolTips[self.ifTimeStamp])

    def on_click_ButtonVaultDir(self):
        tempDir = filedialog.askdirectory()
        if tempDir == "":
            self.show_info_popup("未选择日记文件夹", "warning")
            return

        self.VaultDir = tempDir
        self.EntryVaultDir.configure(state="normal")
        self.EntryVaultDir.delete(0, "end")
        self.EntryVaultDir.insert(0, self.VaultDir)
        self.EntryVaultDir.configure(state="disabled")
        self.saveSetting()

    def on_click_ButtonDailyFormat(self):
        if self.EntryDailyFormat.get() == "":
            self.show_info_popup("请先设置日记格式", "warning")
            self.EntryDailyFormat.insert(0, self.DailyFormat)
            self.focus_set()
            return

        self.DailyFormat = self.EntryDailyFormat.get()
        if self.parseDailyPath() == -1:
            return

        if self.DailyFormat != "":
            self.saveSetting()

    def parseDailyPath(self):
        self.DailyName = self.parseDailyFormat() + ".md"
        self.DailyPath = os.path.join(self.VaultDir, self.DailyName)
        if not os.path.exists(self.DailyPath):
            self.show_info_popup("日记文件不存在", "error")
            self.LabelDailyName.configure(text="")
            return -1
        self.LabelDailyName.configure(text=self.DailyName)

    def parseDailyFormat(self, dt: datetime = None, lang: str = "zh") -> str:  # type: ignore
        mapping = {
            "{YYYY}": "%Y",
            "{YY}": "%y",
            "{MM}": "%m",
            "{DDDD}": "%j",
            # "{DDD}": "%j",
            "{DD}": "%d",
            "{dddd}": "%A",
            "{ddd}": "%a",
            "{dd}": "%d",
            "{d}": "%w",
            "{HH}": "%H",
            "{hh}": "%I",
            "{mm}": "%M",
            "{ss}": "%S",
        }

        mapping_lang = {
            "Monday": "星期一",
            "Tuesday": "星期二",
            "Wednesday": "星期三",
            "Thursday": "星期四",
            "Friday": "星期五",
            "Saturday": "星期六",
            "Sunday": "星期日",
            "Mon": "周一",
            "Tue": "周二",
            "Wed": "周三",
            "Thu": "周四",
            "Fri": "周五",
            "Sat": "周六",
            "Sun": "周日",
            "Mo": "一",
            "Tu": "二",
            "We": "三",
            "Th": "四",
            "Fr": "五",
            "Sa": "六",
            "Su": "日",
        }
        dt = dt or datetime.now()
        fmt = self.DailyFormat
        for mjs, pyfmt in mapping.items():
            fmt = fmt.replace(mjs, pyfmt)
            fmt = dt.strftime(fmt)
            if lang == "zh":
                for mjs, pyfmt in mapping_lang.items():
                    fmt = fmt.replace(mjs, pyfmt)

        return fmt

    def on_click_ButtonBlockName(self):
        if self.EntryBlockName.get() == "":
            self.show_info_popup("请先设置块标题", "warning")
            self.EntryBlockName.insert(0, self.BlockName)
            self.focus_set()
            return
        self.BlockName = self.EntryBlockName.get()
        self.saveSetting()

    def on_click_ButtonQuickAdd(self):
        if self.VaultDir == "":
            self.show_info_popup("请先设置日记路径", "warning")
            return
        if self.DailyFormat == "":
            self.show_info_popup("请先设置日记格式", "warning")
            return
        if self.BlockName == "":
            self.show_info_popup("请先设置块标题", "warning")
            return

        self.QuickAddText = self.TextBoxQuickAdd.get("1.0", "end-1c")
        if self.QuickAddText == "":
            self.show_info_popup("请先输入内容", "warning")
            return

        self.insert_text_to_block(self.DailyPath)

    def insert_text_to_block(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        f.close()

        block_start = None
        block_end = None

        # 查找块开始（标题行）的位置
        for i, line in enumerate(lines):
            if line.strip() == self.BlockName.strip():
                block_start = i
                break

        if block_start is None:
            self.show_info_popup("找不到指定块", "error")
            return

        # 查找下一个标题（块的结束）
        heading_pattern = re.compile(r"^#{1,6}\s+.+$")
        block_end = len(lines)
        for j in range(block_start + 1, len(lines)):
            if heading_pattern.match(lines[j].strip()):
                block_end = j
                break

        if self.ifTimeStamp:
            self.QuickAddText = (
                self.QuickAddText + " [" + datetime.now().strftime("%H:%M:%S") + "]"
            )
        # 插入到块末尾
        lines.insert(block_end, "\n" + self.QuickAddText + "\n")

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)
        f.close()
        self.show_info_popup("记录成功", "info")

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)
        self.geometry(f"{width}x{height}+{int(self.scale*x)}+{int(self.scale*y)}")

    def get_dpi_windows(self):
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(0, hdc)
        dpi /= 96  # 缩放比例
        return dpi

    def get_dpi_macos(self):
        # macOS 通常默认缩放比例为 1.0
        return 1.0

    def get_dpi_linux(self):
        root = tk.Tk()
        root.withdraw()
        dpi = root.winfo_fpixels('1i') / 72  # 转换为缩放比例
        root.destroy()
        return dpi

    def get_dpi(self):
        if sys.platform.startswith('win'):
            return self.get_dpi_windows()
        elif sys.platform.startswith('darwin'):
            return self.get_dpi_macos()
        elif sys.platform.startswith('linux'):
            return self.get_dpi_linux()
        else:
            return 1.0  # 默认缩放比例为 1.0


if __name__ == "__main__":
    set_default_color_theme("green")
    root = App()
    root.iconbitmap(resource_path("assets/icon.ico"))
    root.minsize(640, 480)
    root.center_window(640, 480)
    root.title("QuickDaily")
    root.configure(fg_color=['#f5f5f5', '#555759'])
    root.mainloop()
