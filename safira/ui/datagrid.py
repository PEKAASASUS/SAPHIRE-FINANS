from .scrolling import SapphireScrollbar
"""Virtualized financial Canvas grid: O(viewport) drawing, stable identity, keyboard."""
import math
import tkinter as tk
from tkinter import font as tkfont
import customtkinter as ctk
from .tokens import *
from .controls import Popover,SapphireButton


def rounded(canvas,x0,y0,x1,y1,r=8,**kwargs):
    r=min(r,(x1-x0)/2,(y1-y0)/2)
    return canvas.create_polygon(x0+r,y0,x1-r,y0,x1,y0,x1,y0+r,x1,y1-r,x1,y1,x1-r,y1,
        x0+r,y1,x0,y1,x0,y1-r,x0,y0+r,x0,y0,smooth=True,splinesteps=12,**kwargs)


class SapphireDataGrid(ctk.CTkFrame):
    def __init__(self,parent,columns,on_select=None):
        super().__init__(parent,fg_color=PANEL,corner_radius=18,border_width=1,border_color=PANEL)
        self.pack(fill='x',expand=False,pady=(14,0))
        self.columns=columns; self.records={}; self.keys=[]; self.selected_key=None; self.hover_key=None
        self.formatter=None; self.on_select=on_select; self.context_actions=[]; self.tree=self
        self.row_size=48; self.header_size=42; self.column_widths=[]; self.render_count=0
        self._last_x=None; self._last_y=None; self._last_region=None
        self.normal_font=tkfont.Font(family=FONT,size=10)
        self.bold_font=tkfont.Font(family=FONT,size=10,weight='bold')
        self.number_font=tkfont.Font(family=NUMBER_FONT,size=11)
        self.meta_font=tkfont.Font(family=FONT,size=9)
        self.header=tk.Canvas(self,height=42,bg=PANEL,highlightthickness=0)
        self.header.grid(row=0,column=0,sticky='ew',padx=(12,0),pady=(6,0))
        self.canvas=tk.Canvas(self,height=140,bg=PANEL,highlightthickness=0,takefocus=True)
        self.canvas.grid(row=1,column=0,sticky='nsew',padx=(12,0))
        self.vbar=SapphireScrollbar(self,command=self.canvas.yview,width=10,fg_color=PANEL,button_color=BORDER,button_hover_color=HOVER)
        self.vbar.grid(row=1,column=1,sticky='ns',padx=(2,5))
        self.hbar=SapphireScrollbar(self,orientation='horizontal',command=self._xview,height=8,
            fg_color=PANEL,button_color=BORDER,button_hover_color=HOVER)
        self.footer=ctk.CTkLabel(self,text='',text_color=QUIET,font=font(11),anchor='w')
        self.footer.grid(row=3,column=0,sticky='ew',padx=22,pady=(8,10))
        self.canvas.configure(yscrollcommand=self._yscroll,xscrollcommand=self._xscroll)
        self.grid_columnconfigure(0,weight=1); self.grid_rowconfigure(1,weight=1)
        self.canvas.bind('<Configure>',self._resize)
        self.canvas.bind('<Expose>',lambda _:self.render())
        self.canvas.bind('<Motion>',self._hover)
        self.canvas.bind('<Leave>',lambda _:self._leave())
        self.canvas.bind('<Button-1>',self._click)
        self.canvas.bind('<Button-3>',self._context)
        self.canvas.bind('<MouseWheel>',self._wheel)
        self.canvas.bind('<Button-4>',lambda _:self._scroll(-1))
        self.canvas.bind('<Button-5>',lambda _:self._scroll(1))
        self.canvas.bind('<Key>',self._key)
        self.canvas.bind('<FocusIn>',lambda _:self.configure(border_color=BLUE))
        self.canvas.bind('<FocusOut>',lambda _:self.configure(border_color=PANEL))
        self.resize_job=None
        parent.bind('<Configure>',self._parent_resize,add='+')
        self.bind('<Destroy>',self._cleanup,add='+')

    def _cleanup(self,event):
        if event.widget==self and self.resize_job:
            try:self.after_cancel(self.resize_job)
            except tk.TclError:pass

    def _parent_resize(self,_=None):
        if not self.winfo_exists():return
        if self.resize_job:self.after_cancel(self.resize_job)
        self.resize_job=self.after(50,self._height)

    def _height(self):
        self.resize_job=None
        if not self.winfo_exists():return
        count=len(self.keys)
        # Compact for small sets, fluid viewport for larger ones. No record cap.
        budget=max(120,min(460,self.master.winfo_height()-self.winfo_y()-100))
        height=min(budget,max(150 if not count else self.row_size,count*self.row_size))
        self.canvas.configure(height=height)
        self.render()

    def load(self,records,values):
        selected=self.selected_key
        self.formatter=values
        self.records={}; self.keys=[]
        for index,row in enumerate(records):
            identity=str(row.get('key',row.get('id',index)))
            if 'source' in row and row.get('id') is not None:identity=str(row['source'])+':'+identity
            if identity in self.records:identity+=':'+str(index)
            self.records[identity]=row; self.keys.append(identity)
        self.selected_key=selected if selected in self.records else None
        self.hover_key=None
        self.footer.configure(text=f'{len(self.keys):,} registros  ·  ↑ ↓ para navegar  ·  Enter para detalhes'.replace(',','.'))
        self._height(); self._resize()
        self._notify()

    def selected(self):
        if self.selected_key not in self.records:raise ValueError('Selecione um registro na lista.')
        return self.records[self.selected_key]

    def selection(self):return (self.selected_key,) if self.selected_key else ()
    def selection_set(self,key):
        key=str(key)
        if key in self.records:
            self.selected_key=key; self.render(); self._notify()
    def get_children(self):return tuple(self.keys)
    def see(self,key):
        if key not in self.records:return
        index=self.keys.index(key); total=max(1,len(self.keys)*self.row_size)
        top=self.canvas.canvasy(0); bottom=top+self.canvas.winfo_height()
        if index*self.row_size<top:self.canvas.yview_moveto(index*self.row_size/total)
        elif (index+1)*self.row_size>bottom:self.canvas.yview_moveto(((index+1)*self.row_size-self.canvas.winfo_height())/total)
        self.render()

    def _notify(self):
        if self.on_select:self.on_select(self.records.get(self.selected_key))
        app=self.winfo_toplevel()
        if hasattr(app,'selection_changed'):app.selection_changed(self)

    def _resize(self,_=None):
        scale=self._get_widget_scaling()
        ratio=scale/self.winfo_toplevel()._get_window_scaling()
        for face,size in ((self.normal_font,10),(self.bold_font,10),(self.number_font,11),(self.meta_font,9)):
            target=max(8,round(size*ratio))
            if face.cget('size')!=target:face.configure(size=target)
        self.row_size=round(48*scale)
        self.header_size=round(42*scale)
        self.header.configure(height=self.header_size)
        base=[max(70,w)*scale for _,_,w in self.columns]
        minimum=sum((110 if key in ('amount','value','balance','invested') else 115 if key in ('description','title','name') else 65)*scale for key,_,_ in self.columns)
        available=max(self.canvas.winfo_width(),minimum)
        self.column_widths=[int(w*available/sum(base)) for w in base]
        total=sum(self.column_widths)
        region=(0,0,total,max(1,len(self.keys)*self.row_size))
        if region!=self._last_region:
            self._last_region=region
            self.canvas.configure(scrollregion=region)
            self.header.configure(scrollregion=(0,0,total,self.header_size))
        if total>self.canvas.winfo_width()+3:self.hbar.grid(row=2,column=0,sticky='ew',padx=12)
        else:self.hbar.grid_remove()
        self.render_header(); self.render()

    def _yscroll(self,first,last):
        fractions=(round(float(first),6),round(float(last),6))
        if fractions==self._last_y:return
        self._last_y=fractions
        self.vbar.set(first,last); self.render()
    def _xscroll(self,first,last):
        fractions=(round(float(first),6),round(float(last),6))
        if fractions==self._last_x:return
        self._last_x=fractions
        self.hbar.set(first,last)
        if abs(self.header.xview()[0]-float(first))>0.000001:self.header.xview_moveto(float(first))
    def _xview(self,*args):
        self.canvas.xview(*args); self.header.xview(*args)
    def _scroll(self,delta):self.canvas.yview_scroll(delta,'units'); self.render()
    def _wheel(self,event):self._scroll(-int(event.delta/120)*2); return 'break'
    def _row_at(self,event):
        index=int(self.canvas.canvasy(event.y)//self.row_size)
        return self.keys[index] if 0<=index<len(self.keys) else None
    def _hover(self,event):
        key=self._row_at(event)
        if key!=self.hover_key:self.hover_key=key; self.render()
    def _leave(self):self.hover_key=None; self.render()
    def _click(self,event):
        self.canvas.focus_set(); key=self._row_at(event)
        if key:self.selection_set(key)
    def _key(self,event):
        if not self.keys:return
        index=self.keys.index(self.selected_key) if self.selected_key in self.records else 0
        jump=max(1,self.canvas.winfo_height()//self.row_size)
        target={'Up':index-1,'Down':index+1,'Home':0,'End':len(self.keys)-1,'Prior':index-jump,'Next':index+jump}.get(event.keysym)
        if target is not None:
            key=self.keys[max(0,min(len(self.keys)-1,target))]; self.selection_set(key); self.see(key); return 'break'
        if event.keysym=='Return' and self.context_actions:self.context_actions[0][1]()

    def _context(self,event):
        self._click(event)
        if not self.selected_key or not self.context_actions:return
        pop=Popover(self.canvas,230,48*len(self.context_actions)+12)
        for text,callback in self.context_actions:
            def act(cb=callback):pop.destroy(); cb()
            SapphireButton(pop,text=text,command=act,variant='danger' if 'Cancelar' in text else 'tertiary',anchor='w').pack(fill='x',padx=8,pady=4)

    def fit(self,text,width,font_obj=None):
        text=str(text if text is not None else '—'); font_obj=font_obj or self.normal_font
        if font_obj.measure(text)<=width:return text
        while text and font_obj.measure(text+'…')>width:text=text[:-1]
        return text+'…'

    def render_header(self):
        c=self.header; c.delete('all'); x=0
        for (key,name,_),width in zip(self.columns,self.column_widths):
            amount=key in ('amount','value','balance','invested','limit','paid','rest','total','free','cost')
            c.create_text(x+width-16 if amount else x+14,self.header_size/2,text=name.upper(),anchor='e' if amount else 'w',fill=QUIET,font=self.meta_font)
            x+=width
        c.create_line(0,self.header_size-1,sum(self.column_widths),self.header_size-1,fill=BORDER)

    def render(self):
        if not hasattr(self,'canvas') or not self.canvas.winfo_exists():return
        c=self.canvas; c.delete('all'); self.render_count+=1
        width=sum(self.column_widths) or c.winfo_width()
        if not self.keys:
            mid=c.winfo_width()/2
            rounded(c,mid-24,22,mid+24,70,14,fill=SURFACE,outline='')
            c.create_line(mid-10,46,mid+10,46,fill=BRIGHT,width=2)
            c.create_line(mid,36,mid,56,fill=BRIGHT,width=2)
            c.create_text(mid,96,text='Tudo pronto para começar',fill=TEXT,font=self.bold_font)
            c.create_text(mid,121,text='Nenhum registro neste filtro. Use a ação de cadastro acima.',fill=MUTED,font=self.meta_font)
            return
        start=max(0,int(c.canvasy(0)//self.row_size)-1)
        end=min(len(self.keys),start+math.ceil(c.winfo_height()/self.row_size)+3)
        for index in range(start,end):
            key=self.keys[index]; row=self.records[key]; y=index*self.row_size
            selected=key==self.selected_key; hovered=key==self.hover_key
            if selected or hovered:
                rounded(c,0,y+3,width-2,y+self.row_size-3,8,fill=SELECTED if selected else SURFACE,outline='')
                if selected:rounded(c,0,y+11,3,y+self.row_size-11,1,fill=BLUE,outline='')
            else:c.create_line(12,y+self.row_size-1,width-12,y+self.row_size-1,fill=blend(PANEL,BORDER,.5))
            values=self.formatter(row); x=0
            for (column,_,_),col_width,value in zip(self.columns,self.column_widths,values):
                value=str(value if value is not None else '—')
                amount='R$' in value
                status=column in ('state','active','standard')
                color=TEXT
                if amount:
                    if row.get('kind',row.get('type'))=='income':color=GREEN
                    elif row.get('kind',row.get('type'))=='expense' or value.startswith('-'):color=RED
                    text=self.fit(value,col_width-28,self.number_font)
                    c.create_text(x+col_width-14,y+self.row_size/2,text=text,anchor='e',fill=color,font=self.number_font)
                elif status:
                    positive=value in ('Confirmado','Pago','Quitada','Ativa','Ativo','Registrada')
                    negative=value in ('Cancelado','Cancelada','Vencida','Vencido')
                    warning=value in ('Pendente','Adiado','Próximo')
                    color=GREEN if positive else RED if negative else YELLOW if warning else MUTED
                    background=POS_BG if positive else NEG_BG if negative else WARN_BG if warning else SURFACE
                    text=self.fit(value,col_width-30,self.meta_font)
                    badge_width=min(col_width-20,self.meta_font.measure(text)+20)
                    rounded(c,x+10,y+self.row_size/2-12,x+10+badge_width,y+self.row_size/2+12,10,fill=background,outline='')
                    c.create_text(x+20,y+self.row_size/2,text=text,anchor='w',fill=color,font=self.meta_font)
                else:
                    offset=14
                    if column in ('type','kind'):
                        color=GREEN if value=='Receita' else RED if value=='Despesa' else MUTED
                        if value in ('Receita','Despesa'):
                            cy=y+self.row_size/2
                            c.create_line(x+12,cy+5,x+22,cy-5,fill=color,width=1.6)
                            c.create_line(x+15,cy-5,x+22,cy-5,x+22,cy+2,fill=color,width=1.6)
                            offset=30
                    c.create_text(x+offset,y+self.row_size/2,text=self.fit(value,col_width-offset-10),anchor='w',fill=color,
                        font=self.bold_font if column in ('description','title','name') else self.normal_font)
                x+=col_width

Grid=SapphireDataGrid
