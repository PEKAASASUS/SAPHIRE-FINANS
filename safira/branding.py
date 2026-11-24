"""Owner-supplied brand assets; source and packaged builds share the same files."""
from functools import lru_cache
from pathlib import Path
import sys

ASSETS={'logo':'safira-logo-horizontal-transparente.png','icon':'safira-icon-transparente-256.png','ico':'favicon-transparente.ico'}


def brand_file(kind):
    root=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))
    return root/'assets'/'brand'/ASSETS[kind]


@lru_cache(maxsize=8)
def logo_image(width):
    from PIL import Image
    import customtkinter as ctk
    with Image.open(brand_file('logo')) as source:
        image=source.copy()
    height=round(width*image.height/image.width)
    return ctk.CTkImage(light_image=image,dark_image=image,size=(width,height))


def apply_window_icon(window):
    import tkinter as tk
    if sys.platform=='win32':
        window.iconbitmap(str(brand_file('ico')))
    else:
        # Default applies to child windows too. Keep the PhotoImage alive.
        window._safira_icon=tk.PhotoImage(master=window,file=str(brand_file('icon')))
        window.iconphoto(True,window._safira_icon)
