"""Paired, scrollable planned/actual bars with a common monetary scale."""
import tkinter as tk
import customtkinter as ctk
from safira.domain import brl
from .tokens import *
from .scrolling import SapphireScrollbar


class BudgetComparison(ctk.CTkFrame):
    def __init__(self,parent):
        super().__init__(parent,fg_color=PANEL,corner_radius=18)
        self.rows=[]
        self.title_label=ctk.CTkLabel(self,text='Planejado × Realizado',font=font(14,True),text_color=TEXT,anchor='w')
        self.title_label.pack(fill='x',padx=22,pady=(18,2))
        self.note=ctk.CTkLabel(self,text='Azul: planejado · verde/vermelho: realizado',font=font(10),text_color=MUTED,anchor='w')
        self.note.pack(fill='x',padx=22,pady=(0,4))
        body=ctk.CTkFrame(self,fg_color='transparent');body.pack(fill='both',expand=True,padx=16,pady=(4,14))
        self.canvas=tk.Canvas(body,bg=PANEL,highlightthickness=0,height=200)
        self.canvas.pack(side='left',fill='both',expand=True)
        self.bar=SapphireScrollbar(body,command=self.canvas.yview,width=10,fg_color=PANEL,button_color=BORDER)
        self.bar.pack(side='right',fill='y')
        self.canvas.configure(yscrollcommand=self.bar.set)
        self.canvas.bind('<Configure>',self.draw)
        self.canvas.bind('<MouseWheel>',lambda e:self.canvas.yview_scroll(-1 if e.delta>0 else 1,'units'))
        self.canvas.bind('<Button-4>',lambda _:self.canvas.yview_scroll(-1,'units'))
        self.canvas.bind('<Button-5>',lambda _:self.canvas.yview_scroll(1,'units'))

    def update_data(self,rows,month,until):
        self.rows=rows
        self.title_label.configure(text='Planejado × Realizado · '+month)
        self.note.configure(text='Orçamento geral · realizado até '+until+' nas contas selecionadas')
        self.draw()

    def draw(self,event=None):
        c=self.canvas;c.delete('all')
        scale=self._get_widget_scaling();width=max(200,c.winfo_width())
        row_height=72*scale
        c.configure(scrollregion=(0,0,width,max(c.winfo_height(),len(self.rows)*row_height)))
        if not self.rows:
            c.create_text(width/2,60*scale,text='Defina limites por categoria em Planejamento.',fill=MUTED,font=font(11),width=max(100,width-30))
            return
        maximum=max(1,max(max(r['planned'] or 0,r['actual']) for r in self.rows))
        label_width=min(150*scale,width*.28);right=width-115*scale
        available=max(10,right-label_width)
        for index,row in enumerate(self.rows):
            y=index*row_height+10*scale
            c.create_text(0,y+17*scale,text=row['name'],anchor='w',fill=TEXT,font=font(11),width=max(40,label_width-10*scale))
            for offset,value,color,caption in (
                (0,row['planned'],BLUE,'Planejado'),
                (25,row['actual'],RED if row['planned'] is not None and row['actual']>row['planned'] else GREEN,'Realizado')):
                top=y+offset*scale
                c.create_rectangle(label_width,top,right,top+12*scale,fill=SURFACE,outline='')
                if value:
                    c.create_rectangle(label_width,top,label_width+available*value/maximum,top+12*scale,fill=color,outline='')
                c.create_text(width-2,top+6*scale,text='Sem limite' if value is None else brl(value),anchor='e',fill=color if value is not None else MUTED,font=font(10))
            c.create_text(label_width,y+53*scale,text='Planejado / Realizado',anchor='w',fill=QUIET,font=font(8))
