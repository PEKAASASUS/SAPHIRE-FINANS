"""Native rounded bounds for undecorated popup windows."""
import ctypes
import ctypes.util
import math
import sys


def round_popup(window, radius=12):
    width, height = window.winfo_width(), window.winfo_height()
    radius = min(round(radius * window._get_window_scaling()), width // 2, height // 2)
    if width <= 1 or height <= 1:
        return
    if sys.platform == 'win32':
        from ctypes import wintypes
        gdi = ctypes.WinDLL('gdi32', use_last_error=True)
        user = ctypes.WinDLL('user32', use_last_error=True)
        gdi.CreateRoundRectRgn.argtypes = [ctypes.c_int] * 6
        gdi.CreateRoundRectRgn.restype = wintypes.HRGN
        gdi.DeleteObject.argtypes = [wintypes.HANDLE]
        user.SetWindowRgn.argtypes = [wintypes.HWND, wintypes.HRGN, wintypes.BOOL]
        region = gdi.CreateRoundRectRgn(0, 0, width + 1, height + 1, radius * 2, radius * 2)
        if region and not user.SetWindowRgn(int(window.wm_frame(), 0), region, True):
            gdi.DeleteObject(region)
    elif sys.platform.startswith('linux'):
        x11_name, shape_name = ctypes.util.find_library('X11'), ctypes.util.find_library('Xext')
        if not x11_name or not shape_name:
            return
        x11, shape = ctypes.CDLL(x11_name), ctypes.CDLL(shape_name)
        x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x11.XOpenDisplay.restype = ctypes.c_void_p
        x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        x11.XFlush.argtypes = [ctypes.c_void_p]
        shape.XShapeQueryExtension.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
        class Rectangle(ctypes.Structure):
            _fields_ = [('x', ctypes.c_short), ('y', ctypes.c_short),
                        ('width', ctypes.c_ushort), ('height', ctypes.c_ushort)]
        shape.XShapeCombineRectangles.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(Rectangle),
            ctypes.c_int, ctypes.c_int, ctypes.c_int]
        display = x11.XOpenDisplay(None)
        if not display:
            return
        try:
            event, error = ctypes.c_int(), ctypes.c_int()
            if not shape.XShapeQueryExtension(display, ctypes.byref(event), ctypes.byref(error)):
                return
            strips = []
            for y in range(height):
                distance = max(0, radius - (y + .5), (y + .5) - (height - radius))
                inset = math.ceil(radius - math.sqrt(max(0, radius * radius - distance * distance))) if distance else 0
                strips.append(Rectangle(inset, y, max(1, width - 2 * inset), 1))
            rectangles = (Rectangle * len(strips))(*strips)
            shape.XShapeCombineRectangles(display, int(window.wm_frame(), 0),
                0, 0, 0, rectangles, len(strips), 0, 0)
            x11.XFlush(display)
        finally:
            x11.XCloseDisplay(display)
