from .scrolling import SapphireScrollFrame
import calendar
from datetime import date
import tkinter as tk
import customtkinter as ctk
from .tokens import *
from .icons import icon
from .motion import Motion
from .window_shape import round_popup
from safira.presentation_dates import date_br,date_iso


class SapphireButton(ctk.CTkButton):
    def __init__(self,parent,text='',command=None,variant='primary',**kwargs):
        self.variant=variant
        normal={'primary':BLUE,'secondary':SURFACE,'tertiary':PANEL,'danger':NEG_BG,'icon':PANEL}.get(variant,SURFACE)
        self.base_color=kwargs.pop('fg_color',normal)
        self.target_hover={'primary':BRIGHT,'danger':'#4A263B'}.get(variant,HOVER)
        options=dict(height=38,corner_radius=11,fg_color=self.base_color,hover=False,
            text_color=RED if variant=='danger' else TEXT,font=font(12,True),border_width=1,border_color=self.base_color)
        options.update(kwargs)
        super().__init__(parent,text=text,command=command,**options)
        self.motion=Motion(self)
        self.bind('<Enter>',lambda _:self._animate_hover(True),add='+')
        self.bind('<Leave>',lambda _:self._animate_hover(False),add='+')
        self.bind('<FocusIn>',lambda _:self.configure(border_color=BRIGHT),add='+')
        self.bind('<FocusOut>',lambda _:self.configure(border_color=self.base_color),add='+')
        self.bind('<ButtonPress-1>',lambda _:self._press(),add='+')
        self.bind('<ButtonRelease-1>',lambda _:self._animate_hover(True),add='+')
        self.bind('<Return>',lambda _:self.invoke(),add='+')

    def _press(self):
        if self.cget('state')!='disabled':self.configure(fg_color=blend(self.base_color,BG,.18))

    def _animate_hover(self,on):
        if self.cget('state')=='disabled':return
        start=self.cget('fg_color'); target=self.target_hover if on else self.base_color
        if not isinstance(start,str) or not start.startswith('#'):start=self.base_color
        if start.lower()==target.lower():return
        self.motion.animate('hover',DURATION['hover'],lambda t:self.configure(fg_color=blend(start,target,t)))

    def set_active(self,active):
        self.base_color=SELECTED if active else SIDEBAR
        self.configure(fg_color=self.base_color,text_color=TEXT if active else MUTED)

    def destroy(self):
        image=getattr(self,'_image',None)
        if isinstance(image,ctk.CTkImage):
            try:image.remove_configure_callback(self._update_image)
            except ValueError:pass
        super().destroy()


class SapphireInput(ctk.CTkEntry):
    def __init__(self,parent,**kwargs):
        options=dict(height=40,corner_radius=11,fg_color=BG,border_color=BORDER,border_width=1,
            text_color=TEXT,placeholder_text_color=QUIET,font=font(13))
        options.update(kwargs)
        super().__init__(parent,**options)
        self.bind('<FocusIn>',lambda _:self.configure(border_color=BRIGHT),add='+')
        self.bind('<FocusOut>',lambda _:self.configure(border_color=BORDER),add='+')


class Popover(ctk.CTkToplevel):
    def __init__(self,anchor,width=260,height=300):
        super().__init__(anchor)
        self.anchor=anchor
        self.overrideredirect(True)
        # Match the host surface behind the rounded popup content.
        surface=anchor.master
        background=BG
        while surface is not None:
            try:color=surface.cget('fg_color')
            except (ValueError,tk.TclError,AttributeError):color=None
            if color and color!='transparent':
                background=color; break
            surface=getattr(surface,'master',None)
        self.configure(fg_color=background)
        self.transient(anchor.winfo_toplevel())
        self.previous_grab=self.grab_current()
        self.update_idletasks()
        window_scale=self._get_window_scaling()
        width=min(width,int((self.winfo_screenwidth()-30)/window_scale))
        height=min(height,int((self.winfo_screenheight()-60)/window_scale))
        actual_width=int(width*window_scale); actual_height=int(height*window_scale)
        x=anchor.winfo_rootx(); y=anchor.winfo_rooty()+anchor.winfo_height()+6
        if y+actual_height>self.winfo_screenheight()-35:y=anchor.winfo_rooty()-actual_height-6
        self.geometry(f'{width}x{height}+{min(x,self.winfo_screenwidth()-actual_width-10)}+{max(10,y)}')
        self.bind('<Escape>',lambda _:self.destroy())
        self.bind('<FocusOut>',lambda _:self.after_idle(self._check_focus))
        self.bind('<Map>',self._activate,add='+')
        self.after_idle(self._activate_if_mapped)
        self.bind('<Configure>',self._round_bounds,add='+')
        self.bind('<ButtonPress-1>',self._dismiss_outside,add='+')

    def _dismiss_outside(self,event):
        x,y=self.winfo_rootx(),self.winfo_rooty()
        if not (x<=event.x_root<x+self.winfo_width()
                and y<=event.y_root<y+self.winfo_height()):
            self.destroy()
            return 'break'

    def _round_bounds(self,event):
        if event.widget is self:round_popup(self)

    def _activate_if_mapped(self):
        if self.winfo_exists() and self.winfo_ismapped():self._activate()

    def _activate(self,event=None):
        if event is not None and event.widget is not self:return
        self.grab_set()
        self.focus_force()

    def _check_focus(self):
        if self.winfo_exists() and self.focus_displayof() is None:self.destroy()

    def destroy(self):
        previous=self.previous_grab
        super().destroy()
        try:
            if previous and previous.winfo_exists():previous.grab_set()
        except tk.TclError:pass


class SapphireSelect(ctk.CTkFrame):
    def __init__(self,parent,values,command=None,width=180,height=40,**kwargs):
        kwargs={k:v for k,v in kwargs.items() if k in ('fg_color','corner_radius')}
        super().__init__(parent,width=width,height=height,fg_color=BG,corner_radius=11,border_width=1,border_color=BORDER)
        self.pack_propagate(False)
        self.values=list(values); self.value=self.values[0] if values else ''; self.command=command; self.popup=None
        self.display=ctk.CTkButton(self,text=self.value,anchor='w',fg_color='transparent',hover_color=SURFACE,
            height=height-4,corner_radius=9,font=font(12),text_color=TEXT,command=self.open)
        self.display.pack(side='left',fill='both',expand=True,padx=(8,0),pady=2)
        self.arrow=ctk.CTkButton(self,text='⌄',width=24,height=height-4,fg_color='transparent',hover_color=SURFACE,command=self.open)
        self.arrow.pack(side='right',padx=(0,4))
        self.display.bind('<Return>',lambda _:self.open(),add='+')
        self.display.bind('<Down>',lambda _:self.open(),add='+')
        self.display.bind('<FocusIn>',lambda _:super(SapphireSelect,self).configure(border_color=BRIGHT),add='+')
        self.display.bind('<FocusOut>',lambda _:super(SapphireSelect,self).configure(border_color=BORDER),add='+')
        self.bind('<Configure>',lambda _:self._truncate())

    def _truncate(self):
        limit=max(8,int((self.winfo_width()-55)/7))
        self.display.configure(text=self.value if len(self.value)<=limit else self.value[:limit-1]+'…')

    def get(self):return self.value
    def set(self,value):self.value=str(value); self._truncate()
    def configure(self,**kwargs):
        if 'values' in kwargs:self.values=list(kwargs.pop('values'))
        if 'command' in kwargs:self.command=kwargs.pop('command')
        if kwargs:super().configure(**kwargs)

    def open(self):
        if self.popup and self.popup.winfo_exists():self.popup.destroy(); return
        height=min(320,len(self.values)*40+16)
        window_scale=self.winfo_toplevel()._get_window_scaling()
        ratio=self._get_widget_scaling()/window_scale
        popup=Popover(self,max(230,round(self.winfo_width()/window_scale)),max(round(height*ratio),70)); self.popup=popup
        area=SapphireScrollFrame(popup,fg_color=PANEL,corner_radius=12,scrollbar_button_color=BORDER,scrollbar_button_hover_color=HOVER)
        area.pack(fill='both',expand=True,padx=1,pady=1)
        for value in self.values:
            b=SapphireButton(area,text=value,variant='tertiary',anchor='w',height=34,
                command=lambda v=value:self.choose(v))
            b.pack(fill='x',pady=2)
        popup.bind('<Return>',lambda _:self.choose(self.value))

    def choose(self,value):
        self.set(value)
        if self.popup and self.popup.winfo_exists():self.popup.destroy()
        if self.command:self.command(value)


class SapphireDatePicker(ctk.CTkFrame):
    def __init__(self,parent,width=150,**kwargs):
        super().__init__(parent,fg_color='transparent',height=40,width=width)
        self.grid_columnconfigure(0,weight=1)
        self.entry=SapphireInput(self,placeholder_text='DD/MM/AAAA',width=width-38)
        self.entry.grid(row=0,column=0,sticky='ew')
        self.calendar_button=SapphireButton(self,text='',image=icon('calendar',MUTED,17),variant='icon',width=34,command=self.open)
        self.calendar_button.grid(row=0,column=1,padx=(4,0))
        self.popup=None

    def get(self):
        value=self.entry.get()
        return date_iso(value) if value.strip() else ''
    def delete(self,*args):return self.entry.delete(*args)
    def insert(self,index,value):return self.entry.insert(index,date_br(value))
    def focus_set(self):return self.entry.focus_set()
    def bind(self,sequence=None,command=None,add=None):
        if hasattr(self,'entry'):return self.entry.bind(sequence,command,'+' if add is None else add)
        return super().bind(sequence,command,add)

    def open(self):
        if self.popup and self.popup.winfo_exists():self.popup.destroy(); return
        try:chosen=date.fromisoformat(self.get())
        except ValueError:chosen=date.today()
        self.month=chosen.replace(day=1)
        ratio=self._get_widget_scaling()/self.winfo_toplevel()._get_window_scaling()
        self.popup=Popover(self,round(310*ratio),round(340*ratio))
        self.calendar_area=ctk.CTkFrame(self.popup,fg_color=PANEL,corner_radius=14)
        self.calendar_area.pack(fill='both',expand=True,padx=1,pady=1)
        self.draw_month()

    def draw_month(self):
        for widget in self.calendar_area.winfo_children():widget.destroy()
        bar=ctk.CTkFrame(self.calendar_area,fg_color='transparent'); bar.pack(fill='x',padx=10,pady=12)
        SapphireButton(bar,text='‹',width=32,variant='tertiary',command=lambda:self.move(-1)).pack(side='left')
        months=['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
        ctk.CTkLabel(bar,text=f'{months[self.month.month-1]} {self.month.year}',font=font(14,True)).pack(side='left',expand=True)
        SapphireButton(bar,text='›',width=32,variant='tertiary',command=lambda:self.move(1)).pack(side='right')
        days=ctk.CTkFrame(self.calendar_area,fg_color='transparent'); days.pack(fill='both',expand=True,padx=10)
        for col,day in enumerate(['S','T','Q','Q','S','S','D']):
            days.grid_columnconfigure(col,weight=1)
            ctk.CTkLabel(days,text=day,text_color=QUIET,font=font(11)).grid(row=0,column=col)
        try:selected=self.get()
        except ValueError:selected=''
        for row,week in enumerate(calendar.monthcalendar(self.month.year,self.month.month),1):
            for col,day in enumerate(week):
                if not day:continue
                value=self.month.replace(day=day).isoformat()
                SapphireButton(days,text=str(day),width=32,height=30,variant='primary' if value==selected else 'tertiary',
                    command=lambda v=value:self.choose(v)).grid(row=row,column=col,padx=1,pady=1)

    def move(self,delta):
        index=self.month.year*12+self.month.month-1+delta
        self.month=date(index//12,index%12+1,1); self.draw_month()

    def choose(self,value):
        self.delete(0,'end'); self.insert(0,value)
        if self.popup and self.popup.winfo_exists():self.popup.destroy()
        self.entry.focus_set()


class SapphireTabs(ctk.CTkSegmentedButton):
    def __init__(self,parent,**kwargs):
        super().__init__(parent,fg_color=PANEL,selected_color=SELECTED,selected_hover_color=HOVER,
            unselected_color=PANEL,unselected_hover_color=SURFACE,text_color=MUTED,text_color_disabled=QUIET,
            corner_radius=10,height=36,font=font(12),**kwargs)
