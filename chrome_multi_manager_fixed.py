"""Chrome Multi Manager - independent Chrome instances with settings sync and batch Load unpacked."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import uuid
import ctypes
import msvcrt
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
import tkinter as tk

APP_NAME = "Chrome Multi Manager"
APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ChromeMultiManager"
CONFIG_FILE = APP_DIR / "config.json"
PROFILES_DIR = APP_DIR / "profiles"

SYNC_OPTIONS = {
    "settings": "浏览器设置",
    "bookmarks": "书签",
}

# These are preserved when copying Preferences from the source instance so
# settings sync does not overwrite the target's extension registration state.
EXTENSION_PREF_KEYS = (
    "extensions",
    "extensions_ui",
    "extension_commands",
)

# Chromium's preference key for the Developer mode switch in chrome://extensions.
DEVELOPER_MODE_PREF_PATH = ("extensions", "ui", "developer_mode")

EXTENSIONS_SETTINGS_PATH = ("extensions", "settings")

ZH_TO_EN = {
    "独立用户数据目录 · 设置同步 · 批量 Load unpacked": "Independent data directories · Settings sync · Batch Load unpacked",
    "语言": "Language",
    "Chrome 实例": "Chrome Instances",
    "每个实例都有独立的 Cookie、登录状态、扩展和缓存。": "Each instance has independent cookies, sessions, extensions, and cache.",
    "新建实例": "New Instance",
    "删除实例": "Delete Instance",
    "实例操作": "Instance Actions",
    "请选择左侧实例": "Select an instance",
    "启动选中": "Launch Selected",
    "启动全部": "Launch All",
    "停止选中": "Stop Selected",
    "此实例参与同步": "Include this instance in sync",
    "可选设置同步": "Optional Settings Sync",
    "同步源": "Sync source",
    "浏览器设置": "Browser settings",
    "书签": "Bookmarks",
    "选择同步内容": "Choose sync items",
    "一键选中所有实例": "Select all instances",
    "取消选中所有实例": "Clear all selected instances",
    "同步所选实例": "Sync selected instances",
    "同步前请关闭同步源和目标实例；所选项目会覆盖目标": "Close source and target instances first; selected items replace target data",
    "扩展目录": "Extension folder",
    "目录下每个包含 manifest.json 的一级子文件夹都会作为一个 unpacked extension。": "Each first-level subfolder containing manifest.json is treated as one unpacked extension.",
    "批量 Load unpacked": "Batch Load unpacked",
    "自动开启 Developer mode；Load unpacked 后在 Chrome 正常关闭时保存扩展注册，之后重新启动实例仍会保留。": "Developer mode is enabled automatically; after Load unpacked, extension registrations are made persistent when Chrome closes normally, so they remain after the instance is restarted.",
    "Chrome 程序路径": "Chrome executable path",
    "选择…": "Browse...",
    "● 运行中": "● Running",
    "○ 已停止": "○ Stopped",
    " · 同步": " · Sync",
    "● 正在运行": "● Running",
    "数据目录：": "Data directory: ",
}
EN_TO_ZH = {english: chinese for chinese, english in ZH_TO_EN.items()}

ZH_TO_JA = {
    "独立用户数据目录 · 设置同步 · 批量 Load unpacked": "独立ユーザーデータディレクトリ · 設定同期 · Load unpacked の一括実行",
    "语言": "言語",
    "Chrome 实例": "Chrome インスタンス",
    "每个实例都有独立的 Cookie、登录状态、扩展和缓存。": "各インスタンスには独立した Cookie、ログイン状態、拡張機能、キャッシュがあります。",
    "新建实例": "新しいインスタンス",
    "删除实例": "インスタンスを削除",
    "实例操作": "インスタンス操作",
    "请选择左侧实例": "左側のインスタンスを選択してください",
    "启动选中": "選択したものを起動",
    "启动全部": "すべて起動",
    "停止选中": "選択したものを停止",
    "此实例参与同步": "このインスタンスを同期対象にする",
    "可选设置同步": "オプション設定の同期",
    "同步源": "同期元",
    "浏览器设置": "ブラウザ設定",
    "书签": "ブックマーク",
    "选择同步内容": "同期する項目を選択",
    "一键选中所有实例": "すべてのインスタンスを選択",
    "取消选中所有实例": "すべての選択を解除",
    "同步所选实例": "選択したインスタンスを同期",
    "同步前请关闭同步源和目标实例；所选项目会覆盖目标": "同期前に同期元と対象のインスタンスを閉じてください。選択した項目で対象データが上書きされます",
    "扩展目录": "拡張機能フォルダー",
    "目录下每个包含 manifest.json 的一级子文件夹都会作为一个 unpacked extension。": "ディレクトリ内で manifest.json を含む各第1階層のサブフォルダーが unpacked extension として扱われます。",
    "批量 Load unpacked": "Load unpacked を一括実行",
    "自动开启 Developer mode；Load unpacked 后在 Chrome 正常关闭时保存扩展注册，之后重新启动实例仍会保留。": "Developer mode を自動的に有効にします。Load unpacked 後、Chrome が正常に終了すると拡張機能の登録が保存され、インスタンスを再起動しても保持されます。",
    "Chrome 程序路径": "Chrome 実行ファイルのパス",
    "选择…": "参照…",
    "● 运行中": "● 実行中",
    "○ 已停止": "○ 停止中",
    " · 同步": " · 同期",
    "● 正在运行": "● 実行中",
    "数据目录：": "データディレクトリ：",
}
JA_TO_ZH = {japanese: chinese for chinese, japanese in ZH_TO_JA.items()}

ZH_TO_DE = {
    "独立用户数据目录 · 设置同步 · 批量 Load unpacked": "Unabhängige Benutzerdatenverzeichnisse · Einstellungssynchronisierung · Load unpacked für mehrere Instanzen",
    "语言": "Sprache",
    "Chrome 实例": "Chrome-Instanzen",
    "每个实例都有独立的 Cookie、登录状态、扩展和缓存。": "Jede Instanz verfügt über eigene Cookies, Anmeldestatus, Erweiterungen und Cache.",
    "新建实例": "Neue Instanz",
    "删除实例": "Instanz löschen",
    "实例操作": "Instanzaktionen",
    "请选择左侧实例": "Wählen Sie eine Instanz auf der linken Seite aus",
    "启动选中": "Ausgewählte starten",
    "启动全部": "Alle starten",
    "停止选中": "Ausgewählte stoppen",
    "此实例参与同步": "Diese Instanz in die Synchronisierung einbeziehen",
    "可选设置同步": "Optionale Einstellungssynchronisierung",
    "同步源": "Synchronisierungsquelle",
    "浏览器设置": "Browsereinstellungen",
    "书签": "Lesezeichen",
    "选择同步内容": "Synchronisierungsinhalte auswählen",
    "一键选中所有实例": "Alle Instanzen auswählen",
    "取消选中所有实例": "Auswahl aller Instanzen aufheben",
    "同步所选实例": "Ausgewählte Instanzen synchronisieren",
    "同步前请关闭同步源和目标实例；所选项目会覆盖目标": "Schließen Sie vor der Synchronisierung die Quell- und Zielinstanzen. Die ausgewählten Elemente überschreiben die Zieldaten",
    "扩展目录": "Erweiterungsordner",
    "目录下每个包含 manifest.json 的一级子文件夹都会作为一个 unpacked extension。": "Jeder Unterordner der ersten Ebene mit manifest.json wird als eine entpackte Erweiterung behandelt.",
    "批量 Load unpacked": "Load unpacked für mehrere Instanzen",
    "自动开启 Developer mode；Load unpacked 后在 Chrome 正常关闭时保存扩展注册，之后重新启动实例仍会保留。": "Der Entwicklermodus wird automatisch aktiviert. Nach Load unpacked werden die Erweiterungsregistrierungen beim normalen Schließen von Chrome gespeichert und bleiben nach dem Neustart der Instanz erhalten.",
    "Chrome 程序路径": "Chrome-Programm-Pfad",
    "选择…": "Durchsuchen…",
    "● 运行中": "● Läuft",
    "○ 已停止": "○ Gestoppt",
    " · 同步": " · Sync",
    "● 正在运行": "● Läuft",
    "数据目录：": "Datenverzeichnis: ",
}
DE_TO_ZH = {german: chinese for chinese, german in ZH_TO_DE.items()}



def default_chrome_path() -> str:
    candidates = [
        Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    return ""


def set_nested_value(data: dict, path: tuple[str, ...], value: object) -> None:
    current = data
    for key in path[:-1]:
        child = current.get(key)
        if not isinstance(child, dict):
            child = {}
            current[key] = child
        current = child
    current[path[-1]] = value


def read_json_file(path: Path, *, tolerate_missing: bool = True) -> dict:
    if not path.exists():
        return {} if tolerate_missing else {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OSError(f"无法读取 JSON 文件：{path}\n{exc}") from exc
    if not isinstance(data, dict):
        raise OSError(f"JSON 文件不是对象：{path}")
    return data


class ChromeMultiManager(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1040x740")
        self.minsize(900, 620)
        self.configure(bg="#f4f6f8")
        APP_DIR.mkdir(parents=True, exist_ok=True)
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        self.config_data = self.load_config()
        self.processes: dict[str, subprocess.Popen] = {}
        self.profile_ids: list[str] = []
        self.cdp_request_id = 0
        self.cdp_streams: dict[str, tuple[object, object]] = {}
        self.sync_option_vars: dict[str, tk.BooleanVar] = {
            key: tk.BooleanVar(value=bool(self.config_data.get("sync_options", {}).get(key, True)))
            for key in SYNC_OPTIONS
        }
        self.build_ui()
        self.refresh_profiles()
        self.after(1200, self.poll_processes)

    def load_config(self) -> dict:
        defaults = {
            "chrome_path": default_chrome_path(),
            "language": "zh-CN",
            "source_profile": "",
            "extensions_folder": "",
            "sync_options": {"settings": True, "bookmarks": True},
            "profiles": [],
        }
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                defaults.update(loaded)
            if not isinstance(defaults.get("profiles"), list):
                defaults["profiles"] = []
        except (OSError, json.JSONDecodeError):
            pass

        # Migration: each instance keeps its own explicit list of extensions
        # that the user has loaded through the batch button.
        for profile in defaults["profiles"]:
            if not isinstance(profile, dict):
                continue
            loaded_extensions = profile.get("loaded_extensions")
            if not isinstance(loaded_extensions, list):
                profile["loaded_extensions"] = []
            else:
                profile["loaded_extensions"] = [
                    str(item) for item in loaded_extensions
                    if isinstance(item, str) and item.strip()
                ]
        return defaults

    def save_config(self) -> None:
        self.config_data["sync_options"] = {
            key: bool(var.get()) for key, var in self.sync_option_vars.items()
        }
        temp_file = CONFIG_FILE.with_suffix(".tmp")
        with temp_file.open("w", encoding="utf-8") as handle:
            json.dump(self.config_data, handle, ensure_ascii=False, indent=2)
        os.replace(temp_file, CONFIG_FILE)

    def t(self, chinese: str, english: str | None = None) -> str:
        language = self.config_data.get("language", "zh-CN")
        if language == "en-US":
            return english if english is not None else ZH_TO_EN.get(chinese, chinese)
        if language == "ja-JP":
            return ZH_TO_JA.get(chinese, chinese)
        if language == "de-DE":
            return ZH_TO_DE.get(chinese, chinese)
        return chinese

    def build_ui(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#17324d")
        style.configure("Subtle.TLabel", foreground="#5d6b78")
        style.configure("Panel.TLabelframe", padding=12)
        style.configure("Panel.TLabelframe.Label", font=("Segoe UI", 10, "bold"))

        header = ttk.Frame(self, padding=(24, 18, 24, 10))
        header.pack(fill="x")
        ttk.Label(header, text=APP_NAME, style="Title.TLabel").pack(side="left")
        ttk.Label(
            header,
            text="独立用户数据目录 · 设置同步 · 批量 Load unpacked",
            style="Subtle.TLabel",
        ).pack(side="left", padx=(14, 0), pady=(5, 0))
        language_frame = ttk.Frame(header)
        language_frame.pack(side="right")
        ttk.Label(language_frame, text="语言").pack(side="left", padx=(0, 6))
        self.language_var = tk.StringVar(
            value={
                "en-US": "English",
                "ja-JP": "日本語",
                "de-DE": "Deutsch",
            }.get(self.config_data.get("language"), "中文")
        )
        self.language_combo = ttk.Combobox(
            language_frame,
            textvariable=self.language_var,
            values=("中文", "English", "日本語", "Deutsch"),
            state="readonly",
            width=10,
        )
        self.language_combo.pack(side="left")
        self.language_combo.bind("<<ComboboxSelected>>", self.change_language)

        main = ttk.Frame(self, padding=(24, 0, 24, 20))
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=2)
        main.columnconfigure(1, weight=3)
        main.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(main, text="Chrome 实例", style="Panel.TLabelframe")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)
        ttk.Label(
            left,
            text="每个实例都有独立的 Cookie、登录状态、扩展和缓存。",
            style="Subtle.TLabel",
            wraplength=330,
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))
        list_frame = ttk.Frame(left)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        self.profile_list = tk.Listbox(
            list_frame,
            activestyle="none",
            exportselection=False,
            font=("Segoe UI", 11),
            borderwidth=0,
            highlightthickness=1,
            highlightcolor="#4d8ac7",
            selectbackground="#dbeafe",
            selectforeground="#17324d",
        )
        self.profile_list.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.profile_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.profile_list.configure(yscrollcommand=scrollbar.set)
        self.profile_list.bind("<<ListboxSelect>>", lambda _event: self.on_profile_selected())
        buttons = ttk.Frame(left)
        buttons.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)
        ttk.Button(buttons, text="新建实例", command=self.add_profile).grid(
            row=0, column=0, sticky="ew", padx=(0, 5)
        )
        ttk.Button(buttons, text="删除实例", command=self.delete_profile).grid(
            row=0, column=1, sticky="ew", padx=(5, 0)
        )

        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)

        instance_panel = ttk.LabelFrame(right, text="实例操作", style="Panel.TLabelframe")
        instance_panel.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        instance_panel.columnconfigure(0, weight=1)
        self.selected_label = ttk.Label(
            instance_panel, text="请选择左侧实例", font=("Segoe UI", 12, "bold")
        )
        self.selected_label.grid(row=0, column=0, sticky="w")
        self.instance_status = ttk.Label(instance_panel, text="", style="Subtle.TLabel")
        self.instance_status.grid(row=1, column=0, sticky="w", pady=(3, 12))
        action_row = ttk.Frame(instance_panel)
        action_row.grid(row=2, column=0, sticky="ew")
        ttk.Button(action_row, text="启动选中", command=self.launch_selected).pack(side="left")
        ttk.Button(action_row, text="启动全部", command=self.launch_all).pack(side="left", padx=8)
        ttk.Button(action_row, text="停止选中", command=self.stop_selected).pack(side="left")
        self.sync_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            instance_panel,
            text="此实例参与同步",
            variable=self.sync_enabled_var,
            command=self.update_selected_sync,
        ).grid(row=3, column=0, sticky="w", pady=(12, 0))

        sync_panel = ttk.LabelFrame(right, text="可选设置同步", style="Panel.TLabelframe")
        sync_panel.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        sync_panel.columnconfigure(1, weight=1)
        ttk.Label(sync_panel, text="同步源").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(sync_panel, textvariable=self.source_var, state="readonly")
        self.source_combo.grid(row=0, column=1, sticky="ew")
        self.source_combo.bind("<<ComboboxSelected>>", self.update_source)
        target_buttons = ttk.Frame(sync_panel)
        target_buttons.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 4))
        ttk.Button(
            target_buttons,
            text="一键选中所有实例",
            command=self.select_all_targets,
        ).pack(side="left")
        ttk.Button(
            target_buttons,
            text="取消选中所有实例",
            command=self.clear_all_targets,
        ).pack(side="left", padx=(8, 0))
        ttk.Label(sync_panel, text="选择同步内容", style="Subtle.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(4, 4)
        )
        files_frame = ttk.Frame(sync_panel)
        files_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        for index, key in enumerate(SYNC_OPTIONS):
            ttk.Checkbutton(
                files_frame,
                text=SYNC_OPTIONS[key],
                variable=self.sync_option_vars[key],
                command=self.save_config,
            ).grid(row=0, column=index, sticky="w", padx=(0, 22))
        sync_actions = ttk.Frame(sync_panel)
        sync_actions.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(sync_actions, text="同步所选实例", command=self.sync_now).pack(side="left")
        ttk.Label(
            sync_actions,
            text="同步前请关闭同步源和目标实例；所选项目会覆盖目标",
            style="Subtle.TLabel",
        ).pack(side="left", padx=12)

        extension_panel = ttk.LabelFrame(right, text="扩展目录", style="Panel.TLabelframe")
        extension_panel.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        extension_panel.columnconfigure(0, weight=1)
        self.extensions_folder_var = tk.StringVar(
            value=self.config_data.get("extensions_folder", "")
        )
        ttk.Entry(extension_panel, textvariable=self.extensions_folder_var).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Button(extension_panel, text="选择…", command=self.choose_extensions_folder).grid(
            row=0, column=1, sticky="ew"
        )
        ttk.Button(
            extension_panel,
            text="批量 Load unpacked",
            command=self.batch_load_extensions,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 4))
        ttk.Label(
            extension_panel,
            text="目录下每个包含 manifest.json 的一级子文件夹都会作为一个 unpacked extension。",
            style="Subtle.TLabel",
            wraplength=580,
        ).grid(row=2, column=0, columnspan=2, sticky="w")
        ttk.Label(
            extension_panel,
            text="自动开启 Developer mode；点击 Load unpacked 后由 Chrome 保存扩展，之后重新启动实例仍会保留。",
            style="Subtle.TLabel",
            wraplength=580,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))

        path_panel = ttk.LabelFrame(right, text="Chrome 程序路径", style="Panel.TLabelframe")
        path_panel.grid(row=3, column=0, sticky="ew")
        path_panel.columnconfigure(0, weight=1)
        self.chrome_path_var = tk.StringVar(value=self.config_data.get("chrome_path", ""))
        ttk.Entry(path_panel, textvariable=self.chrome_path_var).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Button(path_panel, text="选择…", command=self.choose_chrome).grid(row=0, column=1)
        self.status_var = tk.StringVar(value=f"数据目录：{PROFILES_DIR}")
        ttk.Label(
            right,
            textvariable=self.status_var,
            style="Subtle.TLabel",
            wraplength=580,
        ).grid(row=4, column=0, sticky="w", pady=(14, 0))
        self.apply_language()

    def apply_language(self) -> None:
        def translate_widgets(widget: tk.Misc) -> None:
            try:
                current = widget.cget("text")
                if isinstance(current, str):
                    language = self.config_data.get("language", "zh-CN")
                    if language == "en-US":
                        translated = ZH_TO_EN.get(current, current)
                    elif language == "ja-JP":
                        translated = ZH_TO_JA.get(current, current)
                    elif language == "de-DE":
                        translated = ZH_TO_DE.get(current, current)
                    else:
                        translated = (
                            EN_TO_ZH.get(current, JA_TO_ZH.get(current, DE_TO_ZH.get(current, current)))
                        )
                    if translated != current:
                        widget.configure(text=translated)
            except (tk.TclError, TypeError):
                pass
            for child in widget.winfo_children():
                translate_widgets(child)

        translate_widgets(self)
        self.language_var.set({
            "en-US": "English",
            "ja-JP": "日本語",
            "de-DE": "Deutsch",
        }.get(self.config_data.get("language"), "中文"))
        self.status_var.set(self.t("数据目录：", "Data directory: ") + str(PROFILES_DIR))
        self.refresh_profiles(self.selected_id())

    def change_language(self, _event=None) -> None:
        self.config_data["language"] = {
            "中文": "zh-CN",
            "English": "en-US",
            "日本語": "ja-JP",
            "Deutsch": "de-DE",
        }.get(self.language_var.get(), "zh-CN")
        self.save_config()
        self.apply_language()

    def profile_by_id(self, profile_id: str) -> dict | None:
        return next(
            (item for item in self.config_data["profiles"] if item["id"] == profile_id),
            None,
        )

    def refresh_profiles(self, select_id: str | None = None) -> None:
        self.profile_ids = [item["id"] for item in self.config_data["profiles"]]
        self.profile_list.delete(0, tk.END)
        for item in self.config_data["profiles"]:
            marker = (
                self.t("● 运行中", "● Running")
                if item["id"] in self.processes and self.processes[item["id"]].poll() is None
                else self.t("○ 已停止", "○ Stopped")
            )
            sync_marker = self.t(" · 同步", " · Sync") if item.get("sync_enabled", False) else ""
            self.profile_list.insert(tk.END, f"{item['name']}   [{marker}{sync_marker}]")
        self.source_combo["values"] = [item["name"] for item in self.config_data["profiles"]]
        source = self.profile_by_id(self.config_data.get("source_profile", ""))
        self.source_var.set(
            source["name"]
            if source
            else (
                self.source_combo["values"][0]
                if self.source_combo["values"]
                else ""
            )
        )
        if source is None and self.config_data["profiles"]:
            self.config_data["source_profile"] = self.config_data["profiles"][0]["id"]
            self.save_config()
        if select_id in self.profile_ids:
            index = self.profile_ids.index(select_id)
            self.profile_list.selection_set(index)
            self.profile_list.see(index)
        elif self.profile_ids and not self.profile_list.curselection():
            self.profile_list.selection_set(0)
        self.on_profile_selected()

    def selected_id(self) -> str | None:
        selection = self.profile_list.curselection()
        return (
            self.profile_ids[selection[0]]
            if selection and selection[0] < len(self.profile_ids)
            else None
        )

    def on_profile_selected(self) -> None:
        profile = self.profile_by_id(self.selected_id() or "")
        if not profile:
            self.selected_label.configure(text=self.t("请选择左侧实例", "Select an instance"))
            self.instance_status.configure(text="")
            self.sync_enabled_var.set(False)
            return
        running = profile["id"] in self.processes and self.processes[profile["id"]].poll() is None
        self.selected_label.configure(text=profile["name"])
        marker = self.t("● 正在运行", "● Running") if running else self.t("○ 已停止", "○ Stopped")
        self.instance_status.configure(
            text=marker
            + f"   {self.t('数据目录：', 'Data directory: ')}{self.profile_dir(profile)}"
        )
        self.sync_enabled_var.set(bool(profile.get("sync_enabled", False)))

    def profile_dir(self, profile: dict) -> Path:
        return PROFILES_DIR / profile["id"]

    def add_profile(self) -> None:
        name = simpledialog.askstring(
            self.t("新建实例", "New Instance"),
            self.t("实例名称：", "Instance name:"),
            parent=self,
        )
        if not name:
            return
        name = name.strip()
        if not name:
            return
        if any(
            item["name"].casefold() == name.casefold()
            for item in self.config_data["profiles"]
        ):
            messagebox.showwarning(
                self.t("名称重复", "Duplicate name"),
                self.t("已经存在同名实例。", "An instance with this name already exists."),
                parent=self,
            )
            return
        profile = {"id": uuid.uuid4().hex[:12], "name": name, "sync_enabled": False, "loaded_extensions": []}
        self.config_data["profiles"].append(profile)
        if not self.config_data.get("source_profile"):
            self.config_data["source_profile"] = profile["id"]
        self.profile_dir(profile).mkdir(parents=True, exist_ok=True)
        self.save_config()
        self.refresh_profiles(profile["id"])

    def delete_profile(self) -> None:
        profile_id = self.selected_id()
        profile = self.profile_by_id(profile_id or "")
        if not profile:
            return
        if profile_id in self.processes and self.processes[profile_id].poll() is None:
            messagebox.showwarning(
                self.t("无法删除", "Cannot delete"),
                self.t("请先停止正在运行的实例。", "Stop the running instance first."),
                parent=self,
            )
            return
        if not messagebox.askyesno(
            self.t("确认删除", "Confirm deletion"),
            self.t(
                f"删除实例“{profile['name']}”及其全部数据？",
                f"Delete instance '{profile['name']}' and all its data?",
            ),
            parent=self,
        ):
            return
        self.config_data["profiles"] = [
            item for item in self.config_data["profiles"] if item["id"] != profile_id
        ]
        if self.config_data.get("source_profile") == profile_id:
            self.config_data["source_profile"] = (
                self.config_data["profiles"][0]["id"] if self.config_data["profiles"] else ""
            )
        shutil.rmtree(self.profile_dir(profile), ignore_errors=True)
        self.save_config()
        self.refresh_profiles()

    def choose_chrome(self) -> None:
        path = filedialog.askopenfilename(
            title=self.t("选择 chrome.exe", "Select chrome.exe"),
            filetypes=[
                ("Chrome", "chrome.exe"),
                (self.t("所有文件", "All files"), "*.*"),
            ],
        )
        if path:
            self.chrome_path_var.set(path)
            self.config_data["chrome_path"] = path
            self.save_config()

    def choose_extensions_folder(self) -> None:
        current = self.extensions_folder_var.get().strip()
        initialdir = current if Path(current).is_dir() else None
        path = filedialog.askdirectory(
            title=self.t("选择扩展目录", "Select extension folder"),
            initialdir=initialdir,
            mustexist=True,
        )
        if path:
            self.extensions_folder_var.set(path)
            self.config_data["extensions_folder"] = path
            self.save_config()
            try:
                count = len(self.find_unpacked_extensions())
                self.status_var.set(
                    self.t(
                        f"已设置扩展目录，发现 {count} 个 unpacked extension。",
                        f"Extension folder set; found {count} unpacked extension(s).",
                    )
                )
            except OSError as exc:
                messagebox.showerror(
                    self.t("扩展目录错误", "Extension folder error"), str(exc), parent=self
                )

    def update_selected_sync(self) -> None:
        profile = self.profile_by_id(self.selected_id() or "")
        if profile:
            profile["sync_enabled"] = bool(self.sync_enabled_var.get())
            self.save_config()
            self.refresh_profiles(profile["id"])

    def update_source(self, _event=None) -> None:
        selected_name = self.source_var.get()
        profile = next(
            (item for item in self.config_data["profiles"] if item["name"] == selected_name),
            None,
        )
        self.config_data["source_profile"] = profile["id"] if profile else ""
        if profile:
            profile["sync_enabled"] = False
        self.save_config()
        self.refresh_profiles(self.selected_id())

    def select_all_targets(self) -> None:
        source_id = self.config_data.get("source_profile", "")
        for profile in self.config_data["profiles"]:
            profile["sync_enabled"] = profile["id"] != source_id
        self.save_config()
        self.refresh_profiles(self.selected_id())
        count = sum(
            1 for profile in self.config_data["profiles"] if profile.get("sync_enabled", False)
        )
        self.status_var.set(
            self.t(
                f"已选中 {count} 个目标实例。",
                f"Selected {count} target instance(s).",
            )
        )

    def clear_all_targets(self) -> None:
        source_id = self.config_data.get("source_profile", "")
        changed = 0
        for profile in self.config_data.get("profiles", []):
            if profile.get("id") != source_id and profile.get("sync_enabled") is True:
                profile["sync_enabled"] = False
                changed += 1
        self.save_config()
        self.refresh_profiles(self.selected_id())
        self.status_var.set(
            self.t(
                f"已取消选中 {changed} 个目标实例。",
                f"Cleared {changed} selected target instance(s).",
            )
        )

    def selected_sync_categories(self) -> list[str]:
        return [key for key, var in self.sync_option_vars.items() if var.get()]

    def get_extension_target_profiles(self) -> list[dict]:
        """Return exactly the instances allowed to receive batch unpacked extensions.

        Only an explicit JSON boolean True in sync_enabled qualifies. The sync
        source is always excluded, even if stale configuration data says True.
        """
        source_id = self.config_data.get("source_profile", "")
        return [
            profile
            for profile in self.config_data.get("profiles", [])
            if profile.get("id") != source_id
            and type(profile.get("sync_enabled")) is bool
            and profile.get("sync_enabled") is True
        ]

    def chrome_profile_dir(self, profile: dict, create: bool = False) -> Path:
        path = self.profile_dir(profile) / "Default"
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def copy_file_atomic(self, source: Path, target: Path) -> int:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".sync_tmp")
        shutil.copy2(source, temporary)
        os.replace(temporary, target)
        return 1

    def write_json_atomic(self, target: Path, data: dict) -> int:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".sync_tmp")
        temporary.write_text(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(temporary, target)
        return 1

    def set_developer_mode(self, profile: dict) -> None:
        """Persist chrome://extensions Developer mode for this profile."""
        profile_dir = self.chrome_profile_dir(profile, create=True)
        preferences = profile_dir / "Preferences"
        data = read_json_file(preferences)
        set_nested_value(data, DEVELOPER_MODE_PREF_PATH, True)
        self.write_json_atomic(preferences, data)

    def copy_browser_settings(self, source: Path, target: Path) -> int:
        """Copy Preferences while preserving extension registration from target."""
        source_data = read_json_file(source)
        target_data = read_json_file(target)
        for key in EXTENSION_PREF_KEYS:
            if key in target_data:
                source_data[key] = target_data[key]
            else:
                source_data.pop(key, None)
        return self.write_json_atomic(target, source_data)

    def is_profile_running(self, profile: dict) -> bool:
        process = self.processes.get(profile["id"])
        if process and process.poll() is None:
            return True
        environment = os.environ.copy()
        environment["CMM_PROFILE_DIR"] = str(self.profile_dir(profile))
        script = (
            "$path=[Environment]::GetEnvironmentVariable('CMM_PROFILE_DIR');"
            "$found=Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" -ErrorAction Stop | "
            "Where-Object { $_.CommandLine -and $_.CommandLine.Contains($path) } | Select-Object -First 1;"
            "if($found){'1'}else{'0'}"
        )
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                timeout=8,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                env=environment,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise OSError(f"无法检查 Chrome 进程：{exc}") from exc
        if result.returncode:
            raise OSError(f"无法检查 Chrome 进程：{result.stderr.strip()}")
        return result.stdout.strip() == "1"

    def sync_profile(self, source: dict, target: dict, categories: list[str]) -> tuple[int, list[str]]:
        copied = 0
        missing: list[str] = []
        source_dir = self.chrome_profile_dir(source)
        if not source_dir.is_dir():
            raise OSError(f"同步源尚未初始化：{source_dir}")
        target_dir = self.chrome_profile_dir(target, create=True)

        if "settings" in categories:
            source_file = source_dir / "Preferences"
            if source_file.exists():
                copied += self.copy_browser_settings(source_file, target_dir / "Preferences")
            else:
                missing.append("settings")

        if "bookmarks" in categories:
            source_file = source_dir / "Bookmarks"
            if source_file.exists():
                copied += self.copy_file_atomic(source_file, target_dir / "Bookmarks")
            else:
                missing.append("bookmarks")

        return copied, missing

    def sync_now(self) -> None:
        categories = self.selected_sync_categories()
        if not categories:
            messagebox.showinfo(
                self.t("未选择同步内容", "No sync items selected"),
                self.t("请至少选择浏览器设置或书签中的一项。", "Select at least one sync item."),
                parent=self,
            )
            return
        source = self.profile_by_id(self.config_data.get("source_profile", ""))
        if not source:
            messagebox.showinfo(
                self.t("没有同步源", "No sync source"),
                self.t("请先创建实例并选择同步源。", "Create an instance and select a sync source first."),
                parent=self,
            )
            return
        targets = [
            item
            for item in self.config_data["profiles"]
            if item["id"] != source["id"] and item.get("sync_enabled", False)
        ]
        if not targets:
            messagebox.showinfo(
                self.t("没有目标实例", "No target instances"),
                self.t(
                    "请勾选“此实例参与同步”，或点击“一键选中所有实例”。",
                    "Include at least one instance in sync or click Select all instances.",
                ),
                parent=self,
            )
            return
        try:
            running = [
                item["name"]
                for item in [source] + targets
                if self.is_profile_running(item)
            ]
            if running:
                messagebox.showwarning(
                    self.t("实例正在运行", "Instances are running"),
                    self.t(
                        "请先关闭这些 Chrome 实例再同步：",
                        "Close these Chrome instances before syncing: ",
                    )
                    + ", ".join(running),
                    parent=self,
                )
                return
            total = 0
            missing_count = 0
            for target in targets:
                copied, missing = self.sync_profile(source, target, categories)
                total += copied
                missing_count += len(missing)
        except OSError as exc:
            messagebox.showerror(self.t("同步失败", "Sync failed"), str(exc), parent=self)
            return
        if total == 0:
            messagebox.showwarning(
                self.t("没有找到可同步文件", "No sync files found"),
                self.t(
                    "请先启动同步源实例，完成设置后关闭 Chrome 再同步。",
                    "Launch the sync source once, configure it, close Chrome, and sync again.",
                ),
                parent=self,
            )
            return
        suffix = (
            self.t(
                f"缺少 {missing_count} 项源数据。",
                f"{missing_count} source item(s) were missing.",
            )
            if missing_count
            else ""
        )
        self.status_var.set(
            self.t(
                f"已同步到 {len(targets)} 个所选实例，共复制 {total} 个文件。{suffix}",
                f"Synced {total} file(s) to {len(targets)} selected instance(s). {suffix}",
            )
        )

    # ---------- Unpacked extension management ----------

    def get_saved_extension_paths(self, profile: dict) -> list[Path]:
        """Return unpacked extension paths previously loaded into this instance.

        Current Chrome treats Extensions.loadUnpacked as a CDP/debug installation
        and may remove that registration on the next browser startup. Therefore
        persistence is owned by the manager: after an extension has been
        successfully loaded for an instance, its absolute path is remembered and
        restored through Extensions.loadUnpacked when that instance starts again.
        """
        saved = profile.get("loaded_extensions")
        if not isinstance(saved, list):
            return []

        paths: list[Path] = []
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in saved:
            if not isinstance(item, str) or not item.strip():
                continue
            try:
                path = Path(item).expanduser().resolve()
            except OSError:
                continue
            key = os.path.normcase(str(path))
            if key in seen:
                continue
            seen.add(key)
            if path.is_dir() and (path / "manifest.json").is_file():
                paths.append(path)
                cleaned.append(str(path))

        if cleaned != saved:
            profile["loaded_extensions"] = cleaned
            self.save_config()
        return paths

    def remember_loaded_extension_paths(
        self, profile: dict, extension_paths: list[Path]
    ) -> None:
        """Persist successfully selected extension paths for this instance."""
        existing = self.get_saved_extension_paths(profile)
        merged: list[str] = [str(path.resolve()) for path in existing]
        seen = {os.path.normcase(item) for item in merged}
        changed = False

        for extension_path in extension_paths:
            resolved = extension_path.resolve()
            if not resolved.is_dir() or not (resolved / "manifest.json").is_file():
                continue
            value = str(resolved)
            key = os.path.normcase(value)
            if key not in seen:
                seen.add(key)
                merged.append(value)
                changed = True

        if changed or profile.get("loaded_extensions") != merged:
            profile["loaded_extensions"] = merged
            self.save_config()

    def restore_saved_extensions(self, profile: dict) -> int:
        """Restore this instance's previously loaded unpacked extensions."""
        paths = self.get_saved_extension_paths(profile)
        if not paths:
            return 0

        process = self.processes.get(profile["id"])
        if not process or process.poll() is not None:
            return 0

        existing_paths: set[str] = set()
        result = self.send_cdp_command(
            process, profile["id"], "Extensions.getExtensions"
        )
        for item in result.get("extensions", []):
            if not isinstance(item, dict):
                continue
            path_value = item.get("path")
            if isinstance(path_value, str) and path_value.strip():
                try:
                    existing_paths.add(
                        os.path.normcase(str(Path(path_value).resolve()))
                    )
                except OSError:
                    pass

        missing = [
            path
            for path in paths
            if os.path.normcase(str(path.resolve())) not in existing_paths
        ]
        if not missing:
            return 0

        self.load_unpacked_with_retry(profile, missing)
        return len(missing)

    def extension_root(self) -> Path:
        root_text = self.extensions_folder_var.get().strip()
        if not root_text:
            raise OSError("请先设置扩展目录。")
        root = Path(root_text).expanduser()
        if not root.is_dir():
            raise OSError(f"扩展目录不存在：{root}")
        self.config_data["extensions_folder"] = str(root)
        self.save_config()
        return root

    def find_unpacked_extensions(self) -> list[Path]:
        root = self.extension_root()
        candidates: list[Path] = []

        # Also accept the selected folder itself as an extension package.
        if (root / "manifest.json").is_file():
            candidates.append(root)

        # Normal layout: one extension per first-level folder.
        for child in sorted(root.iterdir(), key=lambda p: p.name.casefold()):
            if child.is_dir() and (child / "manifest.json").is_file():
                if child.resolve() not in {item.resolve() for item in candidates}:
                    candidates.append(child)

        if not candidates:
            raise OSError(
                f"在目录中没有找到 unpacked extension：{root}\n"
                "请确保扩展目录本身或其一级子目录包含 manifest.json。"
            )
        return candidates

    def _next_cdp_id(self) -> int:
        self.cdp_request_id += 1
        return self.cdp_request_id

    @staticmethod
    def _create_windows_cdp_pipes() -> tuple[int, int, object, object]:
        """Create Chrome's Windows DevTools input/output pipes.

        Chrome expects two inherited Windows HANDLE values through
        --remote-debugging-io-pipes=read_handle,write_handle. The parent keeps
        the opposite ends for reading Chrome's responses and writing commands.
        """
        if os.name != "nt":
            raise OSError("Windows DevTools pipe 仅支持 Windows。")

        class SECURITY_ATTRIBUTES(ctypes.Structure):
            _fields_ = [
                ("nLength", ctypes.c_ulong),
                ("lpSecurityDescriptor", ctypes.c_void_p),
                ("bInheritHandle", ctypes.c_int),
            ]

        kernel32 = ctypes.windll.kernel32
        kernel32.CreatePipe.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.POINTER(SECURITY_ATTRIBUTES),
            ctypes.c_ulong,
        ]
        kernel32.CreatePipe.restype = ctypes.c_int
        kernel32.SetHandleInformation.argtypes = [
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.c_ulong,
        ]
        kernel32.SetHandleInformation.restype = ctypes.c_int
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_int

        HANDLE_FLAG_INHERIT = 0x00000001
        sa = SECURITY_ATTRIBUTES(
            ctypes.sizeof(SECURITY_ATTRIBUTES), None, 1
        )

        # child_read <- Chrome writes here; parent_write writes into it.
        child_read = ctypes.c_void_p()
        parent_write = ctypes.c_void_p()
        # parent_read reads Chrome output; child_write <- Chrome reads here.
        parent_read = ctypes.c_void_p()
        child_write = ctypes.c_void_p()

        if not kernel32.CreatePipe(
            ctypes.byref(child_read), ctypes.byref(parent_write), ctypes.byref(sa), 0
        ):
            raise OSError(f"CreatePipe failed: {ctypes.get_last_error()}")
        if not kernel32.CreatePipe(
            ctypes.byref(parent_read), ctypes.byref(child_write), ctypes.byref(sa), 0
        ):
            kernel32.CloseHandle(child_read)
            kernel32.CloseHandle(parent_write)
            raise OSError(f"CreatePipe failed: {ctypes.get_last_error()}")

        # Parent ends must not be inherited. Child ends remain inheritable.
        if not kernel32.SetHandleInformation(
            parent_write, HANDLE_FLAG_INHERIT, 0
        ) or not kernel32.SetHandleInformation(
            parent_read, HANDLE_FLAG_INHERIT, 0
        ):
            for handle in (child_read, parent_write, parent_read, child_write):
                kernel32.CloseHandle(handle)
            raise OSError(f"SetHandleInformation failed: {ctypes.get_last_error()}")

        child_read_value = int(child_read.value)
        child_write_value = int(child_write.value)
        parent_read_value = int(parent_read.value)
        parent_write_value = int(parent_write.value)

        # open_osfhandle transfers ownership of the HANDLE to the CRT fd.
        read_fd = msvcrt.open_osfhandle(parent_read_value, os.O_BINARY | os.O_RDONLY)
        try:
            write_fd = msvcrt.open_osfhandle(parent_write_value, os.O_BINARY | os.O_WRONLY)
        except Exception:
            os.close(read_fd)
            raise

        read_stream = os.fdopen(read_fd, "rb", buffering=0)
        write_stream = os.fdopen(write_fd, "wb", buffering=0)
        return child_read_value, child_write_value, read_stream, write_stream

    @staticmethod
    def _close_child_handle(handle: int) -> None:
        ctypes.windll.kernel32.CloseHandle(ctypes.c_void_p(handle))

    @staticmethod
    def _read_cdp_message(stream) -> bytes:
        # DevTools' Windows pipe uses ASCIIZ framing: one JSON message followed
        # by a NUL byte. Do not interpret it as a 4-byte length-prefixed frame.
        chunks: list[bytes] = []
        while True:
            chunk = stream.read(1)
            if not chunk:
                raise OSError("Chrome DevTools pipe 已关闭。")
            if chunk == b"\x00":
                return b"".join(chunks)
            chunks.append(chunk)

    def send_cdp_command(
        self, process: subprocess.Popen, profile_id: str, method: str, params: dict | None = None
    ) -> dict:
        if process.poll() is not None:
            raise OSError("Chrome 进程已经退出。")

        streams = self.cdp_streams.get(profile_id)
        if not streams:
            raise OSError("当前 Chrome 实例没有可用的 DevTools pipe。请使用本程序重新启动实例。")
        read_stream, write_stream = streams

        request_id = self._next_cdp_id()
        message = {"id": request_id, "method": method}
        if params:
            message["params"] = params
        payload = json.dumps(message, separators=(",", ":")).encode("utf-8") + b"\x00"
        try:
            write_stream.write(payload)
            write_stream.flush()
            while True:
                body = self._read_cdp_message(read_stream)
                if not body:
                    continue
                response = json.loads(body.decode("utf-8"))
                if response.get("id") != request_id:
                    continue
                if "error" in response:
                    error = response["error"]
                    raise OSError(f"{method} 失败：{error.get('message', error)}")
                return response.get("result", {})
        except (BrokenPipeError, OSError) as exc:
            if process.poll() is not None:
                raise OSError("Chrome 已退出，DevTools pipe 已关闭。") from exc
            raise

    def load_unpacked_into_process(
        self,
        process: subprocess.Popen,
        profile_id: str,
        extension_paths: list[Path],
    ) -> list[str]:
        loaded: list[str] = []
        for extension_path in extension_paths:
            result = self.send_cdp_command(
                process,
                profile_id,
                "Extensions.loadUnpacked",
                {"path": str(extension_path.resolve())},
            )
            extension_id = result.get("extensionId") or result.get("id")
            loaded.append(extension_id or extension_path.name)
        return loaded

    def load_unpacked_with_retry(
        self,
        profile: dict,
        extension_paths: list[Path],
        attempts: int = 12,
    ) -> list[str]:
        process = self.processes.get(profile["id"])
        if not process or process.poll() is not None:
            raise OSError(f"实例“{profile['name']}”当前没有由本程序运行。")

        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return self.load_unpacked_into_process(process, profile["id"], extension_paths)
            except OSError as exc:
                last_error = exc
                if process.poll() is not None:
                    break
                if attempt + 1 < attempts:
                    time.sleep(0.75)
        raise OSError(
            f"实例“{profile['name']}”加载 unpacked extension 失败：{last_error}"
        )

    def batch_load_extensions(self) -> None:
        """Run the real Chrome ``Load unpacked`` operation for selected instances.

        We deliberately do not use --load-extension here. Recent Google Chrome
        builds disable that command-line switch on branded Chrome builds. The
        supported automation path is the DevTools Extensions.loadUnpacked command
        over the trusted DevTools pipe. Keep that Chrome process running after the
        load so Chrome does not discard the CDP-loaded extensions during a restart.
        """
        try:
            extension_paths = self.find_unpacked_extensions()
        except OSError as exc:
            messagebox.showerror(
                self.t("扩展目录错误", "Extension folder error"), str(exc), parent=self
            )
            return

        profiles = self.get_extension_target_profiles()
        if not profiles:
            messagebox.showinfo(
                self.t("没有选中的实例", "No selected instances"),
                self.t(
                    "请先勾选至少一个“此实例参与同步”的实例。同步源不会参与批量 Load unpacked。",
                    "First enable “Include this instance in sync” for at least one instance. The sync source is excluded from batch Load unpacked.",
                ),
                parent=self,
            )
            return

        chrome_path = Path(self.chrome_path_var.get().strip())
        if not chrome_path.is_file():
            messagebox.showerror(
                self.t("找不到 Chrome", "Chrome not found"),
                self.t(
                    "请在右侧选择有效的 chrome.exe 路径。",
                    "Select a valid chrome.exe path on the right.",
                ),
                parent=self,
            )
            return

        failures: list[str] = []
        loaded_total = 0
        started: list[str] = []

        for profile in profiles:
            try:
                external = self.is_profile_running(profile) and profile["id"] not in self.processes
                if external:
                    raise OSError(
                        "该实例已由本程序之外启动。请先关闭它，再使用本程序启动后重试。"
                    )

                self.set_developer_mode(profile)
                running = (
                    profile["id"] in self.processes
                    and self.processes[profile["id"]].poll() is None
                )

                if running:
                    if profile["id"] not in self.cdp_streams:
                        raise OSError(
                            "该实例正在以普通模式运行。请先关闭它，再点击批量 Load unpacked。"
                        )
                else:
                    # Start with only DevTools pipe enabled; the unpacked extensions
                    # are installed by the actual Extensions.loadUnpacked command.
                    if not self.launch_profile(
                        profile,
                        report_errors=False,
                        enable_devtools=True,
                        restore_extensions=False,
                    ):
                        raise OSError(f"实例“{profile['name']}”启动失败。")
                    started.append(profile["name"])

                ids = self.load_unpacked_with_retry(profile, extension_paths)
                self.remember_loaded_extension_paths(profile, extension_paths)
                loaded_total += len(ids)
            except OSError as exc:
                failures.append(f"{profile['name']}: {exc}")

        if failures:
            messagebox.showerror(
                self.t("批量加载部分失败", "Batch load partially failed"),
                "\n".join(failures),
                parent=self,
            )
            self.status_var.set(
                self.t(
                    f"已尝试在 {len(profiles)} 个选中实例中加载 {len(extension_paths)} 个扩展；成功处理 {loaded_total} 个。",
                    f"Tried to load {len(extension_paths)} extension(s) into {len(profiles)} selected instance(s); {loaded_total} processed successfully.",
                )
            )
            return

        suffix = (
            self.t(
                f"，启动了 {len(started)} 个实例并保持运行",
                f", started {len(started)} instance(s) and left them running",
            )
            if started
            else ""
        )
        self.status_var.set(
            self.t(
                f"已在 {len(profiles)} 个选中实例中 Load unpacked {len(extension_paths)} 个扩展，共成功 {loaded_total} 个{suffix}。",
                f"Loaded {len(extension_paths)} unpacked extension(s) into {len(profiles)} selected instance(s); {loaded_total} succeeded{suffix}.",
            )
        )

    # ---------- Chrome lifecycle ----------

    def launch_selected(self) -> None:
        profile = self.profile_by_id(self.selected_id() or "")
        if profile:
            self.launch_profile(profile)

    def launch_all(self) -> None:
        for profile in self.config_data["profiles"]:
            self.launch_profile(profile)

    def launch_profile(
        self,
        profile: dict,
        *,
        report_errors: bool = True,
        enable_devtools: bool = True,
        restore_extensions: bool = True,
    ) -> bool:
        existing = self.processes.get(profile["id"])
        if existing and existing.poll() is None:
            self.status_var.set(
                self.t(
                    f"实例“{profile['name']}”已经在运行。",
                    f"Instance '{profile['name']}' is already running.",
                )
            )
            return True

        chrome_path = Path(self.chrome_path_var.get().strip())
        if not chrome_path.is_file():
            if report_errors:
                messagebox.showerror(
                    self.t("找不到 Chrome", "Chrome not found"),
                    self.t(
                        "请在右侧选择有效的 chrome.exe 路径。",
                        "Select a valid chrome.exe path on the right.",
                    ),
                    parent=self,
                )
            return False

        user_data_dir = self.profile_dir(profile)
        user_data_dir.mkdir(parents=True, exist_ok=True)
        try:
            command = [
                str(chrome_path),
                f"--user-data-dir={user_data_dir.resolve()}",
            ]

            if enable_devtools:
                self.set_developer_mode(profile)
                child_read, child_write, read_stream, write_stream = (
                    self._create_windows_cdp_pipes()
                )
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.lpAttributeList = {
                    "handle_list": [child_read, child_write]
                }
                # These switches exist only for the temporary Load unpacked session.
                command.extend(
                    [
                        "--remote-debugging-pipe",
                        "--enable-unsafe-extension-debugging",
                        f"--remote-debugging-io-pipes={child_read},{child_write}",
                    ]
                )
                try:
                    process = subprocess.Popen(
                        command,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        startupinfo=startupinfo,
                        close_fds=True,
                        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
                    )
                except Exception:
                    read_stream.close()
                    write_stream.close()
                    raise
                finally:
                    # Chrome inherited these handles; close the parent's copies.
                    self._close_child_handle(child_read)
                    self._close_child_handle(child_write)
            else:
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                    creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
                )
        except (OSError, ValueError) as exc:
            for stream in (locals().get("read_stream"), locals().get("write_stream")):
                if stream is not None:
                    try:
                        stream.close()
                    except OSError:
                        pass
            if report_errors:
                messagebox.showerror(
                    self.t("启动失败", "Launch failed"), str(exc), parent=self
                )
            return False

        self.processes[profile["id"]] = process
        if enable_devtools:
            self.cdp_streams[profile["id"]] = (read_stream, write_stream)

        if enable_devtools and restore_extensions:
            try:
                restored = self.restore_saved_extensions(profile)
                if restored:
                    self.status_var.set(
                        self.t(
                            f"已为“{profile['name']}”恢复 {restored} 个 unpacked extension。",
                            f"Restored {restored} unpacked extension(s) for '{profile['name']}'.",
                        )
                    )
            except OSError as exc:
                # The browser itself remains usable; a later explicit batch load
                # can retry the saved extensions.
                if report_errors:
                    messagebox.showwarning(
                        self.t("扩展恢复失败", "Extension restore failed"),
                        str(exc),
                        parent=self,
                    )

        self.status_var.set(
            self.t(
                f"已启动“{profile['name']}”。",
                f"Launched '{profile['name']}'.",
            )
        )
        self.refresh_profiles(profile["id"])
        return True

    def close_profile_process(self, profile_id: str) -> None:
        process = self.processes.get(profile_id)
        if not process:
            return

        if process.poll() is None:
            if profile_id in self.cdp_streams:
                try:
                    self.send_cdp_command(process, profile_id, "Browser.close")
                except OSError:
                    pass
            else:
                process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        pass

        self.processes.pop(profile_id, None)
        streams = self.cdp_streams.pop(profile_id, None)
        if streams:
            for stream in streams:
                try:
                    stream.close()
                except OSError:
                    pass

    def stop_selected(self) -> None:
        profile_id = self.selected_id()
        process = self.processes.get(profile_id or "")
        if process and process.poll() is None:
            self.close_profile_process(profile_id or "")
            self.status_var.set(
                self.t(
                    "已停止选中实例。",
                    "Stopped the selected instance.",
                )
            )
        else:
            self.status_var.set(
                self.t(
                    "选中实例当前没有由本程序启动的进程。",
                    "The selected instance is not running under this manager.",
                )
            )

    def poll_processes(self) -> None:
        finished = [
            profile_id
            for profile_id, process in self.processes.items()
            if process.poll() is not None
        ]
        for profile_id in finished:
            self.processes.pop(profile_id, None)
            streams = self.cdp_streams.pop(profile_id, None)
            if streams:
                for stream in streams:
                    try:
                        stream.close()
                    except OSError:
                        pass
        if finished:
            self.refresh_profiles(self.selected_id())
        self.after(1200, self.poll_processes)


if __name__ == "__main__":
    app = ChromeMultiManager()
    app.mainloop()
