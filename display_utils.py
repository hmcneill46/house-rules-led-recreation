import platform
import ctypes
from ctypes import wintypes

def get_display_ppi_and_scale():
    system = platform.system()

    # --- macOS ---
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
            ppi = (ppi_x + ppi_y) / 2

            print(f"[macOS] {ppi:.2f} PPI, scale={scale:.2f}")
            return ppi, scale

        except Exception as e:
            print(f"[Warning] macOS PPI detection failed: {e}")
            return None, 1.0

    # --- Windows ---
    elif system == "Windows":
        try:
            # Enable DPI awareness
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass

            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()

            # Get monitor handle
            MONITOR_DEFAULTTOPRIMARY = 1
            MonitorFromPoint = user32.MonitorFromPoint
            MonitorFromPoint.restype = wintypes.HMONITOR
            MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
            hMonitor = MonitorFromPoint(wintypes.POINT(0, 0), MONITOR_DEFAULTTOPRIMARY)

            # Get DPI for that monitor
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

            # Windows “scale factor” (e.g. 1.25 for 125%)
            scale = dpiX.value / 96.0

            # Get physical size from GDI
            hdc = user32.GetDC(0)
            HORZSIZE = 4
            VERTSIZE = 6
            horz_mm = ctypes.windll.gdi32.GetDeviceCaps(hdc, HORZSIZE)
            vert_mm = ctypes.windll.gdi32.GetDeviceCaps(hdc, VERTSIZE)
            ctypes.windll.user32.ReleaseDC(0, hdc)

            screen_w = user32.GetSystemMetrics(0)
            screen_h = user32.GetSystemMetrics(1)

            if horz_mm > 0:
                width_in = horz_mm / 25.4
                height_in = vert_mm / 25.4
                ppi_x = screen_w / width_in
                ppi_y = screen_h / height_in
                ppi = (ppi_x + ppi_y) / 2
            else:
                ppi = (dpiX.value + dpiY.value) / 2

            print(f"[Windows] {ppi:.2f} PPI, scale={scale:.2f}")
            return ppi, scale

        except Exception as e:
            print(f"[Warning] Windows PPI detection failed: {e}")
            return None, 1.0

    else:
        print("[Warning] Unsupported OS for PPI detection.")
        return None, 1.0


def mm_to_pixels(mm, ppi, scale=1.0):
    """
    Convert millimetres to *logical* pixels for window creation.
    macOS → divide by scale (because Pygame expects logical coords)
    Windows → don't divide (scale is already baked into PPI)
    """
    if platform.system() == "Darwin":
        return (mm / 25.4) * ppi / scale
    else:
        return (mm / 25.4) * ppi
