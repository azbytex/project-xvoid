from __future__ import annotations

import base64
import binascii
import datetime
import hashlib
import itertools
import mimetypes
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import quote, urlparse

import requests


if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

try:
    from rich import box
    from rich.align import Align
    from rich.console import Console, Group
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        DownloadColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeRemainingColumn,
        TransferSpeedColumn,
    )
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print("Library 'rich' belum terpasang.")
    print("Install dengan: pip install rich requests")
    raise SystemExit(1)

APP_NAME = "PROJECT-XVOID"
APP_VERSION = "1.0"
DEBUG = False

DEFAULT_TIMEOUT = 20
DOWNLOAD_TIMEOUT = 180
MAX_RETRIES = 2

LICENSE_EXPIRES_AT = "2099-12-31T23:59:59+07:00"
LICENSE_NAME = "PROJECT-XVOID"

# ─── SECURE MULTI-LAYER ENCRYPTED API VAULT (PROJECT-XVOID HYDRA) ───
import zlib as _zl

_XV_SEC = os.environ.get("XVOID_VAULT_SECRET", "XVOID_HYDRA_MASTER_KEY_v2.0_2026")
_XV_K = hashlib.sha256(_XV_SEC.encode("utf-8") + b"xv_vault_salt_99x").digest()

def _xv_dec(c: str) -> str:
    """Internal runtime dynamic decryptor for protected API endpoints."""
    if not c or not c.startswith("XV_"):
        return c
    d = bytearray(base64.urlsafe_b64decode(c[3:].encode("ascii")))
    L = len(d)
    for i in range(0, L - 1, 2):
        d[i], d[i+1] = d[i+1], d[i]
    klen = len(_XV_K)
    u = bytearray((b ^ _XV_K[idx % klen]) for idx, b in enumerate(d))
    return _zl.decompress(bytes(((x >> 3) | (x << 5)) & 0xFF for x in u)).decode("utf-8")

ALIGHT_MOTION_V1_URL = _xv_dec("XV_yh2a-SP7Qh0LWkZZ6MnMhtPIP2by2rRoz-XSgTaH3JMkWJT3XYv3TDiUC0g=")
ALIGHT_MOTION_API_KEY = _xv_dec("XV_yh2C_QDgljbTinlS18LLjiAXfTCFBacB")
ALIGHT_MOTION_V2_URL = _xv_dec("XV_yh2a-SP7Qh0LWl5a38HLmsjgG2Y1wrhwwzIang5X53xav-MBOyVcDS5UQHgCMsnEOeyy")
ALIGHT_MOTION_ORIGIN = _xv_dec("XV_yh2a-SP7Qh0LWl5a38HLmsjgG2Y1wrhwwzIang5XnfpYOo33")
ALIGHT_MOTION_REFERER = _xv_dec("XV_yh2a-SP7Qh0LWl5a38HLmsjgG2Y1wrhwwzIang5X53xypLL9C-COEtxaBLnLoNXyIg==")

STROM_AI_CHAT_URL = _xv_dec("XV_yh2a-SP7Qh0LWmVZz-kDstfkI47K0Yxv5wL6khav34QUv3anMoSl")
STROM_AI_MODE = "strom"
STROM_AI_USER_ID = "termux_user"
STROM_AI_ORIGIN = _xv_dec("XV_yh2a-SP7Qh0LWmVZz-kDstfkI47K0YxvnYTXAVRJ")
STROM_AI_REFERER = _xv_dec("XV_yh2a-SP7Qh0LWmVZz-kDstfkI47K0YxvpQKP8ywUQw==")

XVOID_AI_NAME = "XVoid"
XVOID_SYSTEM_PROMPT = _xv_dec("XV_yh1ZzBlodkJorGxwtqeDvNE8fsPq5alcc_XwM67dfbo2BiLUBItU3QkSQCHYBOq7cxZWvfPQcnyZGtzvJYdFQFk88g04G_lsFsWvmuPsM_OGUXsFhWQJvyU47jUkF1nkmfD51ijl4TzDO5KZ1NuqBuZCwMTn8CYjnEAi3uBIDOpm81j0FVAo5le2CeuyjLIn5PDFEOly68AxOPvQlfRSR-xtqghb8cqPKNHiaSQYg2wmiS1J5cgYkjOLNjjDR5Z1-ll3NuPBrb3mX0W8e10Sz1c3VGnJZJhHysEFZU9As0pdZpfctA==")

CEK_NOMOR_BASE_URL = _xv_dec("XV_yh2a-SP7Qh0LWnVaP-b7pdj3FGIyKo9D3_3tmhl_81R-lG32HOhZIsu1bmb_0uSCsb5C5FE0")
CEK_NOMOR_HEADERS = {
    "sec-ch-ua-platform": '"Android"',
    "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36",
    "accept": "application/json",
    "sec-ch-ua": '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
    "content-type": "application/json",
    "sec-ch-ua-mobile": "?1",
    "origin": _xv_dec("XV_yh2a-SP7Qh0LWmpZ4-bLvvjAI57i3pxv7O3VsRpYO4dqhPPZzLKXpSg="),
    "sec-fetch-site": "cross-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": _xv_dec("XV_yh2a-SP7Qh0LWmpZ4-bLvvjAI57i3pxv7O3VsRpYO4dqhHXZaoqnU-us"),
    "accept-language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
    "priority": "u=1, i",
}

BUAT_GAMBAR_URL = _xv_dec("XV_yh2a-SP7Qh0LWm1aMOH3QuPX00IK5peXOxXajQ5jM4hmpIHJONu9PY1ihCDx3-I=")
BUAT_GAMBAR_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
    "content-type": "application/json",
    "origin": _xv_dec("XV_yh2a-SP7Qh0LWk1a8_L3YpHoHChEwQI="),
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "sec-fetch-dest": "empty",
    "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36",
    "sec-ch-ua": '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "priority": "u=1, i",
}
BUAT_GAMBAR_MODELS = ["sdxl", "flux", "flux-pro", "dall-e-3"]
BUAT_GAMBAR_ASPECT_RATIOS = ["1:1", "16:9", "9:16", "4:3", "3:4"]

SCANREPO_API = _xv_dec("XV_yh2a-SP7Qh0LWm1ZJ9nfldf8L3Eq1bSP9MbGbSpopVQclkWnCg5_")
SCANREPO_USER_AGENT = "ScanRepoCLI/1.0"

VIEW_SOURCE_TOKEN_URL = _xv_dec("XV_yh2a-SP7Qh0LWm1ZJ9nzldjsFJYO_kBL6-XVih5bx1xiqKEJLNOO-suCelKZuM5e9_Y=")
VIEW_SOURCE_FETCH_URL = _xv_dec("XV_yh2a-SP7Qh0LWm1ZJ9nzldjsFJYO_kBL6-XVih5bx1xiqKEJLNON-tyWYmqZoNVePPY=")
VIEW_SOURCE_ORIGIN = _xv_dec("XV_yh2a-SP7Qh0LWm1ZJ9nzldjsFJYO_kBL6-XVih5bx1xiqNuP3oSPPA==")
VIEW_SOURCE_REFERER = _xv_dec("XV_yh2a-SP7Qh0LWm1ZJ9nzldjsFJYO_kBL6-XVih5bx1xiqOMJ_LKX-j0=")

TIKTOK_API_URL = _xv_dec("XV_yh2a-SP7Qh0LWnVaP-bblfDvMEHq6YNvwyq0kStF2s8_YmeUUZVLA70E7SDhLtw=")
TIKTOK_REFERER = _xv_dec("XV_yh2a-SP7Qh0LWnVaP-bblfDvMEHq6YNvwyoykWwx6-7Qlg==")

ASPOSE_WEB_TO_ZIP_URL = _xv_dec("XV_yh2a-SP7Qh0LWnVaP-bslcvYF2ElzbSH7O3FtcJ7_Kian6ndJNxBFcO2TV7w-uedoefjZVgHDr55gBp0rShsDLkj3oJLF2J5G81CkZk5V8yoUHo=")
ASPOSE_DOWNLOAD_BASE_URL = _xv_dec("XV_yh2NDzq4dlqVjOwmdO9O89Wsaa5GmnFbC2PCOgDnWSdk9sCuBcG-TX3uEmju833iHNEjS-NDc3W-bREA3My9")
ASPOSE_ORIGIN = _xv_dec("XV_yh2a-SP7Qh0LWlVZ4_bHhfj_J54d3Zd3M_7dqWxIEfJMd-Q=")
ASPOSE_REFERER = _xv_dec("XV_yh2a-SP7Qh0LWlVZ4_bHhfj_J54d3Zd3M_7dqepIncp6Amf3")

WEB2APK_START_URL = _xv_dec("XV_yh2a-SP7Qh0LWkJawMbLhsvUO0kyGkhc_9KEfcucB6x4QoM3xSetAOlcs3II8K2c2woFoA==")
WEB2APK_STATUS_URL = _xv_dec("XV_yh2a-SP7Qh0LWkJawMbLhsvUO0kyGkhc_9KEfcucB6x4QoM3xSetAO9cSHLJD_1dpI714ZA=")
WEB2APK_POLL_INTERVAL = 3
WEB2APK_POLL_LIMIT = 100

WEB2APK_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36",
    "Accept": "*/*",
    "Origin": _xv_dec("XV_yh2a-SP7Qh0LWkJawMbLhsjUA2YlwreH9_biZWRrGfJM4Z0="),
    "Referer": _xv_dec("XV_yh2a-SP7Qh0LWkJawMbLhsjUA2YlwreH9_biZeJrncr2Amj3"),
    "Accept-Language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
}

POLLINATIONS_TEXT_URL = _xv_dec("XV_yh2a-SP7Qh0LWl5Z2M30Qs_IM2Y22qBQ4-oKqgpTpVQh3oPXog==")
POLLINATIONS_IMAGE_URL = _xv_dec("XV_yh2a-SP7Qh0LWnJe-8oDtvfXM1YK8o9r-8LljTa_O5Rdp6XxK9vP0uXMZMso")

console = Console(highlight=False, soft_wrap=True, markup=True)


class Colors:
    PRIMARY = "bright_cyan"
    SECONDARY = "bright_magenta"
    SUCCESS = "bright_green"
    ERROR = "bright_red"
    WARNING = "bright_yellow"
    MUTED = "grey62"
    WHITE = "white"
    BLUE = "bright_blue"


class UI:
    WIDTH_MIN = 60
    WIDTH_MAX = 100

    @staticmethod
    def width(default: int = 78) -> int:
        try:
            cols = shutil.get_terminal_size((default, 24)).columns
        except OSError:
            cols = default
        return max(UI.WIDTH_MIN, min(cols, UI.WIDTH_MAX))

    @staticmethod
    def clear() -> None:
        console.clear()

    @staticmethod
    def rule(title: str = "") -> None:
        console.rule(title, style=Colors.MUTED)

    @staticmethod
    def header(title: str = APP_NAME, subtitle: str = "Modular Terminal Toolkit") -> None:
        content = Group(
            Align.center(Text(title, style=f"bold {Colors.SECONDARY}")),
            Align.center(Text(subtitle, style=Colors.MUTED)),
        )
        console.print(
            Panel(
                content,
                box=box.DOUBLE,
                border_style=Colors.SECONDARY,
                padding=(1, 3),
                expand=True,
            )
        )

    @staticmethod
    def section(title: str, icon: str = "◆") -> None:
        console.print()
        console.print(
            Panel(
                Text(f"{icon} {title}", style=f"bold {Colors.PRIMARY}"),
                border_style=Colors.PRIMARY,
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )

    @staticmethod
    def success(text: str) -> None:
        console.print(
            Panel(
                Text(f"✓ {text}", style=f"bold {Colors.SUCCESS}"),
                border_style=Colors.SUCCESS,
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )

    @staticmethod
    def error(text: str) -> None:
        console.print(
            Panel(
                Text(f"✗ {text}", style=f"bold {Colors.ERROR}"),
                border_style=Colors.ERROR,
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )

    @staticmethod
    def warning(text: str) -> None:
        console.print(
            Panel(
                Text(f"! {text}", style=f"bold {Colors.WARNING}"),
                border_style=Colors.WARNING,
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )

    @staticmethod
    def info(text: str) -> None:
        console.print(Text(text, style=Colors.MUTED))

    @staticmethod
    def label(key: str, value: str, key_width: int = 16) -> None:
        grid = Table.grid(padding=(0, 1))
        grid.add_column(width=key_width, justify="left", style=f"bold {Colors.PRIMARY}")
        grid.add_column(justify="left", style=Colors.WHITE)
        grid.add_row(key, value)
        console.print(grid)

    @staticmethod
    def menu_item(number: str, title: str, description: str = "") -> None:
        grid = Table.grid(padding=(0, 1), expand=True)
        grid.add_column(width=4, justify="center", style=f"bold {Colors.PRIMARY}")
        grid.add_column(width=23, style=f"bold {Colors.WHITE}")
        grid.add_column(style=Colors.MUTED)
        grid.add_row(number, title, description)
        console.print(grid)

    @staticmethod
    def success_box(title: str = "SUCCESS", message: str = "") -> None:
        console.print(
            Panel(
                Align.center(Text(message, style=f"bold {Colors.SUCCESS}")),
                title=title,
                title_align="center",
                border_style=Colors.SUCCESS,
                box=box.DOUBLE,
                padding=(1, 2),
                expand=True,
            )
        )

    @staticmethod
    def pause(message: str = "Enter untuk kembali...") -> None:
        try:
            console.input(f"\n[{Colors.PRIMARY}]{message}[/{Colors.PRIMARY}]")
        except (EOFError, KeyboardInterrupt):
            pass

    @staticmethod
    def input(label: str, default: str = "", password: bool = False) -> str:
        if default:
            prompt = f"[bold {Colors.PRIMARY}]{label}[/bold {Colors.PRIMARY}] [{Colors.MUTED}][{default}][/{Colors.MUTED}] › "
        else:
            prompt = f"[bold {Colors.PRIMARY}]{label}[/bold {Colors.PRIMARY}] › "
        if password:
            return console.input(prompt, password=True).strip()
        return console.input(prompt).strip()

    @staticmethod
    def footer() -> None:
        console.print()
        console.rule(style=Colors.MUTED)


class Spinner:
    def __init__(self, message: str) -> None:
        self.message = message
        self._status = None

    def __enter__(self) -> "Spinner":
        self._status = console.status(
            f"[bold {Colors.PRIMARY}]{self.message}[/bold {Colors.PRIMARY}]",
            spinner="dots",
        )
        self._status.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._status:
            self._status.stop()


def show_startup_animation() -> None:
    UI.clear()
    steps = ("Initializing", "Loading modules", "Preparing workspace")
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold bright_cyan]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task(steps[0], total=len(steps))
        for msg in steps:
            progress.update(task, description=msg, advance=1)
            time.sleep(0.18)
    UI.header()


class LicenseExpiredError(RuntimeError):
    pass


class LicenseManager:
    def __init__(self, expires_at: str) -> None:
        try:
            self.expires_at = datetime.datetime.fromisoformat(expires_at)
        except ValueError as exc:
            raise ValueError("LICENSE_EXPIRES_AT harus menggunakan ISO-8601.") from exc
        if self.expires_at.tzinfo is None:
            raise ValueError("LICENSE_EXPIRES_AT harus menyertakan timezone.")

    def now(self) -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc).astimezone(self.expires_at.tzinfo)

    def remaining(self) -> datetime.timedelta:
        return self.expires_at - self.now()

    def is_expired(self) -> bool:
        return self.remaining().total_seconds() <= 0

    def require_valid(self) -> None:
        if self.is_expired():
            raise LicenseExpiredError(f"License {LICENSE_NAME} expired pada {self.expires_at.isoformat()}")

    def formatted_remaining(self) -> str:
        sec = int(self.remaining().total_seconds())
        if sec <= 0:
            return "EXPIRED"
        days, sec = divmod(sec, 86400)
        hours, sec = divmod(sec, 3600)
        minutes, seconds = divmod(sec, 60)
        return f"{days}d {hours:02d}h {minutes:02d}m {seconds:02d}s"

    def formatted_expiry(self) -> str:
        return self.expires_at.strftime("%Y-%m-%d %H:%M:%S %z")

    def show_status(self) -> None:
        tbl = Table(box=box.SIMPLE_HEAVY, border_style=Colors.MUTED, expand=True)
        tbl.add_column("License", style=f"bold {Colors.PRIMARY}")
        tbl.add_column("Expires", style=Colors.WHITE)
        tbl.add_column("Remaining", justify="right", style=f"bold {Colors.SUCCESS}")
        tbl.add_row(LICENSE_NAME, self.formatted_expiry(), self.formatted_remaining())
        console.print(tbl)


LICENSE = LicenseManager(LICENSE_EXPIRES_AT)


@dataclass(frozen=True)
class ApiMethod:
    name: str
    label: str
    endpoint: str
    http_method: str


V1 = ApiMethod("v1", "Method V1 — GET", ALIGHT_MOTION_V1_URL, "GET")
V2 = ApiMethod("v2", "Method V2 — POST", ALIGHT_MOTION_V2_URL, "POST")


class ServiceError(RuntimeError):
    pass


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PACKAGE_NAME_REGEX = re.compile(r"[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)+")


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_REGEX.fullmatch(value))


def is_valid_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def is_valid_package_name(value: str) -> bool:
    return bool(PACKAGE_NAME_REGEX.fullmatch(value))


def is_valid_tiktok_url(value: str) -> bool:
    val = value.lower()
    return is_valid_url(value) and ("tiktok.com/" in val or "vt.tiktok.com/" in val)


def extract_message(payload: Any, default: str = "Tidak ada pesan.") -> str:
    if isinstance(payload, dict):
        for key in ("message", "msg", "error", "detail", "content"):
            val = payload.get(key)
            if val:
                return str(val)
    if isinstance(payload, str) and payload.strip():
        return payload.strip()
    return default


def is_success_status(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    status = payload.get("status")
    if isinstance(status, bool):
        return status
    if isinstance(status, str):
        return status.strip().lower() in {"true", "ok", "success", "successful", "1"}
    return bool(payload.get("success") is True or payload.get("verified") is True)


def extract_order_code(payload: Any) -> Optional[str]:
    if not isinstance(payload, dict):
        return None
    for key in ("codeorder", "code_order", "codeOrder", "order_code", "orderCode", "code"):
        val = payload.get(key)
        if val not in (None, ""):
            return str(val)
    return None


def extract_data_containers(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    containers = [payload]
    for key in ("data", "result"):
        val = payload.get(key)
        if isinstance(val, dict):
            containers.append(val)
    return containers


def extract_build_id(payload: Any) -> Optional[str]:
    for container in extract_data_containers(payload):
        for key in ("build_id", "buildId", "id"):
            val = container.get(key)
            if val not in (None, ""):
                return str(val)
    return None


def extract_download_url(payload: Any) -> Optional[str]:
    for container in extract_data_containers(payload):
        for key in ("download_url", "downloadUrl", "url"):
            val = container.get(key)
            if isinstance(val, str) and is_valid_url(val):
                return val
    return None


def extract_status(payload: Any) -> str:
    for container in extract_data_containers(payload):
        for key in ("status", "state"):
            val = container.get(key)
            if val not in (None, ""):
                return str(val).strip().lower()
    return ""


def prompt_validated(
    label: str,
    validator: Optional[Callable[[str], bool]] = None,
    error_message: str = "Input tidak valid.",
) -> str:
    while True:
        try:
            value = UI.input(label)
        except (EOFError, KeyboardInterrupt):
            raise KeyboardInterrupt
        if not value:
            UI.error("Input tidak boleh kosong.")
            continue
        if validator and not validator(value):
            UI.error(error_message)
            continue
        return value


class HttpClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, image/*, */*"
        })

    def request_json(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> Any:
        last_exc: Optional[Exception] = None
        for attempt in range(1, MAX_RETRIES + 2):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=headers,
                    timeout=timeout,
                )
                try:
                    payload = response.json()
                except ValueError:
                    payload = response.text
                if response.status_code >= 400:
                    raise ServiceError(f"HTTP {response.status_code}: {extract_message(payload)}")
                if DEBUG:
                    self._debug_payload(payload)
                return payload
            except (requests.RequestException, ServiceError) as exc:
                last_exc = exc
                if attempt <= MAX_RETRIES:
                    time.sleep(0.7 * attempt)
        raise ServiceError(str(last_exc) if last_exc else "Request gagal.")

    @staticmethod
    def _debug_payload(payload: Any) -> None:
        if isinstance(payload, dict):
            console.print(f"[dim][DEBUG] Response keys: {list(payload.keys())}[/dim]")
            if "content" in payload:
                preview = str(payload["content"])[:100]
                console.print(f"[dim][DEBUG] content preview: {preview}...[/dim]")
        else:
            console.print(f"[dim][DEBUG] Response type: {type(payload).__name__}[/dim]")

    def download(self, url: str, output_path: Path, *, headers: Optional[dict[str, str]] = None) -> int:
        try:
            with self.session.get(url, headers=headers, stream=True, timeout=DOWNLOAD_TIMEOUT) as response:
                response.raise_for_status()
                total_bytes = 0
                content_length = response.headers.get("content-length")
                total_size = int(content_length) if content_length and content_length.isdigit() else None
                with output_path.open("wb") as file:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[bold bright_cyan]{task.description}"),
                        BarColumn(),
                        DownloadColumn(),
                        TransferSpeedColumn(),
                        TimeRemainingColumn(),
                        console=console,
                    ) as progress:
                        task = progress.add_task("Downloading", total=total_size)
                        for chunk in response.iter_content(chunk_size=131072):
                            if not chunk:
                                continue
                            file.write(chunk)
                            total_bytes += len(chunk)
                            progress.update(task, advance=len(chunk))
                return total_bytes
        except (requests.RequestException, OSError) as exc:
            raise ServiceError(f"Gagal mengunduh file: {exc}") from exc


class LeviathanService:
    def __init__(self, http: Optional[HttpClient] = None) -> None:
        self.http = http or HttpClient()

    def send_magic_link(self, version: str, email: str) -> Any:
        if version == "v1":
            return self.http.request_json(
                "GET",
                ALIGHT_MOTION_V1_URL,
                params={"action": "send", "apikey": ALIGHT_MOTION_API_KEY, "email": email},
            )
        if version == "v2":
            return self.http.request_json(
                "POST",
                ALIGHT_MOTION_V2_URL,
                json_data={"action": "send", "email": email},
            )
        raise ValueError(f"Method tidak dikenal: {version}")

    def verify_magic_link(self, version: str, email: str, link: str) -> Any:
        if version == "v1":
            return self.http.request_json(
                "GET",
                ALIGHT_MOTION_V1_URL,
                params={"action": "verif", "apikey": ALIGHT_MOTION_API_KEY, "email": email, "url": link},
            )
        if version == "v2":
            return self.http.request_json(
                "POST",
                ALIGHT_MOTION_V2_URL,
                json_data={"action": "verify", "email": email, "link": link},
                headers={
                    "Content-Type": "application/json",
                    "Accept": "*/*",
                    "Origin": ALIGHT_MOTION_ORIGIN,
                    "Referer": ALIGHT_MOTION_REFERER,
                },
            )
        raise ValueError(f"Method tidak dikenal: {version}")

    def ai_chat(
        self,
        prompt: str,
        *,
        session_id: Optional[str] = None,
        user_id: str = STROM_AI_USER_ID,
        mode: str = STROM_AI_MODE,
        image: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> Any:
        full_prompt = f"{XVOID_SYSTEM_PROMPT}\n\nUser: {prompt}" if not session_id else prompt

        # 1. Coba primary Strom AI endpoint dengan timeout cepat & support mode
        try:
            res = self.http.session.post(
                STROM_AI_CHAT_URL,
                json={
                    "prompt": full_prompt,
                    "sessionId": session_id,
                    "image": image,
                    "mimeType": mime_type,
                    "userId": user_id,
                    "mode": mode or STROM_AI_MODE,
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "*/*",
                    "Origin": STROM_AI_ORIGIN,
                    "Referer": STROM_AI_REFERER,
                },
                timeout=6,
            )
            if res.ok:
                try:
                    payload = res.json()
                    if isinstance(payload, dict) and (payload.get("reply") or payload.get("text") or payload.get("content")):
                        return payload
                except ValueError:
                    pass
        except Exception:
            pass

        # 2. Fast AI Fallback (Pollinations AI Fast Text Endpoint - <1.5 detik)
        try:
            sys_msg = _xv_dec("XV_yh2_zDro9UqdTINdnNCxAYCJ_-1-PJeEr8OPKCpu3RHqKGavOcVd1kB0VfB6wlnfLT-_MM7ZCpr4vpAneiFYkXXxCeD1zh__rbLAV0lkeTpgk1iyCaaLat3vcRUrDKXko7FCSO-4BRpiZpUc5CrzIJkJzZCmHQ==")
            fast_res = self.http.session.post(
                POLLINATIONS_TEXT_URL,
                json={
                    "messages": [
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": prompt}
                    ],
                    "model": "openai",
                    "seed": random.randint(1000, 999999),
                    "jsonMode": False
                },
                timeout=6,
            )
            if fast_res.ok and fast_res.text.strip():
                reply_clean = sanitize_xvoid_text(fast_res.text.strip())
                return {
                    "text": reply_clean,
                    "sessionId": session_id or f"xvoid_fast_{int(time.time())}",
                    "provider": "xvoid-fast-engine"
                }
        except Exception:
            pass

        # 3. Fallback direct response jika semua network offline
        return {
            "text": f"Halo! Aku XVoid dari Project-XVOID. Aku telah menerima pesanmu: '{prompt}'. Sistem sedang berjalan optimal!",
            "sessionId": session_id or "xvoid_local",
            "provider": "xvoid-core"
        }

    def buat_gambar(
        self,
        prompt: str,
        model: str = "flux",
        aspect_ratio: str = "1:1",
        style: str = "none",
        negative_prompt: str = "",
        seed: Optional[int] = None,
    ) -> dict[str, Any]:
        """Generate gambar AI stabil & unik dengan model Flux/Turbo dan base64 caching."""
        ratio_dimensions = {
            "1:1": (512, 512),
            "16:9": (640, 360),
            "9:16": (360, 640),
            "4:3": (512, 384),
            "3:4": (384, 512),
        }
        width, height = ratio_dimensions.get(aspect_ratio, (512, 512))
        active_seed = seed if seed is not None else random.randint(1000000, 999999999)

        # Mapping model ke model resmi Pollinations AI
        m_lower = model.lower()
        enhanced_prompt = prompt

        if "real" in m_lower:
            poll_model = "flux-realism"
            enhanced_prompt = f"{prompt}, photorealistic, 8k uhd, dslr quality"
            if not negative_prompt:
                negative_prompt = "cartoon, drawing, anime, blurry, lowres"
        elif "anime" in m_lower:
            poll_model = "flux-anime"
            enhanced_prompt = f"{prompt}, anime visual, vivid colors, Makoto Shinkai style, masterpiece"
            if not negative_prompt:
                negative_prompt = "photorealistic, 3d, ugly, deformed, blurry"
        elif "3d" in m_lower or "cgi" in m_lower:
            poll_model = "flux-3d"
            enhanced_prompt = f"{prompt}, 3d octane render, cinema 4d, unreal engine 5, ray tracing"
        elif "turbo" in m_lower or "fast" in m_lower:
            poll_model = "turbo"
            enhanced_prompt = f"{prompt}, vibrant detailed art, high quality"
        else:
            poll_model = "flux"
            enhanced_prompt = f"{prompt}, ultra high quality, fine details"

        encoded_prompt = quote(enhanced_prompt)
        poll_url = f"{POLLINATIONS_IMAGE_URL}{encoded_prompt}?width={width}&height={height}&model={poll_model}&seed={active_seed}&nologo=true"
        hd_url = f"{POLLINATIONS_IMAGE_URL}{encoded_prompt}?width=1024&height=1024&model={poll_model}&seed={active_seed}&nologo=true"

        if negative_prompt:
            neg_encoded = quote(negative_prompt)
            poll_url += f"&negative={neg_encoded}"
            hd_url += f"&negative={neg_encoded}"

        # Fetch image bytes langsung dari backend agar gambar 100% muncul & anti-broken
        b64_data = ""
        used_model = poll_model
        try:
            img_res = self.http.session.get(poll_url, timeout=18)
            if img_res.ok and len(img_res.content) > 1000:
                b64_data = base64.b64encode(img_res.content).decode("ascii")
            else:
                # Jika model lambat/error, fallback cepat ke model turbo
                fallback_url = f"{POLLINATIONS_IMAGE_URL}{encoded_prompt}?width={width}&height={height}&model=turbo&seed={active_seed}&nologo=true"
                fb_res = self.http.session.get(fallback_url, timeout=10)
                if fb_res.ok and len(fb_res.content) > 1000:
                    b64_data = base64.b64encode(fb_res.content).decode("ascii")
                    poll_url = fallback_url
                    used_model = "turbo"
        except Exception:
            # Fallback darurat ke turbo jika timeout
            try:
                fallback_url = f"{POLLINATIONS_IMAGE_URL}{encoded_prompt}?width={width}&height={height}&model=turbo&seed={active_seed}&nologo=true"
                fb_res = self.http.session.get(fallback_url, timeout=10)
                if fb_res.ok and len(fb_res.content) > 1000:
                    b64_data = base64.b64encode(fb_res.content).decode("ascii")
                    poll_url = fallback_url
                    used_model = "turbo"
            except Exception:
                pass

        return {
            "provider": f"Pollinations AI Engine ({used_model})",
            "url": hd_url,
            "preview_url": poll_url,
            "b64_json": b64_data,
            "seed": active_seed,
            "aspect_ratio": aspect_ratio,
            "model": model,
            "prompt": prompt,
        }






    def get_page_source_token(self) -> str:
        res = self.http.request_json(
            "GET",
            VIEW_SOURCE_TOKEN_URL,
            headers={
                "Accept": "*/*",
                "Origin": VIEW_SOURCE_ORIGIN,
                "Referer": VIEW_SOURCE_REFERER,
            },
        )
        if not isinstance(res, dict):
            raise ServiceError("Response token tidak valid.")
        token = res.get("token")
        if not isinstance(token, str) or not token.strip():
            raise ServiceError("Token tidak ditemukan pada response.")
        return token.strip()

    def fetch_page_source(self, url: str, *, stylize: bool = True) -> Any:
        token = self.get_page_source_token()
        return self.http.request_json(
            "POST",
            VIEW_SOURCE_FETCH_URL,
            json_data={"url": url, "token": token, "stylize": stylize},
            headers={
                "Content-Type": "application/json",
                "Accept": "*/*",
                "Origin": VIEW_SOURCE_ORIGIN,
                "Referer": VIEW_SOURCE_REFERER,
            },
        )

    def web_to_zip(self, url: str) -> tuple[dict[str, Any], str]:
        try:
            response = self.http.session.post(
                ASPOSE_WEB_TO_ZIP_URL,
                files={"link_303108836": (None, url)},
                headers={"Accept": "*/*", "Origin": ASPOSE_ORIGIN, "Referer": ASPOSE_REFERER},
                timeout=DOWNLOAD_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise ServiceError(f"Gagal menghubungi Aspose: {exc}") from exc
        if response.status_code >= 400:
            raise ServiceError(f"Aspose HTTP {response.status_code}: {response.text[:300]}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ServiceError(f"Response Aspose bukan JSON: {response.text[:300]}") from exc
        if not isinstance(payload, dict):
            raise ServiceError("Response Aspose tidak valid.")
        if not payload.get("IsSuccess"):
            raise ServiceError(str(payload.get("Text") or "Konversi Web to ZIP gagal."))
        folder_name = payload.get("FolderName")
        file_name = payload.get("FileName")
        if not isinstance(folder_name, str) or not folder_name.strip():
            raise ServiceError("FolderName tidak ditemukan.")
        if not isinstance(file_name, str) or not file_name.strip():
            raise ServiceError("FileName tidak ditemukan.")
        download_url = f"{ASPOSE_DOWNLOAD_BASE_URL}/{quote(folder_name.strip(), safe='')}?file={quote(file_name.strip(), safe='')}"
        return (payload, download_url)

    def tiktok_info(self, url: str) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
        }
        try:
            response = self.http.session.get(
                TIKTOK_API_URL,
                params={"url": url},
                headers=headers,
                timeout=DEFAULT_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise ServiceError(f"Gagal menghubungi API TikTok: {exc}") from exc
        if response.status_code >= 400:
            raise ServiceError(f"API TikTok HTTP {response.status_code}: {response.text[:300]}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ServiceError("Response API TikTok bukan JSON yang valid.") from exc
        if not isinstance(payload, dict) or not payload.get("status"):
            raise ServiceError(
                str(payload.get("message") if isinstance(payload, dict) else None)
                or "API TikTok mengembalikan status gagal."
            )
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ServiceError("Field data dari API TikTok tidak valid.")
        result: dict[str, str] = {}
        field_mapping = (
            ("no_watermark_link", "video_url"),
            ("no_watermark_link_hd", "video_hd_url"),
            ("music_link", "mp3_url"),
            ("author_nickname", "author"),
            ("text", "caption"),
            ("itemId", "item_id"),
            ("duration", "duration"),
            ("like_count", "like_count"),
            ("comment_count", "comment_count"),
            ("share_count", "share_count"),
            ("play_count", "play_count"),
        )
        for src_key, dest_key in field_mapping:
            val = data.get(src_key)
            if val not in (None, ""):
                result[dest_key] = str(val)
        images = data.get("images") or data.get("photo")
        if isinstance(images, list) and images:
            result["images"] = [str(x) for x in images if x]
        if not result.get("video_url") and not result.get("video_hd_url") and not result.get("images"):
            raise ServiceError("API tidak mengembalikan link video atau foto.")
        return result

    def universal_download_info(self, url: str) -> dict[str, Any]:
        """Ekstraksi metadata & direct download link untuk berbagai platform:
        TikTok, Instagram (foto/video/carousel/stories), YouTube, X/Twitter,
        Facebook, Pinterest, Reddit, dan ribuan situs lainnya.
        """
        raw_url = (url or "").strip()
        if not raw_url:
            raise ServiceError("URL media tidak boleh kosong.")

        # Deteksi platform
        u_lower = raw_url.lower()
        platform = "Media Universal"
        if "tiktok.com" in u_lower:
            platform = "TikTok"
        elif "instagram.com" in u_lower or "instagr.am" in u_lower:
            platform = "Instagram"
        elif "youtube.com" in u_lower or "youtu.be" in u_lower:
            platform = "YouTube"
        elif "twitter.com" in u_lower or "x.com" in u_lower:
            platform = "X (Twitter)"
        elif "facebook.com" in u_lower or "fb.watch" in u_lower:
            platform = "Facebook"
        elif "pinterest.com" in u_lower or "pin.it" in u_lower:
            platform = "Pinterest"
        elif "reddit.com" in u_lower:
            platform = "Reddit"

        # 1. TikTok: Coba API Siputzx tanpa watermark dulu
        if platform == "TikTok":
            try:
                tt_data = self.tiktok_info(raw_url)
                tt_data["platform"] = "TikTok"
                if not tt_data.get("title") and tt_data.get("caption"):
                    tt_data["title"] = tt_data["caption"]
                images = tt_data.pop("images", None)
                if images:
                    tt_data["media_type"] = "carousel"
                    tt_data["media_items"] = [
                        {"type": "photo", "url": img, "thumbnail": img, "filename": f"tiktok_foto_{i+1:02d}.jpg"}
                        for i, img in enumerate(images)
                    ]
                    tt_data["media_count"] = len(images)
                    if not tt_data.get("thumbnail") and images:
                        tt_data["thumbnail"] = images[0]
                else:
                    tt_data.setdefault("media_type", "video")
                    items = []
                    if tt_data.get("video_url"):
                        items.append({
                            "type": "video",
                            "url": tt_data.get("video_hd_url") or tt_data["video_url"],
                            "url_sd": tt_data["video_url"],
                            "thumbnail": tt_data.get("thumbnail") or "",
                            "filename": "tiktok_video.mp4"
                        })
                    tt_data["media_items"] = items
                    tt_data["media_count"] = len(items)
                return tt_data
            except Exception:
                pass  # fallback ke yt-dlp

        # 2. Universal Extractor via yt-dlp
        try:
            import yt_dlp
        except ImportError:
            raise ServiceError("Module yt-dlp belum terinstall. Jalankan: pip install yt-dlp")

        # Instagram carousel/slides/stories membutuhkan noplaylist=False
        is_instagram = platform == "Instagram"
        ydl_opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": not is_instagram,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(raw_url, download=False)
        except Exception as exc:
            err_msg = str(exc)
            if "Video unavailable" in err_msg or "Private" in err_msg:
                raise ServiceError("Video tidak tersedia atau bersifat privat.")
            if "No video formats" in err_msg.lower() or "no video formats" in err_msg.lower():
                if platform == "Pinterest":
                    return self._pinterest_image_fallback(raw_url)
                raise ServiceError(f"Tidak ditemukan format video yang bisa diunduh dari {platform}.")
            if "Login" in err_msg or "login" in err_msg.lower() or "authentication" in err_msg.lower():
                raise ServiceError(f"Konten {platform} ini membutuhkan login. Coba link yang bersifat publik.")
            raise ServiceError(f"Gagal memproses media dari {platform}: {err_msg[:200]}")

        if not info:
            raise ServiceError(f"Tidak dapat mengekstrak informasi media dari URL {platform}.")

        # Handle playlist / carousel (IG Slides, IG Stories, YouTube Playlist, dll.)
        entries = info.get("entries")
        if entries:
            return self._handle_media_playlist(info, list(entries), platform)

        return self._extract_single_media(info, platform)

    def _pinterest_image_fallback(self, url: str) -> dict[str, Any]:
        """Scrape Pinterest image via og:image meta tag."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,*/*;q=0.8",
            }
            resp = self.http.session.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            html = resp.text

            def og(prop: str) -> str:
                pat1 = r'<meta[^>]+property=["\']og:' + re.escape(prop) + r'["\'][^>]+content=["\']([^"\']+)["\']'
                pat2 = r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:' + re.escape(prop) + r'["\']'
                m = re.search(pat1, html)
                if not m:
                    m = re.search(pat2, html)
                return m.group(1) if m else ""

            img_url = og("image")
            title = og("title") or "Pinterest Image"
            author = og("description")[:80] if og("description") else "Pinterest"

            if img_url:
                img_url_hd = re.sub(r'/[0-9]+x/', '/originals/', img_url)
                return {
                    "platform": "Pinterest",
                    "author": author,
                    "caption": title,
                    "title": title,
                    "thumbnail": img_url,
                    "duration": "",
                    "view_count": "",
                    "like_count": "",
                    "video_url": "",
                    "video_hd_url": "",
                    "mp3_url": "",
                    "media_type": "photo",
                    "media_items": [
                        {"type": "photo", "url": img_url_hd, "thumbnail": img_url, "filename": "pinterest_image.jpg"}
                    ],
                    "media_count": 1,
                }
            raise ServiceError("Tidak ditemukan gambar dari halaman Pinterest ini.")
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(f"Gagal mengambil gambar Pinterest: {exc}") from exc

    def _handle_media_playlist(self, info: dict, entries: list, platform: str) -> dict[str, Any]:
        """Handle playlist / carousel (IG slides, stories, YouTube playlist, dll.)"""
        title = info.get("title") or info.get("description") or f"Media_{platform}"
        author = (
            info.get("uploader") or info.get("channel") or
            info.get("creator") or info.get("uploader_id") or platform
        )
        thumbnail = info.get("thumbnail") or ""

        media_items: list[dict[str, Any]] = []
        primary_video_url = ""
        primary_hd_url = ""
        primary_mp3_url = ""
        photo_count = 0
        video_count = 0

        for idx, entry in enumerate(entries[:50]):  # max 50 items
            if not entry:
                continue
            entry_title = entry.get("title") or title
            entry_thumb = entry.get("thumbnail") or thumbnail
            entry_formats = entry.get("formats") or []
            entry_url = entry.get("url") or ""
            entry_ext = (entry.get("ext") or "").lower()

            video_url_e = ""
            hd_url_e = ""

            if entry_formats:
                prog = [
                    f for f in entry_formats
                    if f.get("ext") == "mp4"
                    and (f.get("vcodec") or "none") != "none"
                    and (f.get("acodec") or "none") != "none"
                    and f.get("url")
                ]
                all_vid = [f for f in entry_formats if f.get("url") and (f.get("vcodec") or "none") != "none"]
                all_aud = [f for f in entry_formats if f.get("url") and (f.get("vcodec") or "") == "none"]

                if prog:
                    prog.sort(key=lambda x: x.get("height") or 0)
                    video_url_e = prog[0].get("url", "")
                    hd_url_e = prog[-1].get("url", "")
                elif all_vid:
                    all_vid.sort(key=lambda x: x.get("height") or 0)
                    video_url_e = all_vid[-1].get("url", "")
                elif all_aud:
                    all_aud.sort(key=lambda x: x.get("abr") or 0)
                    video_url_e = all_aud[-1].get("url", "")
                    entry_ext = "mp3"

            if not video_url_e:
                video_url_e = entry_url

            # Classify as photo or video
            is_photo = entry_ext in ("jpg", "jpeg", "png", "webp", "gif") or (
                entry_url and any(entry_url.lower().endswith(x) for x in (".jpg", ".jpeg", ".png", ".webp"))
            )

            if is_photo or (not entry_formats and entry_url and not any(
                k in entry_url.lower() for k in ("mp4", "video", "m3u8")
            )):
                media_type = "photo"
                photo_count += 1
                filename = f"foto_{idx+1:02d}.jpg"
            else:
                media_type = "video"
                video_count += 1
                filename = f"video_{idx+1:02d}.mp4"
                if not primary_video_url and video_url_e:
                    primary_video_url = video_url_e
                    primary_hd_url = hd_url_e or video_url_e

            if video_url_e:
                media_items.append({
                    "type": media_type,
                    "url": hd_url_e or video_url_e,
                    "url_sd": video_url_e,
                    "thumbnail": entry_thumb,
                    "filename": filename,
                    "title": entry_title,
                })

        # Overall audio
        for f in (info.get("formats") or []):
            if f.get("url") and (f.get("vcodec") or "") == "none":
                primary_mp3_url = f.get("url", "")

        if not media_items:
            return self._extract_single_media(info, platform)

        overall_type = "carousel" if (photo_count > 0 and video_count == 0) else "video"

        return {
            "platform": platform,
            "author": str(author).replace("@", ""),
            "caption": str(title)[:200],
            "title": str(title),
            "thumbnail": thumbnail,
            "duration": "",
            "view_count": str(info.get("view_count") or ""),
            "like_count": str(info.get("like_count") or ""),
            "video_url": primary_video_url,
            "video_hd_url": primary_hd_url or primary_video_url,
            "mp3_url": primary_mp3_url,
            "media_type": overall_type,
            "media_items": media_items,
            "media_count": len(media_items),
        }

    def _extract_single_media(self, info: dict, platform: str) -> dict[str, Any]:
        """Extract media info from a single yt-dlp result."""
        title = info.get("title") or info.get("description") or f"Media_{platform}"
        author = (
            info.get("uploader") or info.get("channel") or
            info.get("creator") or info.get("uploader_id") or platform
        )
        thumbnail = info.get("thumbnail") or ""
        duration_sec = info.get("duration")
        duration_str = ""
        if duration_sec:
            m, s = divmod(int(duration_sec), 60)
            duration_str = f"{m}:{s:02d}"

        formats = info.get("formats") or []
        video_url = info.get("url") or ""
        video_hd_url = ""
        mp3_url = ""

        prog_mp4 = [
            f for f in formats
            if f.get("ext") == "mp4"
            and (f.get("vcodec") or "none") != "none"
            and (f.get("acodec") or "none") != "none"
            and f.get("url")
        ]
        if prog_mp4:
            prog_mp4.sort(key=lambda x: x.get("height") or 0)
            video_url = prog_mp4[0].get("url", "")
            video_hd_url = prog_mp4[-1].get("url", "")
        elif not video_url and formats:
            vf = [f for f in formats if f.get("url") and (f.get("vcodec") or "none") != "none"]
            if vf:
                vf.sort(key=lambda x: x.get("height") or 0)
                video_url = vf[-1].get("url", "")

        af = [
            f for f in formats
            if f.get("url") and (
                (f.get("vcodec") or "") == "none"
                or "audio" in (f.get("format_note") or "").lower()
            )
        ]
        if af:
            af.sort(key=lambda x: x.get("abr") or 0)
            mp3_url = af[-1].get("url", "")

        if not video_url and not mp3_url:
            # Try image fallback
            if platform == "Pinterest":
                return self._pinterest_image_fallback(info.get("webpage_url") or "")
            thumbs = info.get("thumbnails") or []
            if thumbs:
                img_url = thumbs[-1].get("url", "")
                if img_url:
                    return {
                        "platform": platform,
                        "author": str(author).replace("@", ""),
                        "caption": str(title)[:200],
                        "title": str(title),
                        "thumbnail": thumbnail or img_url,
                        "duration": duration_str,
                        "view_count": str(info.get("view_count") or ""),
                        "like_count": str(info.get("like_count") or ""),
                        "video_url": "",
                        "video_hd_url": "",
                        "mp3_url": "",
                        "media_type": "photo",
                        "media_items": [{"type": "photo", "url": img_url, "thumbnail": img_url, "filename": "image.jpg"}],
                        "media_count": 1,
                    }
            raise ServiceError(f"Tidak ditemukan link unduhan untuk media {platform}.")

        media_items = []
        if video_url:
            media_items.append({
                "type": "video",
                "url": video_hd_url or video_url,
                "url_sd": video_url,
                "thumbnail": thumbnail,
                "filename": "video.mp4",
                "title": str(title),
            })

        return {
            "platform": platform,
            "author": str(author).replace("@", ""),
            "caption": str(title)[:200],
            "title": str(title),
            "thumbnail": thumbnail,
            "duration": duration_str,
            "view_count": str(info.get("view_count") or ""),
            "like_count": str(info.get("like_count") or ""),
            "video_url": video_url,
            "video_hd_url": video_hd_url or video_url,
            "mp3_url": mp3_url,
            "media_type": "video" if video_url else "audio",
            "media_items": media_items,
            "media_count": len(media_items),
        }

    def download_media(self, url: str, output_path: Path, referer: str = TIKTOK_REFERER) -> int:
        return self.http.download(
            url,
            output_path,
            headers={
                "Accept": "*/*",
                "Referer": referer,
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
            },
        )

    @staticmethod
    def encode_file_base64(file_path: str | Path) -> tuple[str, str, int]:
        path = Path(file_path).expanduser()
        if not path.is_file():
            raise ServiceError(f"File tidak ditemukan: {path}")
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ServiceError(f"Gagal membaca file: {exc}") from exc
        encoded = base64.b64encode(data).decode("ascii")
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return (encoded, mime_type, len(data))

    @staticmethod
    def decode_base64_to_file(encoded: str, output_path: str | Path) -> int:
        value = encoded.strip()
        if not value:
            raise ServiceError("Data Base64 kosong.")
        value = "".join(value.split())
        if value.lower().startswith("data:"):
            comma_idx = value.find(",")
            if comma_idx == -1:
                raise ServiceError("Format data URI tidak valid.")
            value = value[comma_idx + 1 :]
        try:
            raw_bytes = base64.b64decode(value, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ServiceError(f"Base64 tidak valid: {exc}") from exc
        path = Path(output_path).expanduser()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw_bytes)
        except OSError as exc:
            raise ServiceError(f"Gagal menulis file: {exc}") from exc
        return len(raw_bytes)

    @staticmethod
    def make_data_uri(encoded: str, mime_type: str) -> str:
        mime = mime_type.strip() or "application/octet-stream"
        return f"data:{mime};base64,{encoded}"

    def create_web2apk(
        self,
        app_name: str,
        website_url: str,
        package_name: str,
        version_name: str,
        version_code: str,
        app_icon_url: str,
    ) -> Any:
        fields = {
            "appName": app_name,
            "websiteUrl": website_url,
            "packageName": package_name,
            "versionName": version_name,
            "versionCode": version_code,
            "appIconUrl": app_icon_url,
        }
        try:
            response = self.http.session.post(
                WEB2APK_START_URL,
                files={k: (None, v) for k, v in fields.items()},
                headers=WEB2APK_HEADERS,
                timeout=DEFAULT_TIMEOUT,
            )
        except requests.RequestException as exc:
            raise ServiceError(f"Gagal membuat APK: {exc}") from exc
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
        if response.status_code >= 400:
            raise ServiceError(f"HTTP {response.status_code}: {extract_message(payload)}")
        return payload

    def web2apk_status(self, build_id: str) -> Any:
        return self.http.request_json(
            "GET",
            WEB2APK_STATUS_URL,
            params={"build_id": build_id},
            headers=WEB2APK_HEADERS,
        )

    def cek_nomor(self, nomor: str, lang: str = "id", region: str = "ID") -> dict[str, Any]:
        """Cek info nomor telepon menggunakan Kaspersky WhoCallsID API."""
        # Normalize nomor: 08xx -> 628xx
        n = "".join(c for c in nomor if c.isdigit())
        if n.startswith("0"):
            n = "62" + n[1:]
        elif n.startswith("620"):
            n = "62" + n[3:]
        try:
            info_url = f"{CEK_NOMOR_BASE_URL}/v2/number"
            info_res = self.http.session.get(
                info_url,
                params={"language": lang, "number": n},
                headers=CEK_NOMOR_HEADERS,
                timeout=DEFAULT_TIMEOUT,
            )
            info_data = info_res.json() if info_res.ok else {}
        except Exception:
            info_data = {}
        try:
            similar_url = f"{CEK_NOMOR_BASE_URL}/similar-numbers"
            sim_res = self.http.session.get(
                similar_url,
                params={"region": region, "number": n},
                headers=CEK_NOMOR_HEADERS,
                timeout=DEFAULT_TIMEOUT,
            )
            similar_data = sim_res.json() if sim_res.ok else {}
        except Exception:
            similar_data = {}
        return {"nomor_normalized": n, "info": info_data, "similar": similar_data}

    def scan_github_repo(self, repo_url: str) -> dict[str, Any]:
        """Scan repository GitHub menggunakan ScanRepo API."""
        try:
            response = self.http.session.post(
                SCANREPO_API,
                json={"url": repo_url},
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": SCANREPO_USER_AGENT,
                    "Accept": "application/json",
                },
                timeout=90,
            )
            if response.status_code == 200:
                return {"success": True, "result": response.json()}
            else:
                raise ServiceError(f"ScanRepo API mengembalikan status HTTP {response.status_code}: {response.text[:200]}")
        except requests.RequestException as exc:
            raise ServiceError(f"Gagal menghubungi ScanRepo API: {exc}") from exc


        raise ServiceError("Semua provider gambar sedang sibuk. Silakan coba beberapa saat lagi.")

    def scan_github_repo(self, repo_url: str) -> dict[str, Any]:
        """Scan keamanan GitHub repository menggunakan ScanRepo API."""
        headers = {
            "User-Agent": SCANREPO_USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                SCANREPO_API,
                json={"url": repo_url, "force": False},
                headers=headers,
                timeout=60,
            )
        except requests.RequestException as exc:
            raise ServiceError(f"Gagal scan repo: {exc}") from exc
        if not response.ok:
            raise ServiceError(f"HTTP {response.status_code}: {response.text[:300]}")
        scan_id = None
        result = None
        progress_log: list[dict] = []
        for line in response.text.strip().splitlines():
            if not line.strip():
                continue
            try:
                data_line = __import__('json').loads(line)
            except Exception:
                continue
            if data_line.get("type") == "progress":
                progress_log.append({
                    "step": data_line.get("step", "unknown"),
                    "progress": data_line.get("progress", 0),
                })
            elif data_line.get("type") == "result":
                result = data_line.get("data", {})
                scan_id = result.get("commitSha")
        if not scan_id or not result:
            raise ServiceError("Scan selesai tapi tidak ada data hasil.")
        return {"scan_id": scan_id, "result": result, "progress": progress_log}

    def inspect_web_ssl(self, target: str) -> dict[str, Any]:
        """Audit mendalam keamanan web & SSL: Cert details, Security Headers grading A-F, server recon."""
        import ssl
        import socket
        import datetime
        import urllib.parse
        import requests

        t = target.strip()
        if not t:
            raise ServiceError("Domain atau URL target tidak boleh kosong.")

        if "://" in t:
            parsed = urllib.parse.urlsplit(t)
            hostname = parsed.hostname or parsed.netloc or t
        else:
            hostname = t.split("/")[0].split(":")[0].strip()

        if not hostname:
            raise ServiceError("Format domain atau hostname tidak valid.")

        # 1. DNS & IP Resolution
        try:
            ip_list = socket.gethostbyname_ex(hostname)[2]
            if not ip_list:
                raise ServiceError(f"Domain '{hostname}' tidak dapat di-resolve (tidak ada IP ditemukan).")
            primary_ip = ip_list[0]
        except socket.gaierror:
            raise ServiceError(f"Domain '{hostname}' tidak terdaftar atau tidak ditemukan di server DNS.")
        except Exception as exc:
            if isinstance(exc, ServiceError):
                raise
            raise ServiceError(f"Gagal memeriksa DNS domain '{hostname}': {exc}")

        # 2. SSL Inspection
        ssl_info: dict[str, Any] = {"valid": False}
        has_ssl = False
        days_left = None
        issuer_name = "Tidak diketahui"

        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=7) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    tls_ver = ssock.version()
                    cipher_info = ssock.cipher()
                    has_ssl = True

                    issuer_dict = dict(x[0] for x in cert.get('issuer', []))
                    subject_dict = dict(x[0] for x in cert.get('subject', []))

                    issuer_name = issuer_dict.get('organizationName') or issuer_dict.get('commonName') or 'Tidak diketahui'
                    common_name = subject_dict.get('commonName') or hostname

                    not_before = cert.get('notBefore', '')
                    not_after = cert.get('notAfter', '')

                    if not_after:
                        expire_dt = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                        days_left = (expire_dt - datetime.datetime.utcnow()).days

                    sans = [v for k, v in cert.get('subjectAltName', []) if k == 'DNS']

                    ssl_info = {
                        "valid": True,
                        "issuer": issuer_name,
                        "common_name": common_name,
                        "not_before": not_before,
                        "not_after": not_after,
                        "days_remaining": days_left,
                        "is_expired": (days_left < 0) if days_left is not None else False,
                        "tls_version": tls_ver or "TLS",
                        "cipher": cipher_info[0] if cipher_info else "Tidak diketahui",
                        "sans_count": len(sans),
                        "sans_sample": sans[:6]
                    }
        except Exception as ssl_err:
            ssl_info = {
                "valid": False,
                "error": str(ssl_err),
                "days_remaining": None,
                "is_expired": True,
                "tls_version": "-",
                "cipher": "-"
            }

        # 3. HTTP Security Headers Audit
        headers_audit: dict[str, Any] = {}
        findings: list[dict[str, str]] = []
        recommendations: list[str] = []
        score = 100
        server_banner = "Disembunyikan / Tidak Terdeteksi"
        status_code = 0
        http_proto = "HTTP/1.1"

        try:
            resp = requests.get(
                f"https://{hostname}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Project-XVoid/1.0"},
                timeout=7,
                allow_redirects=True
            )
            h = {k.lower(): v for k, v in resp.headers.items()}
            status_code = resp.status_code
            server_banner = resp.headers.get('Server') or resp.headers.get('server') or "Disembunyikan / Tidak Terdeteksi"
        except Exception:
            h = {}

        # Evaluate SSL Status
        if has_ssl and ssl_info.get("valid") and not ssl_info.get("is_expired"):
            findings.append({
                "type": "pass",
                "title": "Sertifikat SSL Aktif & Terpercaya",
                "desc": f"Diterbitkan oleh {issuer_name}. Masa berlaku tersisa {days_left} hari dengan enkripsi {ssl_info.get('tls_version')} ({ssl_info.get('cipher')})."
            })
        else:
            score -= 35
            findings.append({
                "type": "crit",
                "title": "Sertifikat SSL Tidak Valid / Bermasalah",
                "desc": ssl_info.get("error") or "Koneksi HTTPS aman tidak dapat diverifikasi."
            })
            recommendations.append("Pasang atau perbarui sertifikat SSL/TLS valid untuk mengamankan enkripsi data pengguna.")

        # Evaluate HSTS
        if "strict-transport-security" in h:
            val = h["strict-transport-security"]
            headers_audit["hsts"] = {"present": True, "value": val, "status": "PASS", "label": "Strict-Transport-Security (HSTS)"}
            findings.append({
                "type": "pass",
                "title": "Proteksi HSTS Terpasang",
                "desc": f"Memaksa browser hanya mengakses via HTTPS terenkripsi. Aturan: {val}"
            })
        else:
            score -= 20
            headers_audit["hsts"] = {"present": False, "value": None, "status": "FAIL", "label": "Strict-Transport-Security (HSTS)"}
            findings.append({
                "type": "warn",
                "title": "Header HSTS Tidak Ditemukan",
                "desc": "Situs tidak memaksa browser selalu menggunakan HTTPS, rentan terhadap serangan downgrade SSL stripping."
            })
            recommendations.append("Aktifkan Strict-Transport-Security dengan max-age minimal 1 tahun (max-age=31536000; includeSubDomains).")

        # Evaluate CSP
        if "content-security-policy" in h:
            val = h["content-security-policy"]
            headers_audit["csp"] = {"present": True, "value": (val[:100] + '...') if len(val) > 100 else val, "status": "PASS", "label": "Content-Security-Policy (CSP)"}
            findings.append({
                "type": "pass",
                "title": "Content-Security-Policy (CSP) Aktif",
                "desc": "Membatasi eksekusi skrip eksternal dan melindungi dari injeksi Cross-Site Scripting (XSS)."
            })
        else:
            score -= 20
            headers_audit["csp"] = {"present": False, "value": None, "status": "FAIL", "label": "Content-Security-Policy (CSP)"}
            findings.append({
                "type": "warn",
                "title": "Content-Security-Policy (CSP) Belum Dipasang",
                "desc": "Situs tidak memiliki pembatasan sumber script, meningkatkan risiko injeksi XSS dan pencurian session."
            })
            recommendations.append("Konfigurasikan Content-Security-Policy untuk mengatur domain terpercaya yang boleh memuat skrip/gaya.")

        # Evaluate X-Frame-Options
        if "x-frame-options" in h:
            val = h["x-frame-options"]
            headers_audit["x_frame_options"] = {"present": True, "value": val, "status": "PASS", "label": "X-Frame-Options (Anti-Clickjacking)"}
            findings.append({
                "type": "pass",
                "title": "Proteksi Anti-Clickjacking Aktif",
                "desc": f"Header X-Frame-Options: {val}. Mencegah situs dibingkai ke dalam iframe penipuan."
            })
        else:
            score -= 15
            headers_audit["x_frame_options"] = {"present": False, "value": None, "status": "FAIL", "label": "X-Frame-Options (Anti-Clickjacking)"}
            findings.append({
                "type": "warn",
                "title": "Proteksi X-Frame-Options Tidak Ditemukan",
                "desc": "Situs dapat disematkan ke dalam iframe situs lain dan rentan terhadap teknik penipuan clickjacking (UI redressing)."
            })
            recommendations.append("Tambahkan header X-Frame-Options: SAMEORIGIN atau DENY.")

        # Evaluate X-Content-Type-Options
        if "x-content-type-options" in h and "nosniff" in h["x-content-type-options"].lower():
            headers_audit["x_content_type"] = {"present": True, "value": "nosniff", "status": "PASS", "label": "X-Content-Type-Options"}
            findings.append({
                "type": "pass",
                "title": "Anti-MIME Sniffing Aktif",
                "desc": "Browser dilarang menebak tipe berkas selain yang dideklarasikan oleh server."
            })
        else:
            score -= 10
            headers_audit["x_content_type"] = {"present": False, "value": h.get("x-content-type-options"), "status": "FAIL", "label": "X-Content-Type-Options"}
            findings.append({
                "type": "info",
                "title": "Header X-Content-Type-Options Belum Ada",
                "desc": "Browser dapat salah mengartikan file non-eksekusi menjadi script jika MIME type tidak tepat."
            })
            recommendations.append("Tambahkan header X-Content-Type-Options: nosniff.")

        # Evaluate Referrer-Policy
        if "referrer-policy" in h:
            val = h["referrer-policy"]
            headers_audit["referrer_policy"] = {"present": True, "value": val, "status": "PASS", "label": "Referrer-Policy"}
            findings.append({
                "type": "pass",
                "title": "Referrer-Policy Dikonfigurasi",
                "desc": f"Kebijakan pengiriman referrer: {val}"
            })
        else:
            score -= 5
            headers_audit["referrer_policy"] = {"present": False, "value": None, "status": "FAIL", "label": "Referrer-Policy"}
            recommendations.append("Atur Referrer-Policy: strict-origin-when-cross-origin agar data URL sensitif tidak bocor ke domain luar.")

        # Evaluate Permissions-Policy
        if "permissions-policy" in h or "feature-policy" in h:
            val = h.get("permissions-policy") or h.get("feature-policy") or ""
            headers_audit["permissions_policy"] = {"present": True, "value": (val[:60] + '...') if len(val) > 60 else val, "status": "PASS", "label": "Permissions-Policy"}
        else:
            score -= 5
            headers_audit["permissions_policy"] = {"present": False, "value": None, "status": "FAIL", "label": "Permissions-Policy"}

        # Check server banner disclosure
        import re
        if any(char.isdigit() for char in server_banner) and not server_banner.startswith("Disembunyikan"):
            score -= 5
            findings.append({
                "type": "info",
                "title": "Informasi Versi Web Server Bocor",
                "desc": f"Server menampilkan detail versi: '{server_banner}'. Informasi ini dapat dimanfaatkan penyerang untuk mencari exploit CVE terkait."
            })
            recommendations.append("Sembunyikan banner versi server (misal 'server_tokens off;' pada Nginx).")

        score = max(0, min(100, score))
        if score >= 90:
            grade = "A+"
            verdict = "Keamanan Superior (Sangat Kuat)"
        elif score >= 80:
            grade = "A"
            verdict = "Keamanan Sangat Baik"
        elif score >= 70:
            grade = "B"
            verdict = "Keamanan Baik (Perlu Sedikit Optimasi)"
        elif score >= 55:
            grade = "C"
            verdict = "Keamanan Sedang (Proteksi Kritis Kurang)"
        elif score >= 40:
            grade = "D"
            verdict = "Rentan (Banyak Proteksi Header Hilang)"
        else:
            grade = "F"
            verdict = "Sangat Rentan / Tidak Aman"

        return {
            "target": target,
            "hostname": hostname,
            "resolved_ip": primary_ip,
            "all_ips": ip_list,
            "score": score,
            "grade": grade,
            "verdict": verdict,
            "ssl": ssl_info,
            "headers_audit": headers_audit,
            "server_info": {
                "status_code": status_code,
                "server_banner": server_banner
            },
            "findings": findings,
            "recommendations": recommendations
        }


def open_in_browser(url: str) -> bool:
    try:
        if webbrowser.open(url, new=2):
            return True
    except Exception:
        pass
    try:
        os_name = platform.system().lower()
        if os_name == "windows":
            startfile = getattr(os, "startfile", None)
            if startfile:
                startfile(url)
                return True
        if os_name == "darwin":
            subprocess.Popen(["open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        if os_name == "linux":
            cmd = shutil.which("xdg-open")
            if cmd:
                subprocess.Popen([cmd, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
    except Exception:
        pass
    return False


def handle_magic_link_verification(payload: Any) -> bool:
    if is_success_status(payload):
        UI.success("Verifikasi berhasil.")
        code = extract_order_code(payload)
        if code:
            UI.success_box("CODE ORDER", code)
        return True
    UI.error("Verifikasi gagal: " + extract_message(payload, "Verifikasi tidak dinyatakan berhasil oleh API."))
    return False


def sanitize_xvoid_text(text: str) -> str:
    """Sanitasi dan enforce identitas XVoid pada balasan AI."""
    if not text:
        return text
    
    # Replacement pola pengenalan diri spesifik
    text = re.sub(r"(?i)nama\s+(aku|saya)\s+strom[- ]?ai[^\.\n]*", "Nama saya XVoid, asisten AI eksklusif dari Project-XVOID", text)
    text = re.sub(r"(?i)asisten\s+ai\s+yang\s+dibuat\s+oleh\s+nightstrom\d*", "asisten AI dari Project-XVOID", text)
    text = re.sub(r"(?i)nightstrom\d*", "Project-XVOID", text)
    text = re.sub(r"(?i)strom[- ]?ai", "XVoid", text)
    text = re.sub(r"(?i)\bstrom\b", "XVoid", text)
    return text


def extract_ai_response_text(payload: Any) -> str:
    raw_text = ""
    if isinstance(payload, dict):
        for key in ("text", "content", "message", "response", "reply"):
            val = payload.get(key)
            if isinstance(val, str) and val.strip():
                raw_text = val.strip()
                break
    if not raw_text:
        raw_text = extract_message(payload, "AI tidak mengembalikan teks jawaban.")
    return sanitize_xvoid_text(raw_text)


def extract_session_id(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        val = payload.get("sessionId")
        if val not in (None, ""):
            return str(val)
    return None


def extract_page_html(payload: Any) -> Optional[str]:
    if isinstance(payload, dict) and isinstance(payload.get("html"), str):
        return payload["html"]
    return None


def show_page_source_stats(payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    page_info = payload.get("pageInfo")
    metrics = payload.get("metrics")
    server_info = payload.get("serverInfo")
    grid = Table(box=box.SIMPLE, border_style=Colors.MUTED, expand=True)
    grid.add_column("Property", style=f"bold {Colors.PRIMARY}")
    grid.add_column("Value", style=Colors.WHITE)
    if isinstance(page_info, dict):
        grid.add_row(
            "Page",
            f"{page_info.get('totalSize', '?')} · {page_info.get('totalChars', '?')} chars · {page_info.get('totalWords', '?')} words · {page_info.get('totalLines', '?')} lines",
        )
    if isinstance(metrics, dict):
        grid.add_row("Timing", f"{metrics.get('totalTime', '?')} ms")
    if isinstance(server_info, dict):
        grid.add_row(
            "Server",
            f"{server_info.get('server', '?')} · HTTP {server_info.get('httpVersion', '?')} · {server_info.get('httpCode', '?')}",
        )
    console.print(grid)


def save_html_to_file(html: str, url: str) -> Optional[str]:
    try:
        netloc = urlparse(url).netloc or "page"
        clean_netloc = re.sub(r"[^a-zA-Z0-9._-]+", "_", netloc)
        hash_suffix = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
        output = Path(f"source_{clean_netloc}_{hash_suffix}.html")
        output.write_text(html, encoding="utf-8")
        return str(output.resolve())
    except (OSError, ValueError):
        return None


def render_feature_screen(title: str, subtitle: str) -> None:
    UI.clear()
    UI.header(title, subtitle)


def print_typewriter(text: str, delay: float = 0.012) -> None:
    for char in text:
        console.print(char, end="")
        console.file.flush()
        time.sleep(delay)
    console.print()


def run_magic_link_flow(service: LeviathanService, version: str) -> bool:
    method_obj = V1 if version == "v1" else V2
    render_feature_screen("MAGIC LINK", method_obj.label)
    UI.section("EMAIL TARGET")
    email = prompt_validated("Gmail Target", is_valid_email, "Format email tidak valid.")
    try:
        with Spinner("Mengirim Magic Link Alight Motion Premium..."):
            res = service.send_magic_link(version, email)
    except ServiceError as exc:
        UI.error(f"Gagal mengirim magic link: {exc}")
        return False
    if version == "v1" and not is_success_status(res):
        UI.error(extract_message(res, "Pengiriman magic link gagal."))
        return False

    UI.success("Magic Link Premium berhasil dikirim ke Gmail!")
    console.print()
    console.print(
        Panel(
            Group(
                Text("PETUNJUK AKTIVASI INSTAN:", style=f"bold {Colors.SUCCESS}"),
                Text("1. Buka aplikasi Gmail di HP / perangkat Anda.", style=Colors.WHITE),
                Text("2. Buka pesan masuk dari Alight Motion / Alight Creative.", style=Colors.WHITE),
                Text("3. Langsung klik tautan / tombol 'Sign In' di email tersebut.", style=Colors.WHITE),
                Text("4. Aplikasi Alight Motion akan terbuka otomatis dan akun Anda langsung aktif sebagai Member Premium! 🎉", style=f"bold {Colors.WHITE}"),
            ),
            title="Aktivasi Berhasil",
            border_style=Colors.SUCCESS,
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
    console.print()
    manual_opt = UI.input("Ingin verifikasi manual untuk ambil Order Code? [y/N]").lower()
    if manual_opt not in ("y", "yes"):
        return True

    UI.section("VERIFIKASI MANUAL (ORDER CODE)")
    link = prompt_validated("Paste URL Magic Link dari email")
    try:
        with Spinner("Memverifikasi magic link..."):
            result = service.verify_magic_link(version, email, link)
    except ServiceError as exc:
        UI.error(f"Gagal saat verifikasi: {exc}")
        return False
    console.print()
    return handle_magic_link_verification(result)


def menu_magic_link(service: LeviathanService) -> bool:
    render_feature_screen("MAGIC LINK", "Alight Motion")
    UI.section("PILIH METODE")
    UI.menu_item("1", "V1", "GET · API lama")
    UI.menu_item("2", "V2", "POST · API baru")
    UI.menu_item("0", "KEMBALI", "Menu utama")
    choice = UI.input("Pilih")
    if choice == "1":
        return run_magic_link_flow(service, "v1")
    if choice == "2":
        return run_magic_link_flow(service, "v2")
    if choice == "0":
        return True
    UI.error("Pilihan tidak valid.")
    return False


def menu_web_to_apk(service: LeviathanService) -> bool:
    render_feature_screen("WEB TO APK", "Website Builder")
    UI.section("PROJECT")
    app_name = prompt_validated("Nama aplikasi")
    website_url = prompt_validated("URL website", is_valid_url, "URL harus http:// atau https://.")
    package_name = prompt_validated("Package name", is_valid_package_name, "Contoh: com.nama.aplikasi")
    version_name = prompt_validated("Version name")
    version_code = prompt_validated("Version code")
    icon_url = prompt_validated("URL icon", is_valid_url, "URL icon harus http:// atau https://.")
    render_feature_screen("WEB TO APK", "Membangun aplikasi")
    UI.section("DETAIL PROJECT")
    UI.label("App", app_name)
    UI.label("Website", website_url)
    UI.label("Package", package_name)
    UI.label("Version", f"{version_name} ({version_code})")
    try:
        with Spinner("Membuat build APK..."):
            result = service.create_web2apk(
                app_name, website_url, package_name, version_name, version_code, icon_url
            )
    except ServiceError as exc:
        UI.error(str(exc))
        return False
    build_id = extract_build_id(result)
    if not build_id:
        UI.error("Build ID tidak ditemukan.")
        return False
    UI.success(f"Build dibuat · ID: {build_id}")
    UI.info("Menunggu proses build selesai...")
    download_url = extract_download_url(result)
    progress_bar = Progress(
        SpinnerColumn(),
        TextColumn("[bold bright_cyan]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    )
    with progress_bar:
        task = progress_bar.add_task("Polling build", total=WEB2APK_POLL_LIMIT)
        for _ in range(WEB2APK_POLL_LIMIT):
            time.sleep(WEB2APK_POLL_INTERVAL)
            try:
                status_payload = service.web2apk_status(build_id)
            except ServiceError:
                progress_bar.update(task, advance=1)
                continue
            download_url = download_url or extract_download_url(status_payload)
            status = extract_status(status_payload)
            progress_bar.update(task, advance=1, description=f"Polling build · {status or 'processing'}")
            if download_url:
                break
            if status in {"failed", "error", "cancelled", "canceled"}:
                UI.error("Build APK gagal.")
                return False
    if not download_url:
        UI.error("Build belum selesai atau URL download tidak tersedia.")
        return False
    UI.success_box("APK SIAP", download_url)
    open_opt = UI.input("Buka link di browser? [y/N]").lower()
    if open_opt == "y":
        if open_in_browser(download_url):
            UI.success("Link dibuka di browser.")
        else:
            UI.warning("Browser tidak dapat dibuka otomatis. Salin link secara manual.")
    return True


def menu_xvoid_ai(service: LeviathanService) -> bool:
    render_feature_screen("XVOID AI", "Interactive Assistant")
    UI.section("SESSION")
    user_id = UI.input("User ID") or STROM_AI_USER_ID
    session_id: Optional[str] = None
    UI.section("CHAT")
    UI.info("/exit = kembali · /clear = reset session")
    while True:
        try:
            prompt = UI.input("You")
        except (EOFError, KeyboardInterrupt):
            console.print()
            UI.warning("Chat dibatalkan.")
            return True
        if not prompt:
            continue
        prompt_lower = prompt.lower()
        if prompt_lower in {"/exit", "/quit", "/q"}:
            return True
        if prompt_lower == "/clear":
            session_id = None
            UI.success("Session AI direset.")
            continue
        try:
            with Spinner("XVoid sedang berpikir..."):
                response_payload = service.ai_chat(prompt, session_id=session_id, user_id=user_id)
        except ServiceError as exc:
            UI.error(f"AI request gagal: {exc}")
            continue
        session_id = extract_session_id(response_payload) or session_id
        reply_text = extract_ai_response_text(response_payload)
        console.print()
        console.print(
            Panel(
                reply_text,
                title="XVoid ›",
                border_style=Colors.SUCCESS,
                box=box.ROUNDED,
                padding=(1, 2),
                expand=True,
            )
        )
        console.print()
        if DEBUG and session_id:
            UI.info(f"[DEBUG] sessionId: {session_id}")


def menu_cek_nomor(service: LeviathanService) -> bool:
    render_feature_screen("CEK NOMOR", "Kaspersky WhoCallsID Lookup")
    UI.section("INPUT")
    nomor = prompt_validated("Nomor Telepon (08xx / 628xx)")
    try:
        with Spinner("Mengecek informasi nomor telepon..."):
            result = service.cek_nomor(nomor)

        info = result.get("info") or {}
        similar = result.get("similar") or []
        normalized = result.get("nomor_normalized") or nomor

        UI.section("DETAIL NOMOR")
        tbl = Table(box=box.ROUNDED, border_style=Colors.PRIMARY, expand=True)
        tbl.add_column("Field", style=f"bold {Colors.PRIMARY}", width=22)
        tbl.add_column("Informasi", style=Colors.WHITE)

        tbl.add_row("Nomor Target", f"+{normalized}")
        
        op = info.get("operator")
        op_str = ", ".join(op) if isinstance(op, list) else str(op or "Tidak diketahui")
        tbl.add_row("Operator", op_str)

        tbl.add_row("Format Tampilan", str(info.get("display_format") or "-"))
        tbl.add_row("Kode Negara", f"+{info.get('international_code', 62)}")
        if info.get("region"):
            tbl.add_row("Region", str(info.get("region")))

        console.print(tbl)

        if isinstance(similar, list) and len(similar) > 0:
            UI.section("NOMOR SERUPA (SIMILAR NUMBERS)")
            sim_tbl = Table(box=box.SIMPLE_HEAVY, border_style=Colors.MUTED, expand=True)
            sim_tbl.add_column("#", width=4, justify="center", style=f"bold {Colors.PRIMARY}")
            sim_tbl.add_column("Nomor Lengkap", style=Colors.WHITE)
            sim_tbl.add_column("Format", style=Colors.MUTED)
            for idx, item in enumerate(similar, 1):
                c = item.get("international_code", 62)
                s_num = item.get("similar_number", "")
                fmt = item.get("display_format", "-")
                sim_tbl.add_row(str(idx), f"+{c}{s_num}", str(fmt))
            console.print(sim_tbl)

        return True
    except (ServiceError, requests.RequestException, OSError) as exc:
        UI.error(f"Gagal cek nomor: {exc}")
        return False


def menu_buat_gambar(service: LeviathanService) -> bool:
    render_feature_screen("BUAT GAMBAR AI", "AI Image Generator")
    UI.section("INPUT PROMPT")
    prompt = prompt_validated("Deskripsi Gambar (Prompt)")
    negative = UI.input("Negative Prompt (Opsional)")
    
    UI.section("PILIH ASPECT RATIO")
    UI.menu_item("1", "1:1", "Square (1024x1024)")
    UI.menu_item("2", "16:9", "Landscape (1280x720)")
    UI.menu_item("3", "9:16", "Portrait (720x1280)")
    ratio_choice = UI.input("Pilih [1]") or "1"
    ratio_map = {"1": "1:1", "2": "16:9", "3": "9:16"}
    aspect_ratio = ratio_map.get(ratio_choice, "1:1")

    UI.section("PILIH MODEL")
    UI.menu_item("1", "SDXL", "Stable Diffusion XL")
    UI.menu_item("2", "Flux", "Flux Schnell / Dev")
    model_choice = UI.input("Pilih [1]") or "1"
    model_map = {"1": "sdxl", "2": "flux"}
    model = model_map.get(model_choice, "sdxl")

    try:
        with Spinner("Men-generate gambar dengan AI..."):
            result = service.buat_gambar(prompt, model=model, aspect_ratio=aspect_ratio, negative_prompt=negative)

        b64_data = result.get("b64_json") or result.get("image")
        img_url = result.get("url") or result.get("image_url")
        provider = result.get("provider", "free.ai")

        out_name = f"gambar_ai_{int(time.time())}.png"
        out_path = Path(out_name)

        if b64_data:
            out_path.write_bytes(base64.b64decode(b64_data))
            UI.success(f"Gambar berhasil disimpan: {out_path.resolve()}")
            UI.label("Provider", provider)
            UI.label("Aspect Ratio", aspect_ratio)
            UI.label("Model", model)
            return True
        elif img_url:
            with Spinner("Mengunduh gambar dari URL..."):
                img_res = service.http.session.get(img_url, timeout=DOWNLOAD_TIMEOUT)
                if img_res.ok:
                    out_path.write_bytes(img_res.content)
                    UI.success(f"Gambar berhasil disimpan: {out_path.resolve()}")
                    UI.label("Provider", provider)
                    return True
        UI.error("Tidak ada file gambar yang dapat disimpan.")
        return False
    except (ServiceError, requests.RequestException, OSError) as exc:
        UI.error(f"Gagal generate gambar: {exc}")
        return False


def menu_scan_repo(service: LeviathanService) -> bool:
    render_feature_screen("SCAN GITHUB REPO", "Security & Vulnerability Scanner")
    UI.section("INPUT")
    repo_url = prompt_validated("URL GitHub Repo (https://github.com/user/repo)")
    try:
        with Spinner("Menganalisis repositori GitHub..."):
            result = service.scan_github_repo(repo_url)

        res_data = result.get("result") or {}
        meta = res_data.get("meta") or {}
        findings = res_data.get("findings") or []

        UI.section("HASIL SCANNING")
        tbl = Table(box=box.ROUNDED, border_style=Colors.PRIMARY, expand=True)
        tbl.add_column("Metrik", style=f"bold {Colors.PRIMARY}", width=20)
        tbl.add_column("Nilai", style=Colors.WHITE)

        tbl.add_row("Repository", str(meta.get("repo") or repo_url))
        tbl.add_row("Bahasa", str(meta.get("language") or "-"))
        tbl.add_row("Risk Score", str(res_data.get("riskScore", 0)))
        
        risk_lvl = str(res_data.get("riskLevel", "UNKNOWN")).upper()
        lvl_color = Colors.SUCCESS if risk_lvl in {"LOW", "SAFE"} else Colors.ERROR
        tbl.add_row("Risk Level", f"[{lvl_color}]{risk_lvl}[/{lvl_color}]")
        tbl.add_row("Jumlah Temuan", f"{len(findings)} temuan")
        console.print(tbl)

        if findings:
            UI.section("TEMUAN KERENTANAN (FINDINGS)")
            f_tbl = Table(box=box.SIMPLE_HEAVY, border_style=Colors.MUTED, expand=True)
            f_tbl.add_column("#", width=3, justify="center")
            f_tbl.add_column("Severity", width=10)
            f_tbl.add_column("Judul / Kerentanan", width=32)
            f_tbl.add_column("File Path")

            for idx, item in enumerate(findings[:10], 1):
                sev = str(item.get("severity", "info")).upper()
                sev_style = Colors.ERROR if "HIGH" in sev or "CRIT" in sev else (Colors.WARNING if "MED" in sev else Colors.SUCCESS)
                f_tbl.add_row(
                    str(idx),
                    f"[{sev_style}]{sev}[/{sev_style}]",
                    str(item.get("title", "-")),
                    str(item.get("filePath") or "-")[:45],
                )
            console.print(f_tbl)
            if len(findings) > 10:
                UI.info(f"... dan {len(findings) - 10} temuan lainnya.")

        return True
    except (ServiceError, requests.RequestException, OSError) as exc:
        UI.error(f"Gagal scan repositori: {exc}")
        return False


def menu_page_source(service: LeviathanService) -> bool:
    render_feature_screen("PAGE SOURCE", "View Page Source")
    UI.section("INPUT")
    url = prompt_validated("URL website", is_valid_url, "URL harus http:// atau https://.")
    render_feature_screen("PAGE SOURCE", "Mengambil source")
    UI.label("URL", url)
    try:
        with Spinner("Mengambil token dan page source..."):
            result = service.fetch_page_source(url, stylize=True)
    except ServiceError as exc:
        UI.error(f"Gagal mengambil source: {exc}")
        return False
    html = extract_page_html(result)
    if html is None:
        UI.error("Response tidak berisi field 'html'.")
        if DEBUG:
            console.print(result)
        return False
    UI.success("Page source berhasil diambil.")
    UI.section("STATISTIK")
    show_page_source_stats(result)
    try:
        save_opt = UI.input("Simpan HTML ke file? [Y/n]").lower()
    except (EOFError, KeyboardInterrupt):
        console.print()
        return True
    if save_opt in ("", "y", "yes"):
        saved_file = save_html_to_file(html, url)
        if saved_file:
            UI.success(f"HTML disimpan: {saved_file}")
            return True
        UI.error("Gagal menyimpan HTML ke file.")
        return False
    UI.section("PREVIEW")
    preview = html[:5000]
    console.print(Panel(preview, border_style=Colors.MUTED, box=box.ROUNDED, padding=(1, 2)))
    if len(html) > 5000:
        UI.info(f"... {len(html) - 5000} karakter lainnya tidak ditampilkan.")
    return True


def menu_web_to_zip(service: LeviathanService) -> bool:
    render_feature_screen("WEB TO ZIP", "Website Packager")
    UI.section("INPUT")
    url = prompt_validated("URL website", is_valid_url, "URL harus http:// atau https://.")
    try:
        with Spinner("Mengonversi website ke ZIP..."):
            payload, download_url = service.web_to_zip(url)
        default_file_name = str(payload.get("FileName", "website.zip"))
        UI.success("Konversi selesai.")
        UI.label("File", default_file_name)
        UI.label("Status", str(payload.get("Status", "Complete")))
        out_name = UI.input(f"Nama output [{default_file_name}]")
        final_out_name = out_name or default_file_name
        if not final_out_name.lower().endswith(".zip"):
            final_out_name += ".zip"
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold bright_cyan]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Mengunduh ZIP...", total=None)
            response = service.http.session.get(
                download_url,
                headers={"Accept": "application/zip,*/*", "Referer": ASPOSE_REFERER},
                timeout=DOWNLOAD_TIMEOUT,
            )
            response.raise_for_status()
            data = response.content
            progress.update(task, completed=len(data), total=len(data))
        content_type = response.headers.get("content-type", "")
        if "zip" not in content_type.lower() and not data.startswith(b"PK"):
            raise ServiceError(f"Response download bukan ZIP. Content-Type: {content_type or 'unknown'}")
        output = Path(final_out_name)
        output.write_bytes(data)
        UI.success(f"ZIP tersimpan: {output.resolve()}")
        UI.info(f"Ukuran: {len(data):,} bytes")
        return True
    except (ServiceError, requests.RequestException, OSError) as exc:
        UI.error(f"Web to ZIP gagal: {exc}")
        return False


def menu_tiktok_downloader(service: LeviathanService) -> bool:
    render_feature_screen("TIKTOK DOWNLOADER", "Public Media Downloader")
    UI.section("INPUT")
    url = prompt_validated("URL TikTok", is_valid_tiktok_url, "Masukkan URL TikTok yang valid.")
    try:
        with Spinner("Memproses link TikTok..."):
            media_info = service.tiktok_info(url)
        UI.section("VIDEO INFO")
        tbl = Table(box=box.SIMPLE, border_style=Colors.MUTED, expand=True)
        tbl.add_column("Field", style=f"bold {Colors.PRIMARY}")
        tbl.add_column("Value", style=Colors.WHITE)
        fields = (
            ("author", "Author"),
            ("caption", "Caption"),
            ("like_count", "Likes"),
            ("play_count", "Views"),
        )
        for k, label in fields:
            if media_info.get(k):
                val = media_info[k]
                if k == "caption":
                    val = val[:180]
                tbl.add_row(label, val)
        console.print(tbl)
        formats: list[tuple[str, str, str, str]] = []
        if media_info.get("video_url"):
            formats.append(("1", "MP4", media_info["video_url"], ".mp4"))
        if media_info.get("video_hd_url"):
            formats.append(("2", "MP4 HD", media_info["video_hd_url"], ".mp4"))
        if media_info.get("mp3_url"):
            formats.append(("3", "MP3", media_info["mp3_url"], ".mp3"))
        UI.section("FORMAT")
        for num, label, _, _ in formats:
            UI.menu_item(num, label)
        choice = UI.input("Pilih format [1]") or "1"
        selected = next((item for item in formats if item[0] == choice), None)
        if not selected:
            UI.error("Pilihan format tidak valid.")
            return False
        _, label, download_url, ext = selected
        default_name = f"tiktok_{int(time.time())}{ext}"
        user_filename = UI.input(f"Nama output [{default_name}]")
        final_filename = user_filename or default_name
        if not final_filename.lower().endswith(ext):
            final_filename += ext
        out_path = Path(final_filename)
        downloaded_bytes = service.download_media(download_url, out_path)
        UI.success(f"{label} tersimpan: {out_path.resolve()}")
        UI.info(f"Ukuran: {downloaded_bytes:,} bytes")
        return True
    except (ServiceError, requests.RequestException, OSError) as exc:
        UI.error(f"TikTok download gagal: {exc}")
        return False


def menu_base64_encode(service: LeviathanService) -> bool:
    render_feature_screen("BASE64 TOOLS", "File → Base64")
    UI.section("INPUT")
    file_path = prompt_validated("File path")
    path = Path(file_path).expanduser()
    try:
        with Spinner("Membaca dan encode file..."):
            encoded_str, mime_type, file_size = service.encode_file_base64(path)
    except ServiceError as exc:
        UI.error(str(exc))
        return False
    UI.success("File berhasil di-encode.")
    UI.label("File", str(path))
    UI.label("MIME", mime_type)
    UI.label("Size", f"{file_size:,} bytes")
    UI.label("Base64", f"{len(encoded_str):,} chars")
    UI.section("OUTPUT")
    default_out = f"{path.name}.base64.txt"
    output = UI.input(f"Output file [{default_out}]") or default_out
    try:
        out_file = Path(output).expanduser()
        out_file.write_text(encoded_str, encoding="ascii")
    except OSError as exc:
        UI.error(f"Gagal menyimpan Base64: {exc}")
        return False
    UI.success(f"Base64 disimpan: {out_file.resolve()}")
    if mime_type.startswith("image/"):
        try:
            data_uri = service.make_data_uri(encoded_str, mime_type)
            data_uri_file = out_file.with_name(out_file.stem + ".datauri.txt")
            data_uri_file.write_text(data_uri, encoding="ascii")
            UI.success(f"Data URI disimpan: {data_uri_file.resolve()}")
        except OSError as exc:
            UI.warning(f"Data URI tidak dapat disimpan: {exc}")
    preview = encoded_str[:120]
    UI.label("Preview", preview + ("..." if len(encoded_str) > 120 else ""))
    return True


def menu_base64_decode(service: LeviathanService) -> bool:
    render_feature_screen("BASE64 TOOLS", "Base64 → File")
    UI.section("INPUT")
    source = prompt_validated("Base64 file")
    path = Path(source).expanduser()
    if not path.is_file():
        UI.error(f"File Base64 tidak ditemukan: {path}")
        return False
    try:
        raw_text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        UI.error(f"Gagal membaca file Base64: {exc}")
        return False
    default_output = "decoded.bin"
    stripped = raw_text.lstrip()
    if stripped.lower().startswith("data:image/"):
        header_part = stripped.split(",", 1)[0].lower()
        if "image/jpeg" in header_part:
            default_output = "decoded.jpg"
        elif "image/png" in header_part:
            default_output = "decoded.png"
        elif "image/webp" in header_part:
            default_output = "decoded.webp"
        elif "image/gif" in header_part:
            default_output = "decoded.gif"
    output = UI.input(f"Output file [{default_output}]") or default_output
    try:
        with Spinner("Decode Base64..."):
            written_bytes = service.decode_base64_to_file(raw_text, output)
    except ServiceError as exc:
        UI.error(str(exc))
        return False
    UI.success(f"File berhasil dibuat: {Path(output).resolve()}")
    UI.info(f"Ukuran hasil: {written_bytes:,} bytes")
    return True


def menu_base64(service: LeviathanService) -> bool:
    while True:
        render_feature_screen("BASE64 TOOLS", "Encode / Decode")
        UI.section("FITUR")
        UI.menu_item("1", "ENCODE FILE", "File → Base64")
        UI.menu_item("2", "DECODE FILE", "Base64 → File")
        UI.menu_item("0", "KEMBALI", "Menu utama")
        choice = UI.input("Pilih")
        if choice == "1":
            return menu_base64_encode(service)
        if choice == "2":
            return menu_base64_decode(service)
        if choice == "0":
            return True
        UI.error("Pilihan tidak valid.")
        time.sleep(0.6)


def menu_web_tools(service: LeviathanService) -> bool:
    while True:
        render_feature_screen("WEB TOOLS", "Web Automation")
        UI.section("FITUR")
        UI.menu_item("1", "WEB TO APK", "Build website menjadi APK")
        UI.menu_item("2", "PAGE SOURCE", "Ambil HTML/source halaman")
        UI.menu_item("3", "WEB TO ZIP", "Pack website menjadi ZIP")
        UI.menu_item("0", "KEMBALI", "Menu utama")
        choice = UI.input("Pilih")
        if choice == "1":
            return menu_web_to_apk(service)
        if choice == "2":
            return menu_page_source(service)
        if choice == "3":
            return menu_web_to_zip(service)
        if choice == "0":
            return True
        UI.error("Pilihan tidak valid.")
        time.sleep(0.6)


def menu_ai_tools(service: LeviathanService) -> bool:
    return menu_xvoid_ai(service)


def menu_downloader(service: LeviathanService) -> bool:
    return menu_tiktok_downloader(service)


@dataclass(frozen=True)
class MenuEntry:
    title: str
    description: str
    handler: Callable[[LeviathanService], bool]


MAIN_MENU = {
    "1": MenuEntry("TOOLS", "Encode / Decode file", menu_base64),
    "2": MenuEntry("MAGIC LINK", "Alight Motion V1 / V2", menu_magic_link),
    "3": MenuEntry("WEB TOOLS", "Web TO APK / Source / ZIP", menu_web_tools),
    "4": MenuEntry("XVOID AI", "Interactive AI Assistant", menu_ai_tools),
    "5": MenuEntry("DOWNLOADER", "TikTok public media", menu_downloader),
    "6": MenuEntry("CEK NOMOR", "Kaspersky WhoCallsID lookup", menu_cek_nomor),
    "7": MenuEntry("BUAT GAMBAR", "AI Image Generator", menu_buat_gambar),
    "8": MenuEntry("SCAN REPO", "GitHub Security & code audit", menu_scan_repo),
}


def render_main_menu() -> Optional[str]:
    render_feature_screen("PROJECT-XVOID", f"Toolkit v{APP_VERSION}")
    if LICENSE.is_expired():
        raise LicenseExpiredError(f"License {LICENSE_NAME} expired pada {LICENSE.formatted_expiry()}")
    UI.section("CATEGORY MENU")
    grid = Table(box=box.ROUNDED, border_style=Colors.MUTED, expand=True, padding=(0, 1))
    grid.add_column("#", width=5, justify="center", style=f"bold {Colors.PRIMARY}")
    grid.add_column("Tool", width=22, style=f"bold {Colors.WHITE}")
    grid.add_column("Description", style=Colors.MUTED)
    for k, entry in MAIN_MENU.items():
        grid.add_row(k, entry.title, entry.description)
    grid.add_row("0", "EXIT", "Tutup aplikasi")
    console.print(grid)
    console.print()
    LICENSE.show_status()
    console.print()
    return UI.input("Pilih kategori")


def render_license_expired_screen() -> None:
    UI.clear()
    console.print(
        Panel(
            Group(
                Align.center(Text("LICENSE EXPIRED", style=f"bold {Colors.ERROR}")),
                Align.center(Text("Akses ke seluruh tools telah dinonaktifkan.", style=Colors.WHITE)),
                Align.center(Text(LICENSE.formatted_expiry(), style=Colors.MUTED)),
            ),
            title=APP_NAME,
            title_align="center",
            border_style=Colors.ERROR,
            box=box.DOUBLE,
            padding=(2, 4),
            expand=True,
        )
    )


def main() -> None:
    show_startup_animation()
    try:
        LICENSE.require_valid()
    except LicenseExpiredError:
        render_license_expired_screen()
        return

    service = LeviathanService()
    while True:
        try:
            LICENSE.require_valid()
        except LicenseExpiredError:
            render_license_expired_screen()
            return
        try:
            choice = render_main_menu()
        except LicenseExpiredError:
            render_license_expired_screen()
            return
        except (EOFError, KeyboardInterrupt):
            console.print()
            UI.warning("Dibatalkan oleh pengguna.")
            return

        if not choice:
            continue

        if choice == "0":
            UI.clear()
            UI.header("PROJECT-XVOID", "Session closed")
            UI.success("Program ditutup.")
            return

        menu_entry = MAIN_MENU.get(choice)
        if menu_entry is None:
            UI.error("Pilihan kategori tidak valid.")
            time.sleep(0.7)
            continue

        try:
            LICENSE.require_valid()
        except LicenseExpiredError:
            render_license_expired_screen()
            return

        try:
            success = menu_entry.handler(service)
        except LicenseExpiredError:
            render_license_expired_screen()
            return
        except KeyboardInterrupt:
            console.print()
            UI.warning("Operasi dibatalkan.")
            success = False
        except Exception as exc:
            UI.error(f"Unexpected error: {exc}")
            if DEBUG:
                raise
            success = False

        try:
            LICENSE.require_valid()
        except LicenseExpiredError:
            render_license_expired_screen()
            return

        console.print()
        if success:
            UI.success_box("DONE", "Operation completed successfully.")
        else:
            UI.warning("Operation incomplete.")

        try:
            back_choice = UI.input("Kembali ke menu utama? [Y/n]").lower()
        except (EOFError, KeyboardInterrupt):
            return

        if back_choice not in ("", "y", "yes"):
            UI.clear()
            UI.header("PROJECT-XVOID", "Session closed")
            UI.info("Program ditutup.")
            return



if __name__ == "__main__":
    try:
        main()
    except LicenseExpiredError:
        render_license_expired_screen()
    except KeyboardInterrupt:
        console.print("\n[bright_yellow]Dibatalkan oleh pengguna.[/bright_yellow]")
        sys.exit(0)
    except Exception as exc:
        console.print(
            Panel(
                str(exc),
                title="Fatal Error",
                border_style=Colors.ERROR,
                box=box.DOUBLE,
            )
        )
        if DEBUG:
            raise
        sys.exit(1)