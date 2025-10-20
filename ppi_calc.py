import platform
import ctypes
from ctypes import wintypes

def get_display_ppi():
    system = platform.system()

    if system == "Darwin":
        try:
            from AppKit import NSScreen
            import Quartz

            screen = NSScreen.mainScreen()
            desc = screen.deviceDescription()
            display_id = desc["NSScreenNumber"]
            scale = screen.backingScaleFactor()
            size_mm = Quartz.CGDisplayScreenSize(display_id)

            width_mm, height_mm = size_mm.width, size_mm.height
            width_px = int(screen.frame().size.width * scale)
            height_px = int(screen.frame().size.height * scale)

            ppi_x = width_px / (width_mm / 25.4)
            ppi_y = height_px / (height_mm / 25.4)
            return (ppi_x + ppi_y) / 2

        except Exception as e:
            print(f"[Warning] macOS PPI detection failed: {e}")
            return None

    elif system == "Windows":
        try:
            # --- Enable DPI awareness ---
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass

            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()

            # --- Get monitor handle ---
            MONITOR_DEFAULTTOPRIMARY = 1
            MonitorFromPoint = user32.MonitorFromPoint
            MonitorFromPoint.restype = wintypes.HMONITOR
            MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
            hMonitor = MonitorFromPoint(wintypes.POINT(0, 0), MONITOR_DEFAULTTOPRIMARY)

            # --- Get DPI for that monitor ---
            shcore = ctypes.windll.shcore
            GetDpiForMonitor = shcore.GetDpiForMonitor
            GetDpiForMonitor.argtypes = [
                wintypes.HMONITOR,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_uint),
                ctypes.POINTER(ctypes.c_uint),
            ]
            GetDpiForMonitor.restype = ctypes.HRESULT

            dpiX = ctypes.c_uint()
            dpiY = ctypes.c_uint()
            MONITOR_DPI_TYPE = 0  # effective DPI
            res = GetDpiForMonitor(hMonitor, MONITOR_DPI_TYPE, ctypes.byref(dpiX), ctypes.byref(dpiY))

            if res != 0:
                raise ctypes.WinError(res)

            # --- Get physical screen size ---
            hdc = user32.GetDC(0)
            HORZSIZE = 4
            VERTSIZE = 6
            horz_mm = ctypes.windll.gdi32.GetDeviceCaps(hdc, HORZSIZE)
            vert_mm = ctypes.windll.gdi32.GetDeviceCaps(hdc, VERTSIZE)
            ctypes.windll.user32.ReleaseDC(0, hdc)

            # --- Calculate PPI ---
            screen_w = user32.GetSystemMetrics(0)
            screen_h = user32.GetSystemMetrics(1)

            if horz_mm > 0:
                width_in = horz_mm / 25.4
                height_in = vert_mm / 25.4
                ppi_x = screen_w / width_in
                ppi_y = screen_h / height_in
                return (ppi_x + ppi_y) / 2
            else:
                # fallback using DPI from Windows API
                return (dpiX.value + dpiY.value) / 2

        except Exception as e:
            print(f"[Warning] Windows PPI detection failed: {e}")
            return None

    else:
        print("[Warning] Unsupported OS for PPI detection.")
        return None


def mm_to_pixels(mm, ppi):
    return (mm / 25.4) * ppi