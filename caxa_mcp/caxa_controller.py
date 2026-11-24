"""
CAXA Controller for CAXA MCP
Handles CAXA CAD process lifecycle, window discovery, window activation,
file opening, command line / keyboard input simulation, and screen capture.
"""

import csv
import os
import shutil
import subprocess
import time
import winreg
from contextlib import contextmanager
from typing import Any, Dict, Optional

import win32api
import win32con
import win32event
import win32gui
import win32process
from PIL import Image, ImageGrab
from pywintypes import error as WindowsError


_OPEN_DIALOG_TITLES = {"打开", "打开文件", "open", "open file"}
_FILENAME_EDIT_ID = 1148
_POLL_INTERVAL = 0.15
_WINDOW_MUTEX = r"Local\CAXA-MCP-Window"


@contextmanager
def _desktop_operation():
    """Serialize CAXA window operations across clients in this Windows session."""
    handle = win32event.CreateMutex(None, False, _WINDOW_MUTEX)
    try:
        state = win32event.WaitForSingleObject(handle, 45000)
        if state not in (win32event.WAIT_OBJECT_0, win32event.WAIT_ABANDONED):
            raise TimeoutError("CAXA is busy in another MCP client. Retry when its window operation finishes.")
        try:
            yield
        finally:
            win32event.ReleaseMutex(handle)
    finally:
        handle.Close()


class CAXAController:
    """Controls CAXA CAD on Windows."""

    DEFAULT_PATHS = [
        r"E:\CAXA\caxa\2023\Bin64\CDRAFT_M.exe",
        r"C:\CAXA\caxa\2023\Bin64\CDRAFT_M.exe",
        r"D:\CAXA\caxa\2023\Bin64\CDRAFT_M.exe",
    ]

    def __init__(self, caxa_path: Optional[str] = None):
        self.caxa_path = self._resolve_caxa_path(caxa_path)

    def _resolve_caxa_path(self, override_path: Optional[str]) -> str:
        """Resolve the executable path of CAXA 电子图板."""
        if override_path and os.path.isfile(override_path):
            return os.path.abspath(override_path)

        env_path = os.environ.get("CAXA_PATH")
        if env_path and os.path.isfile(env_path):
            return os.path.abspath(env_path)

        executable = shutil.which("CDRAFT_M.exe")
        if executable:
            return os.path.abspath(executable)

        app_key = r"Software\Microsoft\Windows\CurrentVersion\App Paths\CDRAFT_M.exe"
        for hkey in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(hkey, app_key) as key:
                    registered, _ = winreg.QueryValueEx(key, None)
                registered = os.path.expandvars(registered.strip('"'))
                if os.path.isfile(registered):
                    return os.path.abspath(registered)
            except OSError:
                pass

        # Check default paths
        for path in self.DEFAULT_PATHS:
            if os.path.isfile(path):
                return os.path.abspath(path)

        # Check Windows registry
        for hkey in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            try:
                k = winreg.OpenKey(hkey, r"Software\CAXA\CAXA CAD\23.0")
                install_dir, _ = winreg.QueryValueEx(k, "InstallDir")
                winreg.CloseKey(k)
                candidate = os.path.join(install_dir, "Bin64", "CDRAFT_M.exe")
                if os.path.isfile(candidate):
                    return os.path.abspath(candidate)
            except Exception:
                pass

        # Fallback to first default path
        return self.DEFAULT_PATHS[0]

    def get_caxa_pids(self) -> list[int]:
        """Get Windows process IDs for the configured CAXA executable."""
        executable = os.path.basename(self.caxa_path)
        try:
            output = subprocess.check_output(
                ["tasklist", "/FI", f"IMAGENAME eq {executable}", "/FO", "CSV", "/NH"],
                text=True, errors="replace", timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except (OSError, subprocess.SubprocessError):
            return []
        return [
            int(row[1])
            for row in csv.reader(output.splitlines())
            if len(row) > 1 and row[0].casefold() == executable.casefold() and row[1].isdigit()
        ]

    def is_running(self) -> bool:
        return bool(self.get_caxa_pids())

    def find_main_window(self, pids: Optional[list[int]] = None) -> Optional[int]:
        process_ids = set(self.get_caxa_pids() if pids is None else pids)
        windows = []

        def collect(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and not win32gui.GetWindow(hwnd, win32con.GW_OWNER):
                if win32process.GetWindowThreadProcessId(hwnd)[1] in process_ids:
                    title = win32gui.GetWindowText(hwnd)
                    if "caxa" in title.lower() or "电子图板" in title:
                        windows.append(hwnd)
            return True

        if process_ids:
            win32gui.EnumWindows(collect, None)
        foreground = win32gui.GetForegroundWindow()
        return foreground if foreground in windows else next(iter(windows), None)

    def get_status(self, hwnd: Optional[int] = None) -> Dict[str, Any]:
        pids = self.get_caxa_pids()
        hwnd = hwnd if hwnd and win32gui.IsWindow(hwnd) else self.find_main_window(pids)
        return {
            "caxa_path": self.caxa_path,
            "installed": os.path.isfile(self.caxa_path),
            "is_running": bool(pids),
            "pids": pids,
            "main_hwnd": hex(hwnd) if hwnd else None,
            "window_title": win32gui.GetWindowText(hwnd) if hwnd else "",
        }

    def _activate(self, hwnd: int) -> bool:
        if not win32gui.IsWindowEnabled(hwnd):
            return False
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            if win32gui.GetForegroundWindow() != hwnd:
                win32gui.SetForegroundWindow(hwnd)
        except WindowsError:
            return False
        return win32gui.GetForegroundWindow() == hwnd

    def activate_window(self) -> bool:
        with _desktop_operation():
            hwnd = self.find_main_window()
            return bool(hwnd and self._activate(hwnd))

    @staticmethod
    def _wait_for(check, seconds: float):
        deadline = time.monotonic() + max(0, seconds)
        while True:
            result = check()
            if result or time.monotonic() >= deadline:
                return result
            time.sleep(_POLL_INTERVAL)

    def _start(self, *args: str):
        if not os.path.isfile(self.caxa_path):
            raise FileNotFoundError(f"CAXA executable not found at: {self.caxa_path}")
        return subprocess.Popen(
            [self.caxa_path, *args],
            cwd=os.path.dirname(self.caxa_path),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def launch(self, wait_seconds: float = 10.0) -> Dict[str, Any]:
        with _desktop_operation():
            pids = self.get_caxa_pids()
            if not pids:
                pids = [self._start().pid]
            hwnd = self._wait_for(lambda: self.find_main_window(pids), wait_seconds)
            if hwnd:
                self._activate(hwnd)
            return self.get_status(hwnd)

    @staticmethod
    def _document_name(title: str) -> str:
        # CAXA may show a full path or only the filename in the last brackets.
        _, marker, name = title.partition(" - [")
        return name.rsplit("]", 1)[0] if marker and "]" in name else ""

    @staticmethod
    def _matches_path(name: str, path: str, accept_basename: bool = False) -> bool:
        if not name:
            return False
        if accept_basename and name == os.path.basename(name):
            return os.path.normcase(name) == os.path.normcase(os.path.basename(path))
        return os.path.isabs(name) and os.path.normcase(os.path.normpath(name)) == os.path.normcase(path)

    @staticmethod
    def _owned_dialog(hwnd: int) -> Optional[int]:
        dialogs = []

        def collect(candidate, _):
            if (win32gui.IsWindowVisible(candidate)
                    and win32gui.GetWindow(candidate, win32con.GW_OWNER) == hwnd
                    and win32gui.GetClassName(candidate) == "#32770"):
                dialogs.append(candidate)
            return True

        win32gui.EnumWindows(collect, None)
        return next(iter(dialogs), None)

    @staticmethod
    def _open_dialog_edit(dialog: int) -> Optional[int]:
        edits = []

        def collect(child, _):
            if (win32gui.GetClassName(child) == "Edit" and win32gui.IsWindowVisible(child)
                    and win32gui.GetDlgCtrlID(child) == _FILENAME_EDIT_ID):
                edits.append(child)
            return True

        win32gui.EnumChildWindows(dialog, collect, None)
        return edits[0] if len(edits) == 1 else None

    @staticmethod
    def _key(vk: int, *, up: bool = False):
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP if up else 0, 0)

    def _hotkey(self, key: int, modifiers=()):
        for modifier in modifiers:
            self._key(modifier)
        try:
            self._key(key)
            self._key(key, up=True)
        finally:
            for modifier in reversed(modifiers):
                self._key(modifier, up=True)

    def _submit_open_dialog(self, hwnd: int, path: str, wait_seconds: float) -> Optional[str]:
        if self._owned_dialog(hwnd) or not self._activate(hwnd):
            return "CAXA is not ready for input. Close any open dialog and activate CAXA."
        self._hotkey(ord("O"), (win32con.VK_CONTROL,))
        dialog = self._wait_for(lambda: self._owned_dialog(hwnd), min(wait_seconds, 4))
        if not dialog or win32gui.GetWindowText(dialog).casefold() not in _OPEN_DIALOG_TITLES:
            return "The CAXA Open dialog could not be confirmed."
        edit = self._open_dialog_edit(dialog)
        if not edit:
            return "The filename field in the CAXA Open dialog could not be located."
        _, accepted = win32gui.SendMessageTimeout(
            edit, win32con.WM_SETTEXT, 0, path, win32con.SMTO_ABORTIFHUNG, 1000,
        )
        if not accepted:
            return "CAXA did not accept the drawing path."
        ok_button = win32gui.GetDlgItem(dialog, win32con.IDOK)
        win32gui.PostMessage(dialog, win32con.WM_COMMAND, win32con.IDOK, ok_button)
        return None

    def open_drawing(self, file_path: str, wait_seconds: float = 12.0) -> Dict[str, Any]:
        """Open a drawing in the current CAXA instance and confirm the document title."""
        path = os.path.abspath(file_path)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Drawing file not found: {path}")

        with _desktop_operation():
            pids = self.get_caxa_pids()
            hwnd = self.find_main_window(pids)
            reused = bool(pids)

            def result(success: bool, error: Optional[str] = None):
                return {
                    "success": success,
                    "requested_file": path,
                    "opened_file": path if success else None,
                    "reused_instance": reused,
                    "status": self.get_status(hwnd),
                    **({"error": error} if error else {}),
                }

            try:
                if reused:
                    if not hwnd:
                        hwnd = self._wait_for(lambda: self.find_main_window(pids), wait_seconds)
                    if not hwnd:
                        return result(False, "CAXA is running but its main window is not available.")
                    previous = self._document_name(win32gui.GetWindowText(hwnd))
                    if not self._owned_dialog(hwnd) and self._matches_path(previous, path):
                        return result(True)
                    error = self._submit_open_dialog(hwnd, path, wait_seconds)
                    if error:
                        return result(False, error)
                else:
                    previous = ""
                    pids = [self._start(path).pid]

                def loaded():
                    candidate = hwnd or self.find_main_window(pids)
                    if candidate and not self._owned_dialog(candidate) and win32gui.IsWindowEnabled(candidate):
                        name = self._document_name(win32gui.GetWindowText(candidate))
                        if self._matches_path(name, path, accept_basename=name != previous):
                            return candidate
                    return None

                # The frame title can change before a DXF finishes importing.
                ready = self._wait_for(loaded, wait_seconds)
                if ready:
                    hwnd = ready
                    time.sleep(0.6)
                    if loaded():
                        return result(True)
                return result(False, "CAXA did not confirm the target drawing. Check for an import dialog or retry.")
            except WindowsError as exc:
                return result(False, f"Windows could not open the drawing in CAXA: {exc}")

    def _send_command(self, hwnd: int, command: str, press_enter: bool) -> bool:
        for char in command:
            if win32gui.GetForegroundWindow() != hwnd:
                return False
            code = win32api.VkKeyScan(char)
            if code == -1:
                return False
            modifiers = tuple(
                key for bit, key in enumerate((win32con.VK_SHIFT, win32con.VK_CONTROL, win32con.VK_MENU))
                if (code >> 8) & (1 << bit)
            )
            self._hotkey(code & 0xff, modifiers)
            time.sleep(0.02)
        if win32gui.GetForegroundWindow() != hwnd:
            return False
        if press_enter:
            self._hotkey(win32con.VK_RETURN)
        return True

    def send_command(self, command_str: str, press_enter: bool = True) -> bool:
        """Send a command only while the CAXA main window owns the foreground."""
        with _desktop_operation():
            hwnd = self.find_main_window()
            if not hwnd or not self._activate(hwnd):
                return False
            self._hotkey(win32con.VK_ESCAPE)
            return self._send_command(hwnd, command_str, press_enter)

    def zoom_extents(self, hwnd: Optional[int] = None) -> bool:
        """Send the Z and E shortcut sequence without cancelling it halfway."""
        with _desktop_operation():
            hwnd = hwnd or self.find_main_window()
            if not hwnd or not self._activate(hwnd):
                return False
            if not self._send_command(hwnd, "Z", True):
                return False
            time.sleep(0.2)
            return self._send_command(hwnd, "E", True)

    def capture_window(self) -> Optional[Image.Image]:
        """Capture only a confirmed CAXA window at its native resolution."""
        with _desktop_operation():
            hwnd = self.find_main_window()
            if not hwnd or self._owned_dialog(hwnd) or not self._activate(hwnd):
                return None
            try:
                image = ImageGrab.grab(window=hwnd)
                if (win32gui.GetForegroundWindow() != hwnd
                        or all(low == high for low, high in image.getextrema())):
                    return None
                return image
            except (OSError, ValueError, WindowsError):
                return None

    def capture_screenshot(self, output_path: str) -> Optional[str]:
        image = self.capture_window()
        if image is None:
            return None
        path = os.path.abspath(output_path)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            image.save(path)
        except (OSError, ValueError):
            return None
        return path
