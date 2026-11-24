from safira.presentation_dates import month_br,date_br
"""Animated, viewport-sized charts from service data. No fabricated series."""
import math
import tkinter as tk
import customtkinter as ctk
from safira.domain import brl
from .tokens import *
from .datagrid import rounded
from .motion import Motion


class Chart(ctk.CTkFrame):
    def __init__(self,parent,title,series,kind='bars',height=260):
        super().__init__(parent,fg_color=PANEL,corner_radius=18,border_width=1,border_color=PANEL)
        self.title_label=ctk.CTkLabel(self,text=title,font=font(14,True),text_color=TEXT,anchor='w')
        self.title_label.pack(fill='x',padx=22,pady=(18,3))
        self.canvas=tk.Canvas(self,bg=PANEL,highlightthickness=0,height=height-54)
        self.canvas.pack(fill='both',expand=True,padx=16,pady=(4,14))
        self.series=series; self.kind=kind; self.progress=1; self.motion=Motion(self)
        self.canvas.bind('<Configure>',self.draw)
        self.canvas.bind('<Motion>',self.hover)
        self.canvas.bind('<Leave>',lambda _:self.canvas.delete('tooltip'))
        self.update_series(series)

    def update_series(self,series):
        changed=series!=self.series
        self.series=series
        self.motion.animate('chart',DURATION['chart'],self._progress) if changed or not hasattr(self,'started') else self.draw()
        self.started=True

    def _progress(self,t):self.progress=t; self.draw()

    def draw(self,_=None):
        c=self.canvas
        if not c.winfo_exists():return
        c.delete('all')
        width=max(200,c.winfo_width()); height=max(140,c.winfo_height())
        self.hit=[]
        if not self.series or not any(value for _,value,_ in self.series):
            c.create_oval(width/2-22,30,width/2+22,74,outline=BORDER,width=3)
            c.create_arc(width/2-22,30,width/2+22,74,start=20,extent=80,style='arc',outline=BLUE,width=3)
            c.create_text(width/2,103,text='Seu próximo capítulo começa aqui',fill=MUTED,font=font(11))
            c.create_text(width/2,125,text='Os gráficos aparecem quando houver registros.',fill=QUIET,font=font(10))
            return
        if self.kind=='line':self.line(width,height)
        elif self.kind=='donut':self.donut(width,height)
        else:self.bars(width,height)

    def bars(self,width,height):
        c=self.canvas; maximum=max(abs(value) for _,value,_ in self.series)
        step=min(42,(height-12)/max(len(self.series),1))
        label_width=min(160,width*.36)
        for index,(name,value,color) in enumerate(self.series):
            y=12+index*step
            c.create_text(2,y+7,text=name[:24],anchor='w',fill=MUTED,font=font(10))
            left=label_width; end=left+max(2,(width-left-106)*abs(value)/maximum*self.progress)
            rounded(c,left,y,width-102,y+13,6,fill=SURFACE,outline='')
            rounded(c,left,y,end,y+13,6,fill=color,outline='')
            c.create_text(width-2,y+7,text=brl(value),anchor='e',fill=TEXT,font=font(11,numeric=True))
            self.hit.append((0,y-5,width,y+25,name,value))

    def line(self,width,height):
        c=self.canvas; values=[v for _,v,_ in self.series]; minimum=min(0,min(values)); maximum=max(values)
        span=max(1,maximum-minimum); left=76; right=width-20; top=18; bottom=height-34
        for ratio in (0,.5,1):
            y=bottom-(bottom-top)*ratio
            c.create_line(left,y,right,y,fill=blend(PANEL,BORDER,.55),dash=(2,7))
            c.create_text(left-12,y,text=brl(int(minimum+span*ratio)),anchor='e',fill=QUIET,font=font(9))
        points=[]
        for index,(name,value,color) in enumerate(self.series):
            x=left+(right-left)*index/max(1,len(self.series)-1)
            y=bottom-(value-minimum)/span*(bottom-top)*self.progress
            points.extend([x,y]); self.hit.append((x-22,top,x+22,bottom+20,name,value))
            c.create_text(x,bottom+20,text=month_br(date_br(name)),fill=QUIET,font=font(9))
        if len(points)>=4:
            c.create_polygon(left,bottom,*points,right,bottom,fill=blend(PANEL,BLUE,.10),outline='',smooth=True)
            c.create_line(*points,fill=BLUE,width=2.5,smooth=True,splinesteps=24)
        for i in range(0,len(points),2):
            x,y=points[i:i+2]; c.create_oval(x-3,y-3,x+3,y+3,fill=BRIGHT,outline=PANEL,width=2)

    def donut(self,width,height):
        c=self.canvas; data=[r for r in self.series if r[1]>0]
        if not data:return
        diameter=min(height-16,width*.48,170); cx=diameter/2+12; cy=height/2
        total=sum(value for _,value,_ in data); start=90
        box=(cx-diameter/2,cy-diameter/2,cx+diameter/2,cy+diameter/2)
        c.create_oval(*box,outline=SURFACE,width=17)
        for index,(name,value,_) in enumerate(data):
            extent=-value/total*360*self.progress
            color=CHART_COLORS[index%len(CHART_COLORS)]
            c.create_arc(*box,start=start,extent=extent,style='arc',outline=color,width=17)
            start+=extent
            y=20+index*32
            if y+30<height:
                c.create_oval(diameter+30,y+3,diameter+37,y+10,fill=color,outline='')
                c.create_text(diameter+46,y+6,text=name[:23],anchor='w',fill=MUTED,font=font(10))
                c.create_text(diameter+46,y+22,text=brl(value),anchor='w',fill=TEXT,font=font(10,numeric=True))
                self.hit.append((diameter+20,y,width,y+30,name,value))
        c.create_text(cx,cy-8,text=str(len(data)),fill=TEXT,font=font(26,True))
        c.create_text(cx,cy+17,text='categorias',fill=QUIET,font=font(10))

    def hover(self,event):
        self.canvas.delete('tooltip')
        for x0,y0,x1,y1,name,value in self.hit:
            if x0<=event.x<=x1 and y0<=event.y<=y1:
                width=self.canvas.winfo_width(); x=min(event.x+12,max(6,width-228)); y=max(6,min(event.y-48,self.canvas.winfo_height()-48))
                rounded(self.canvas,x,y,x+220,y+40,9,fill=HOVER,outline=BORDER,tags='tooltip')
                self.canvas.create_text(x+12,y+20,text=f'{month_br(date_br(name))[:23]}  {brl(value)}',anchor='w',fill=TEXT,font=font(10),tags='tooltip')
                break
