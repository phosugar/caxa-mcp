"""
CAXA Controller for CAXA MCP
Handles CAXA CAD process lifecycle, window discovery, window activation,
file opening, command line / keyboard input simulation, and screen capture.
"""

import os
import sys
import time
import subprocess
import ctypes
from ctypes import wintypes
from typing import Optional, Dict, Any, Tuple
import winreg

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


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

    def get_caxa_pids(self) -> list:
        """Get all running PIDs for CDRAFT_M.exe."""
        pids = []
        try:
            cmd = 'tasklist /FI "IMAGENAME eq CDRAFT_M.exe" /FO CSV /NH'
            out = subprocess.check_output(cmd, shell=True, text=True, errors="ignore")
            for line in out.strip().splitlines():
                parts = line.split('","')
                if len(parts) >= 2:
                    pid_str = parts[1].replace('"', '').strip()
                    if pid_str.isdigit():
                        pids.append(int(pid_str))
        except Exception:
            pass
        return pids

    def is_running(self) -> bool:
        """Check if CAXA CAD is currently running."""
        return len(self.get_caxa_pids()) > 0

    def find_main_window(self) -> Optional[int]:
        """Find the main HWND of the CAXA window."""
        caxa_pids = set(self.get_caxa_pids())
        found_hwnds = []

        def enum_proc(hwnd, lparam):
            if user32.IsWindowVisible(hwnd):
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value in caxa_pids or not caxa_pids:
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        title = buff.value
                        if "caxa" in title.lower() or "电子图板" in title:
                            found_hwnds.append((hwnd, title))
            return True

        user32.EnumWindows(WNDENUMPROC(enum_proc), 0)

        if found_hwnds:
            # Prefer window with document or main CAXA title
            return found_hwnds[0][0]

        return None

    def get_status(self) -> Dict[str, Any]:
        """Return the current status of CAXA."""
        running = self.is_running()
        hwnd = self.find_main_window() if running else None
        title = ""
        if hwnd:
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value

        return {
            "caxa_path": self.caxa_path,
            "installed": os.path.isfile(self.caxa_path),
            "is_running": running,
            "pids": self.get_caxa_pids(),
            "main_hwnd": hex(hwnd) if hwnd else None,
            "window_title": title,
        }

    def activate_window(self) -> bool:
        """Bring CAXA window to the foreground."""
        hwnd = self.find_main_window()
        if not hwnd:
            return False

        # Restore if minimized
        SW_RESTORE = 9
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        return True

    def launch(self, wait_seconds: float = 3.0) -> Dict[str, Any]:
        """Launch CAXA CAD if not already running, or bring it to front."""
        if not os.path.isfile(self.caxa_path):
            raise FileNotFoundError(f"CAXA executable not found at: {self.caxa_path}")

        if not self.is_running():
            bin_dir = os.path.dirname(self.caxa_path)
            subprocess.Popen([self.caxa_path], cwd=bin_dir, shell=False)
            time.sleep(wait_seconds)

        self.activate_window()
        return self.get_status()

    def open_drawing(self, file_path: str, wait_seconds: float = 2.0) -> Dict[str, Any]:
        """
        Open a CAD drawing (.dxf, .dwg, .exb) directly in CAXA.
        If CAXA is running, uses startfile or launches CAXA with the file argument.
        """
        abs_path = os.path.abspath(file_path)
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"Drawing file not found: {abs_path}")

        bin_dir = os.path.dirname(self.caxa_path)
        # Using CDRAFT_M.exe with the drawing file parameter
        subprocess.Popen([self.caxa_path, abs_path], cwd=bin_dir, shell=False)
        time.sleep(wait_seconds)
        self.activate_window()

        return {
            "opened_file": abs_path,
            "status": self.get_status(),
        }

    def send_command(self, command_str: str, press_enter: bool = True) -> bool:
        """
        Send a CAD command string or shortcut keys to CAXA.
        Activates CAXA window first, then simulates keystrokes.
        """
        if not self.activate_window():
            return False

        time.sleep(0.3)

        # Virtual key codes
        VK_RETURN = 0x0D
        VK_SPACE = 0x20
        VK_ESCAPE = 0x1B

        def send_vk(vk_code):
            user32.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(vk_code, 0, 2, 0)  # KEYEVENTF_KEYUP
            time.sleep(0.05)

        # First send ESC to clear any active command
        send_vk(VK_ESCAPE)

        # Type command characters
        for ch in command_str:
            vk = user32.VkKeyScanW(ord(ch)) & 0xFF
            shift = (user32.VkKeyScanW(ord(ch)) >> 8) & 1
            if shift:
                user32.keybd_event(0x10, 0, 0, 0)  # Shift down
            user32.keybd_event(vk, 0, 0, 0)
            time.sleep(0.02)
            user32.keybd_event(vk, 0, 2, 0)
            if shift:
                user32.keybd_event(0x10, 0, 2, 0)  # Shift up
            time.sleep(0.02)

        if press_enter:
            send_vk(VK_RETURN)

        return True

    def zoom_extents(self) -> bool:
        """Perform Zoom Extents in CAXA CAD (usually 'Z' -> Enter -> 'E' -> Enter)."""
        self.send_command("Z", press_enter=True)
        time.sleep(0.2)
        self.send_command("E", press_enter=True)
        return True

    def capture_screenshot(self, output_path: str) -> Optional[str]:
        """Capture screenshot of the CAXA window or primary screen."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        hwnd = self.find_main_window()
        if hwnd:
            self.activate_window()
            time.sleep(0.5)

        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img.save(output_path)
            return os.path.abspath(output_path)
        except Exception:
            # GDI fallback
            try:
                rect = wintypes.RECT()
                if hwnd and user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                    w = rect.right - rect.left
                    h = rect.bottom - rect.top
                    src_hwnd = hwnd
                else:
                    w = user32.GetSystemMetrics(0)
                    h = user32.GetSystemMetrics(1)
                    src_hwnd = user32.GetDesktopWindow()

                hwin_dc = user32.GetWindowDC(src_hwnd)
                hmem_dc = gdi32.CreateCompatibleDC(hwin_dc)
                hbmp = gdi32.CreateCompatibleBitmap(hwin_dc, w, h)
                gdi32.SelectObject(hmem_dc, hbmp)
                gdi32.BitBlt(hmem_dc, 0, 0, w, h, hwin_dc, 0, 0, 0x00CC0020)  # SRCCOPY

                from PIL import Image
                import win32ui, win32gui
                bmpinfo = gdi32.GetObjectW(hbmp, 0, None)
                # Cleanup
                gdi32.DeleteDC(hmem_dc)
                user32.ReleaseDC(src_hwnd, hwin_dc)
                gdi32.DeleteObject(hbmp)
            except Exception:
                pass

        return None
