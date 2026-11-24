from .scrolling import SapphireScrollFrame
"""Compatibility exports plus Sapphire cards, period controls and typography."""
from datetime import date
import tkinter as tk
import customtkinter as ctk
from safira.domain import brl,iso,LABELS
from .tokens import *
from .controls import SapphireButton,SapphireInput,SapphireSelect,SapphireDatePicker,SapphireTabs
from .datagrid import SapphireDataGrid,Grid
from .dialogs import Form,SapphireModal,Toast,messagebox,show_details
from .charts import Chart
from .icons import icon,shadow_image
from .motion import Motion
from .labels import SapphireLabel


def label(parent,text,size=13,color=TEXT,bold=False,**kwargs):
    return SapphireLabel(parent,text=text,text_color=color,font=font(size,bold),**kwargs)


def button(parent,text,command,secondary=False,**kwargs):
    variant=kwargs.pop('variant','secondary' if secondary else 'primary')
    if any(word in text.casefold() for word in ('cancelar operação','cancelar compra','ignorar','parar recorrência')):variant='danger'
    return SapphireButton(parent,text=text,command=command,variant=variant,**kwargs)


class SapphireCard(ctk.CTkFrame):
    def __init__(self,parent,shadow=False,**kwargs):
        super().__init__(parent,fg_color=BG if shadow else 'transparent',corner_radius=RADIUS,**kwargs)
        self.shadow=shadow
        self.content=ctk.CTkFrame(self,fg_color=PANEL,corner_radius=RADIUS)
        if shadow:
            self.back=ctk.CTkLabel(self,text=''); self.back.place(relwidth=1,relheight=1)
            self.content.pack(fill='both',expand=True,padx=9,pady=(5,14))
            self.bind('<Configure>',self._resize,add='+'); self.pending=None
            self.bind('<Destroy>',self._cleanup,add='+')
        else:self.content.pack(fill='both',expand=True)

    def _resize(self,event):
        if self.pending:self.after_cancel(self.pending)
        width,height=event.width,event.height
        def paint():
            self.pending=None
            if not self.winfo_exists():return
            scale=self._get_widget_scaling()
            self.shadow_ref=ctk.CTkImage(shadow_image(width,height),size=(max(1,int(width/scale)),max(1,int(height/scale))))
            self.back.configure(image=self.shadow_ref)
            self.content.lift()
        self.pending=self.after(80,paint)

    def _cleanup(self,event):
        if event.widget==self and self.pending:
            try:self.after_cancel(self.pending)
            except tk.TclError:pass


class StatCard(ctk.CTkFrame):
    def __init__(self,parent,name,value=0,color=TEXT,icon_name='wallet',note=''):
        super().__init__(parent,fg_color=PANEL,corner_radius=16,border_width=1,border_color=PANEL)
        top=ctk.CTkFrame(self,fg_color='transparent'); top.pack(fill='x',padx=18,pady=(16,8))
        label(top,name,12,MUTED).pack(side='left')
        label(top,'',image=icon(icon_name,color,19)).pack(side='right')
        self.value=label(self,brl(value),23,color,True,anchor='w')
        self.value.configure(font=font(23,True,numeric=True))
        self.value.pack(fill='x',padx=18,pady=(0,4))
        self.note=label(self,note,10,QUIET,anchor='w'); self.note.pack(fill='x',padx=18,pady=(0,14))
        self.motion=Motion(self)
        self.last_value=value

    def update_value(self,value,color=None,note=None):
        changed=value!=self.last_value
        self.last_value=value
        self.value.configure(text=brl(value))
        if color:self.value.configure(text_color=color)
        if note is not None:self.note.configure(text=note)
        if changed:self.motion.animate('refresh',240,lambda t:self.configure(border_color=blend(SELECTED,PANEL,t)))


def metric(parent,name,value,color=TEXT):return StatCard(parent,name,value,color)


class Period(ctk.CTkFrame):
    def __init__(self,parent,callback):
        super().__init__(parent,fg_color=PANEL,corner_radius=14)
        self.pack(fill='x',pady=(2,8))
        today=date.today()
        label(self,'PERÍODO',10,QUIET,True).pack(side='left',padx=(16,12),pady=12)
        self.start=SapphireDatePicker(self,width=148); self.end=SapphireDatePicker(self,width=148)
        self.start.insert(0,today.replace(day=1).isoformat()); self.end.insert(0,today.isoformat())
        self.start.pack(side='left',padx=4,pady=10); label(self,'—',12,QUIET).pack(side='left',padx=4)
        self.end.pack(side='left',padx=4,pady=10)
        button(self,'Aplicar',callback,True,width=88,height=34).pack(side='left',padx=12)
        self.start.bind('<Return>',lambda _:callback()); self.end.bind('<Return>',lambda _:callback())

    def get(self):
        start,end=iso(self.start.get()),iso(self.end.get())
        if start>end:raise ValueError('Período inicial posterior ao final.')
        return start,end


def currency_input(value):
    sign='-' if value<0 else ''
    return f'{sign}{abs(value)//100},{abs(value)%100:02d}'
