"""Desktop notifications on macOS, Linux and Windows (falls back to the terminal)."""

import platform
import shutil
import subprocess


def _ps_escape(text: str) -> str:
    return text.replace("'", "''")


def notify(title: str, message: str) -> None:
    print(f"\a[{title}] {message}", flush=True)
    system = platform.system()
    try:
        if system == "Darwin":
            script = 'display notification (item 2 of argv) with title (item 1 of argv) sound name "Glass"'
            subprocess.run(
                ["osascript", "-e", f"on run argv\n{script}\nend run", title, message],
                check=False, capture_output=True,
            )
        elif system == "Linux" and shutil.which("notify-send"):
            subprocess.run(["notify-send", title, message], check=False, capture_output=True)
        elif system == "Windows":
            ps = (
                "Add-Type -AssemblyName System.Windows.Forms;"
                "$n = New-Object System.Windows.Forms.NotifyIcon;"
                "$n.Icon = [System.Drawing.SystemIcons]::Information;"
                "$n.Visible = $true;"
                f"$n.ShowBalloonTip(10000, '{_ps_escape(title)}', '{_ps_escape(message)}', 'Info');"
                "Start-Sleep -Seconds 10; $n.Dispose()"
            )
            subprocess.Popen(["powershell", "-NoProfile", "-Command", ps])
    except OSError:
        pass  # the terminal message above is enough
