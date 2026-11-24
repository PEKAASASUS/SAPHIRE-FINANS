from .scrolling import SapphireScrollFrame
import customtkinter as ctk
from .tokens import *
from .controls import SapphireButton
from .icons import icon
from .motion import Motion
from .labels import SapphireLabel
from safira.branding import logo_image

NAV_ICONS={'Home':'home','Movimentações':'activity','Contas':'wallet','Transferências':'transfer','Cartões':'card',
    'Faturas':'invoice','Compromissos':'calendar','Investimentos':'invest','Planejamento':'plan',
    'Notificações':'bell','Relatórios':'report','Configurações':'settings','Categorias':'tag','Métodos':'method','Organização':'calendar','Perspectivas':'report'}


class SidebarButton(SapphireButton):
    def _animate_hover(self,on):
        if on:self.master.set_hover(True)
        else:self.master.after_idle(self.master.check_hover)

    def _press(self):
        if self.cget('state')!='disabled':
            self.master.motion.cancel('surface')
            self.master.paint(blend(self.base_color,BG,.18))


class SidebarItem(ctk.CTkFrame):
    def __init__(self,parent,name,callback,small=False):
        super().__init__(parent,fg_color=SIDEBAR,corner_radius=11,height=34 if small else 38)
        self.name=name; self.active=False; self.motion=Motion(self)
        self.indicator=ctk.CTkFrame(self,width=3,height=20,corner_radius=2,fg_color=SIDEBAR)
        self.indicator.place(x=0,rely=.5,anchor='w')
        self.button=SidebarButton(self,text=name,command=callback,variant='tertiary',fg_color=SIDEBAR,
            image=icon(NAV_ICONS.get(name,'activity'),MUTED,17 if small else 20),anchor='w',height=31 if small else 35,
            font=font(12,False),border_width=0)
        self.button.pack(fill='x',padx=(8 if not small else 20,0),pady=2)

    def paint(self,color):
        self.button.configure(fg_color=color)
        if hasattr(self,'disclosure'):
            self.disclosure.configure(fg_color=color,bg_color=color,border_color=color)

    def check_hover(self):
        if not self.winfo_exists():return
        x,y=self.winfo_pointerxy()
        self.set_hover(self.winfo_rootx()<=x<self.winfo_rootx()+self.winfo_width()
            and self.winfo_rooty()<=y<self.winfo_rooty()+self.winfo_height())

    def set_hover(self,on):
        self.motion.cancel('selected')
        start=self.button.cget('fg_color')
        target=HOVER if on else SELECTED if self.active else SIDEBAR
        self.motion.animate('surface',DURATION['hover'],lambda t:self.paint(blend(start,target,t)))

    def set_active(self,active):
        if self.active==active:return
        self.active=active
        self.motion.cancel('surface')
        self.button.motion.cancel('hover')
        start=self.button.cget('fg_color'); target=SELECTED if active else SIDEBAR
        self.button.base_color=target
        self.button.configure(text_color=TEXT if active else MUTED,font=font(12,active),
            image=icon(NAV_ICONS.get(self.name,'activity'),BRIGHT if active else MUTED,20))
        if hasattr(self,'disclosure'):
            self.disclosure.base_color=target
            self.disclosure.configure(fg_color=target,bg_color=target,border_color=target)
        self.indicator.configure(fg_color=BLUE if active else SIDEBAR)
        self.motion.animate('selected',180,lambda t:self.paint(blend(start,target,t)))


class Sidebar(ctk.CTkFrame):
    MOVEMENT_SUBITEMS=('Transferências','Categorias','Métodos')
    def __init__(self,parent,app):
        super().__init__(parent,width=224,fg_color=SIDEBAR,corner_radius=0)
        self.pack_propagate(False); self.grid_propagate(False)
        self.app=app; self.items={}; self.groups={}; self.expanded=False; self.motion=Motion(self)
        brand=ctk.CTkFrame(self,fg_color='transparent'); brand.pack(fill='x',padx=18,pady=(16,12))
        SapphireLabel(brand,text='',image=logo_image(184),anchor='w').pack(anchor='w')
        ctk.CTkLabel(brand,text='P E R S O N A L   F I N A N C E',text_color=QUIET,font=font(8),anchor='w').pack(anchor='w',pady=(2,0))
        nav=SapphireScrollFrame(self,fg_color='transparent',scrollbar_button_color=BORDER,scrollbar_button_hover_color=HOVER)
        nav.pack(fill='both',expand=True,padx=(12,5))
        def section(text):
            ctk.CTkLabel(nav,text=text,font=font(9,True),text_color=QUIET,anchor='w').pack(fill='x',padx=18,pady=(10,4))
        def item(name):
            widget=SidebarItem(nav,name,lambda n=name:app.navigate(n)); widget.pack(fill='x',pady=1)
            self.items[name]=widget
            return widget
        section('VISÃO FINANCEIRA')
        item('Home')
        self.movement_row=item('Movimentações')
        self.arrow=SidebarButton(self.movement_row,text='›',variant='icon',width=22,height=28,border_width=0,fg_color=SIDEBAR,command=self.toggle)
        self.movement_row.disclosure=self.arrow
        self.arrow.place(relx=1,x=-9,rely=.5,anchor='e')
        self.submenu=ctk.CTkFrame(nav,fg_color='transparent',height=1)
        self.submenu.pack_propagate(False)
        for name in self.MOVEMENT_SUBITEMS:
            widget=SidebarItem(self.submenu,name,lambda n=name:app.navigate(n),True); widget.pack(fill='x')
            self.items[name]=widget
        item('Contas')
        for group_name,names in (
            ('Organização',('Cartões','Faturas','Compromissos','Investimentos')),
            ('Perspectivas',('Planejamento','Notificações','Relatórios')),
        ):
            row=SidebarItem(nav,group_name,lambda g=group_name:self.toggle_group(g))
            row.pack(fill='x',pady=(10,1))
            arrow=SidebarButton(row,text='›',variant='icon',width=22,height=28,border_width=0,
                fg_color=SIDEBAR,command=lambda g=group_name:self.toggle_group(g))
            row.disclosure=arrow
            arrow.place(relx=1,x=-9,rely=.5,anchor='e')
            submenu=ctk.CTkFrame(nav,fg_color='transparent',height=1)
            submenu.pack_propagate(False)
            self.groups[group_name]={'row':row,'arrow':arrow,'submenu':submenu,'names':names,'expanded':False}
            for name in names:
                widget=SidebarItem(submenu,name,lambda n=name:app.navigate(n),True)
                widget.pack(fill='x'); self.items[name]=widget
        footer=ctk.CTkFrame(self,fg_color='transparent'); footer.pack(fill='x',padx=16,pady=(6,12))
        self.items['Configurações']=SidebarItem(footer,'Configurações',lambda:app.navigate('Configurações'))
        self.items['Configurações'].pack(fill='x')
        session=ctk.CTkFrame(footer,fg_color=PANEL,corner_radius=14); session.pack(fill='x',pady=(12,0))
        ctk.CTkLabel(session,text='Perfil local',text_color=TEXT,font=font(11,True)).pack(anchor='w',padx=14,pady=(10,0))
        session_actions=ctk.CTkFrame(session,fg_color='transparent'); session_actions.pack(fill='x',padx=8,pady=(4,8))
        SapphireButton(session_actions,text='Bloquear',variant='tertiary',image=icon('lock',MUTED,16),height=28,width=132,command=app.lock).pack(side='left',fill='x',expand=True)
        SapphireButton(session_actions,text='',variant='icon',image=icon('logout',MUTED,16),height=28,width=30,command=app.lock).pack(side='right')

    def toggle(self):
        self.expanded=not self.expanded
        if self.expanded:self.submenu.pack(fill='x',after=self.movement_row)
        start=self.submenu.cget('height'); end=41*len(self.MOVEMENT_SUBITEMS) if self.expanded else 1
        self.arrow.configure(text='⌄' if self.expanded else '›')
        self.motion.animate('submenu',200,lambda t:self.submenu.configure(height=max(1,int(start+(end-start)*t))),
            None if self.expanded else self.submenu.pack_forget)

    def toggle_group(self,name):
        group=self.groups[name]; group['expanded']=not group['expanded']
        submenu=group['submenu']
        if group['expanded']:submenu.pack(fill='x',after=group['row'])
        start=submenu.cget('height'); end=41*len(group['names']) if group['expanded'] else 1
        group['arrow'].configure(text='⌄' if group['expanded'] else '›')
        self.motion.animate('submenu-'+name,200,
            lambda t:submenu.configure(height=max(1,int(start+(end-start)*t))),
            None if group['expanded'] else submenu.pack_forget)

    def select(self,name):
        for key,widget in self.items.items():widget.set_active(key==name)
        if name in self.MOVEMENT_SUBITEMS and not self.expanded:self.toggle()
        for group_name,group in self.groups.items():
            group['row'].set_active(name in group['names'])
            if name in group['names'] and not group['expanded']:self.toggle_group(group_name)
