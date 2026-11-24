from .scrolling import SapphireScrollFrame
"""Themed dialogs, forms and toast feedback. File selection stays with the OS."""
import tkinter as tk
from datetime import date
import customtkinter as ctk
from .tokens import *
from .controls import SapphireButton,SapphireInput,SapphireSelect,SapphireDatePicker
from .icons import icon
from .motion import Motion
from .labels import SapphireLabel
from safira.branding import apply_window_icon


class SapphireModal(ctk.CTkToplevel):
    def __init__(self,parent,title,width=560,height=600):
        super().__init__(parent)
        apply_window_icon(self)
        self.title(title); self.configure(fg_color=BG)
        root=parent.winfo_toplevel()
        self.transient(root)
        window_scale=self._get_window_scaling()
        width=min(width,int((self.winfo_screenwidth()-60)/window_scale))
        height=min(height,max(350,int((self.winfo_screenheight()-120)/window_scale)))
        actual_width=int(width*window_scale); actual_height=int(height*window_scale)
        x=max(8,min(root.winfo_rootx()+(root.winfo_width()-actual_width)//2,self.winfo_screenwidth()-actual_width-12))
        y=max(20,min(root.winfo_rooty()+(root.winfo_height()-actual_height)//2,self.winfo_screenheight()-actual_height-45))
        self.geometry(f'{width}x{height}+{x}+{y}')
        self.minsize(430,350)
        self.motion=Motion(self)
        self.previous_focus=root.focus_get()
        self.previous_grab=root.grab_current()
        self.protocol('WM_DELETE_WINDOW',self.close)
        self.bind('<Escape>',lambda _:self.close())
        self.header=ctk.CTkFrame(self,fg_color='transparent')
        self.header.pack(fill='x',padx=28,pady=(26,10))
        ctk.CTkLabel(self.header,text=title,font=font(22,True),text_color=TEXT,anchor='w').pack(side='left',fill='x',expand=True)
        SapphireButton(self.header,text='',image=icon('close'),variant='icon',width=32,command=self.close).pack(side='right')
        self.after_idle(self._enter)

    def _enter(self):
        if not self.winfo_exists():return
        self.grab_set()
        if not Motion.reduced:
            try:
                self.attributes('-alpha',.84)
                self.motion.animate('enter',DURATION['modal'],lambda t:self.attributes('-alpha',.84+.16*t))
            except tk.TclError:pass

    def close(self):
        if not self.winfo_exists():return
        if Motion.reduced:self.destroy(); return
        self.motion.animate('enter',130,lambda t:self.attributes('-alpha',1-.15*t),self.destroy)

    def destroy(self):
        self.motion.cancel()
        previous=self.previous_grab; focus=self.previous_focus
        super().destroy()
        try:
            if previous and previous.winfo_exists():previous.grab_set()
            if focus and focus.winfo_exists():focus.focus_set()
        except tk.TclError:pass


class Form(SapphireModal):
    def __init__(self,parent,title,fields,on_save,layout=None):
        super().__init__(parent,title,width=800 if layout else 560,height=710 if layout else 690)
        self.fields={}; self.choices={}; self.field_labels={}; self.on_save=on_save
        self.field_frames={}; self.field_layout=layout; self.hidden_fields=set()
        ctk.CTkLabel(self,text='Confira os dados antes de confirmar.',font=font(12),text_color=MUTED,anchor='w').pack(fill='x',padx=28,pady=(0,12))
        area=SapphireScrollFrame(self,fg_color=PANEL,corner_radius=16,
            scrollbar_button_color=BORDER,scrollbar_button_hover_color=HOVER)
        area.pack(fill='both',expand=True,padx=24,pady=4)
        self.field_area=area
        if layout:
            order=[key for group in layout for key in group]
            fields=sorted(fields,key=lambda field:order.index(field[0]))
            area.grid_columnconfigure((0,1),weight=1,uniform='form_fields')
            area.bind('<Configure>',self._layout_fields,add='+')
        for key,name,default,choices in fields:
            field_parent=area
            if layout:
                field_parent=ctk.CTkFrame(area,fg_color='transparent')
                self.field_frames[key]=field_parent
            self.field_labels[key]=ctk.CTkLabel(field_parent,text=name,font=font(12,True),text_color=MUTED,anchor='w',wraplength=450)
            self.field_labels[key].pack(anchor='w',padx=12,pady=(8,4) if layout else (14,6))
            if choices is not None:
                self.choices[key]={str(caption):value for caption,value in choices} or {'Nenhum cadastro disponível':None}
                widget=SapphireSelect(field_parent,values=list(self.choices[key]))
                selected=next((caption for caption,value in self.choices[key].items() if value==default),next(iter(self.choices[key])))
                widget.set(selected)
            elif key in ('date','occurred','due','opened','confirmed','competence') and not isinstance(default,int):
                widget=SapphireDatePicker(field_parent)
                widget.insert(0,str(default or ''))
            else:
                widget=SapphireInput(field_parent,show='•' if 'password' in key else '')
                widget.insert(0,str(default if default is not None else ''))
            widget.pack(fill='x',padx=12,pady=(0,2))
            self.fields[key]=widget
        if layout:self._layout_fields()
        self.error=ctk.CTkLabel(self,text='',font=font(12),text_color=RED,wraplength=480,justify='left')
        self.error.pack(fill='x',padx=28,pady=8)
        actions=ctk.CTkFrame(self,fg_color='transparent'); actions.pack(fill='x',padx=28,pady=(0,24))
        SapphireButton(actions,text='Cancelar',command=self.close,variant='tertiary',width=110).pack(side='left')
        self.save_button=SapphireButton(actions,text='Salvar alterações' if title.startswith(('Editar','Atualizar')) else 'Confirmar',command=self.save,width=180)
        self.save_button.pack(side='right')
        self.after_idle(self._focus_first)

    def _layout_fields(self,event=None):
        if not self.field_layout:return
        width=(event.width if event else self.field_area.winfo_width())/self.field_area._get_widget_scaling()
        compact=width<560
        row=0
        for group in self.field_layout:
            visible=[key for key in group if key not in self.hidden_fields]
            for column,key in enumerate(visible):
                self.field_frames[key].grid(row=row,column=0 if compact else column,
                    columnspan=2 if compact or len(visible)==1 else 1,sticky='ew',padx=4,pady=0)
                if compact:row+=1
            if not compact and visible:row+=1

    def set_field_visible(self,key,visible):
        if visible:self.hidden_fields.discard(key)
        else:
            self.hidden_fields.add(key)
            self.field_frames[key].grid_remove()
        self._layout_fields()

    def _focus_first(self):
        if self.fields:
            first=next(iter(self.fields.values()))
            if hasattr(first,'entry'):first.entry.focus_set()
            elif isinstance(first,ctk.CTkEntry):first.focus_set()

    def save(self):
        if self.save_button.cget('state')=='disabled':return
        self.save_button.configure(state='disabled')
        try:
            values={key:(self.choices[key][field.get()] if key in self.choices else field.get()) for key,field in self.fields.items()}
            self.on_save(values)
        except Exception as exc:
            message='Informe um número inteiro válido.' if str(exc).startswith('invalid literal for int') else str(exc)
            self.error.configure(text='Não foi possível salvar. '+message)
            self.save_button.configure(state='normal'); return
        root=self.master.winfo_toplevel()
        if hasattr(root,'toast') and not getattr(root,'busy',False):root.toast('Registro salvo com sucesso.','success')
        self.destroy()


class Message(SapphireModal):
    def __init__(self,parent,title,message,kind='info',confirm=False):
        super().__init__(parent,title,width=510,height=330)
        self.result=False
        color=RED if kind=='error' else YELLOW if kind=='warning' else BLUE
        body=ctk.CTkFrame(self,fg_color=PANEL,corner_radius=16); body.pack(fill='both',expand=True,padx=26,pady=8)
        SapphireLabel(body,text='',image=icon('info',color,26)).pack(anchor='w',padx=20,pady=(16,4))
        ctk.CTkLabel(body,text=message,font=font(13),text_color=MUTED,wraplength=410,justify='left').pack(anchor='w',padx=20,pady=(0,18))
        bar=ctk.CTkFrame(self,fg_color='transparent'); bar.pack(fill='x',padx=26,pady=(10,22))
        if confirm:SapphireButton(bar,text='Voltar',variant='tertiary',width=100,command=self.destroy).pack(side='left')
        def accept():self.result=True; self.destroy()
        self.accept_button=SapphireButton(bar,text='Confirmar' if confirm else 'Entendi',variant='danger' if confirm else 'primary',command=accept,width=130)
        self.accept_button.pack(side='right')
        self.bind('<Return>',lambda _:accept())


class Toast(ctk.CTkFrame):
    def __init__(self,parent,message,kind='info'):
        super().__init__(parent,fg_color=SURFACE,corner_radius=14,border_width=1,border_color=BORDER)
        color={'success':GREEN,'error':RED,'warning':YELLOW}.get(kind,BLUE)
        SapphireLabel(self,text='',image=icon('check' if kind=='success' else 'info',color,20)).pack(side='left',padx=(18,10),pady=14)
        ctk.CTkLabel(self,text=message,font=font(12),text_color=TEXT,wraplength=320,justify='left').pack(side='left',pady=14)
        SapphireButton(self,text='',image=icon('close',MUTED,14),variant='icon',width=26,height=26,command=self.destroy).pack(side='right',padx=10)
        self.place(relx=1,x=-26,y=18,anchor='ne'); self.lift()
        self.motion=Motion(self)
        self.motion.animate('enter',220,lambda t:self.place_configure(y=12+int(10*t)))
        self.timer=self.after(4000,self.destroy)

    def destroy(self):
        try:self.after_cancel(self.timer)
        except (AttributeError,tk.TclError):pass
        super().destroy()


class MessageBox:
    """Compatibility facade; all old screen calls now use Sapphire dialogs."""
    def showinfo(self,title,message,parent=None,**kwargs):
        root=parent.winfo_toplevel() if parent else ctk._default_root
        if hasattr(root,'toast'):root.toast(message,'success'); return
        dialog=Message(parent or root,title,message); dialog.wait_window()
    def showwarning(self,title,message,parent=None,**kwargs):
        dialog=Message(parent,title,message,'warning'); dialog.wait_window()
    def showerror(self,title,message,parent=None,**kwargs):
        dialog=Message(parent,title,message,'error'); dialog.wait_window()
    def askyesno(self,title,message,parent=None,**kwargs):
        dialog=Message(parent,title,message,'warning',True); dialog.wait_window(); return dialog.result

messagebox=MessageBox()


def show_details(parent,title,message):
    # Details are persistent and selectable, unlike transient success feedback.
    dialog=SapphireModal(parent,title,width=640,height=510)
    text=ctk.CTkTextbox(dialog,fg_color=PANEL,corner_radius=14,font=font(14),text_color=TEXT,border_width=0)
    text.pack(fill='both',expand=True,padx=26,pady=(8,24)); text.insert('1.0',message); text.configure(state='disabled')
    return dialog
