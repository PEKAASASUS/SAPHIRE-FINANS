"""Non-reentrant CTk 6 scrollbars. Let the normal Tk loop flush the canvas.

CTkScrollbar._draw synchronously calls canvas.update_idletasks. At a DPI change,
nested scrollable frames can reenter scaling/layout through that flush. This
instance-local adapter suppresses only that synchronous flush, not drawing or
events. No third-party source file or global CTk object is modified.
"""
import customtkinter as ctk
from .tokens import PANEL,BORDER,HOVER


class SapphireScrollbar(ctk.CTkScrollbar):
    def _draw(self,no_color_updates=False):
        canvas=getattr(self,'_canvas',None)
        if canvas is None:return
        flush=canvas.update_idletasks
        canvas.update_idletasks=lambda:None
        try:super()._draw(no_color_updates)
        finally:canvas.update_idletasks=flush

    def set(self,start,end):
        values=(round(float(start),7),round(float(end),7))
        if getattr(self,'_last_fractions',None)==values:return
        self._last_fractions=values
        super().set(start,end)


class SapphireScrollFrame(ctk.CTkScrollableFrame):
    def __init__(self,parent,**kwargs):
        root=parent._root()
        before=set(root._tclCommands or ())
        super().__init__(parent,**kwargs)
        self._global_callback_ids=set(root._tclCommands or ())-before
        old=self._scrollbar
        fg=old.cget('fg_color'); color=old.cget('button_color'); hover=old.cget('button_hover_color')
        old.destroy()
        horizontal=self._orientation=='horizontal'
        self._scrollbar=SapphireScrollbar(self._parent_frame,orientation=self._orientation,
            command=self._parent_canvas.xview if horizontal else self._parent_canvas.yview,
            fg_color=fg,button_color=color,button_hover_color=hover,width=None if horizontal else 10,
            height=10 if horizontal else None)
        self._parent_canvas.configure(**{'xscrollcommand' if horizontal else 'yscrollcommand':self._scrollbar.set})
        self._create_grid()

    def destroy(self):
        root=self._root()
        for sequence in ('<MouseWheel>','<Button-4>','<Button-5>','<KeyPress-Shift_L>','<KeyPress-Shift_R>','<KeyRelease-Shift_L>','<KeyRelease-Shift_R>'):
            for callback in self._global_callback_ids:
                if callback in (root.bind_all(sequence) or ''):
                    root._unbind(('bind','all',sequence),callback)
        super().destroy()
