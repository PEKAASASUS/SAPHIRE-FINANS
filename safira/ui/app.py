import logging,queue,sqlite3,threading,time
import customtkinter as ctk
from safira.ui.widgets import *
from safira.ui.finance_screens import Accounts,Catalog,Movements,Investments
from safira.ui.obligation_screens import CardScreen,Invoices,CommitmentScreen
from safira.ui.overview_screens import Home,Planning,Notifications
from safira.ui.settings_screen import Settings
from .sidebar import Sidebar
from .preferences import Preferences
from safira.branding import logo_image,apply_window_icon


class App(ctk.CTk):
    def __init__(self,controller):
        ctk.set_appearance_mode('dark'); ctk.set_default_color_theme('blue')
        super().__init__()
        self.controller=controller; self.preferences=Preferences(controller.store.path.parent)
        Motion.set_reduced(self.preferences.values['reduce_motion'])
        ctk.set_widget_scaling(self.preferences.values['scale']/100)
        self.title('SAFIRA • Personal Finance • 3.1.0')
        apply_window_icon(self)
        window_scale=self._get_window_scaling()
        usable_width=int((self.winfo_screenwidth()-60)/window_scale)
        usable_height=int((self.winfo_screenheight()-90)/window_scale)
        self.geometry(f'{min(1460,usable_width)}x{min(900,usable_height)}+20+20')
        self.minsize(min(1000,usable_width),min(620,usable_height)); self.configure(fg_color=BG)
        self.screens={}; self.active=None; self.busy=False; self.last_activity=time.monotonic(); self.tasks=queue.Queue()
        self.toast_widget=None; self.timer_ids=[]
        self.bind_all('<KeyPress>',self.touch,add='+'); self.bind_all('<Button>',self.touch,add='+'); self.bind_all('<Motion>',self.touch,add='+')
        self.protocol('WM_DELETE_WINDOW',self.close); self.report_callback_exception=self.callback_error
        self.login_screen(); self.after(80,self.poll); self.after(1000,self.check_lock)

    def touch(self,_=None):self.last_activity=time.monotonic()

    def clear(self):
        for widget in self.winfo_children():widget.destroy()
        self.screens={}; self.active=None; self.toast_widget=None

    def login_screen(self):
        self.clear(); self.grid_rowconfigure(0,weight=1); self.grid_columnconfigure(0,weight=1); self.grid_columnconfigure(1,weight=1)
        shell=ctk.CTkFrame(self,fg_color=BG); shell.place(relwidth=1,relheight=1)
        shell.grid_rowconfigure(0,weight=1); shell.grid_columnconfigure((0,1),weight=1,uniform='login')
        brand=ctk.CTkFrame(shell,fg_color=SIDEBAR,corner_radius=0); brand.grid(row=0,column=0,sticky='nsew')
        brand_inner=ctk.CTkFrame(brand,fg_color='transparent'); brand_inner.place(relx=.5,rely=.47,anchor='center')
        label(brand_inner,'',image=logo_image(360)).pack(anchor='w')
        label(brand_inner,'Seu dinheiro.\nSua próxima conquista.',32,TEXT,True,justify='left').pack(anchor='w',pady=(36,18))
        label(brand_inner,'Clareza para o presente.\nPerspectiva para o que vem depois.',15,MUTED,justify='left').pack(anchor='w')
        band=ctk.CTkFrame(brand_inner,fg_color=SELECTED,corner_radius=16)
        band.pack(fill='x',pady=(34,0))
        label(band,'',image=icon('lock',BRIGHT,22)).pack(side='left',padx=(18,12),pady=16)
        label(band,'Local. Offline. No seu controle.',12,MUTED).pack(side='left',padx=(0,18))
        right=ctk.CTkFrame(shell,fg_color=BG); right.grid(row=0,column=1,sticky='nsew')
        frame=ctk.CTkFrame(right,fg_color='transparent'); frame.place(relx=.5,rely=.5,anchor='center')
        configured=self.controller.auth.configured()
        label(frame,'BEM-VINDO DE VOLTA' if configured else 'SEU NOVO COMEÇO',10,BRIGHT,True).pack(anchor='w',pady=(0,12))
        label(frame,'Entre no seu espaço' if configured else 'Crie seu espaço financeiro',26,TEXT,True).pack(anchor='w')
        label(frame,'Use sua senha mestra para continuar.' if configured else 'Defina uma senha mestra com 10 ou mais caracteres.',12,MUTED).pack(anchor='w',pady=(8,28))
        label(frame,'Senha mestra',12,MUTED,True).pack(anchor='w',pady=(0,6))
        password=SapphireInput(frame,show='•',width=350,height=44,placeholder_text='Digite sua senha'); password.pack(fill='x')
        confirm=None
        if not configured:
            label(frame,'Confirme a senha',12,MUTED,True).pack(anchor='w',pady=(16,6))
            confirm=SapphireInput(frame,show='•',width=350,height=44); confirm.pack(fill='x')
        error=label(frame,'',12,RED,wraplength=350,justify='left'); error.pack(anchor='w',pady=8)
        def submit():
            secret=password.get(); confirmation=confirm.get() if confirm else ''
            def work():
                if configured:self.controller.auth.login(secret)
                else:self.controller.auth.setup(secret,confirmation)
            self.background(work,lambda _:self.shell(),lambda exc:error.configure(text=str(exc)))
        button(frame,'Acessar SAFIRA' if configured else 'Criar e começar',submit,height=44).pack(fill='x',pady=(6,22))
        label(frame,'3.1.0  ·  PERSONAL FINANCE',10,QUIET).pack(anchor='w')
        password.bind('<Return>',lambda _:submit())
        if confirm:confirm.bind('<Return>',lambda _:submit())
        self.after_idle(lambda:password.focus_set() if password.winfo_exists() else None)

    def shell(self):
        if not self.controller.auth.authenticated:self.login_screen(); return
        self.clear(); self.touch()
        self.grid_columnconfigure(0,weight=0); self.grid_columnconfigure(1,weight=1); self.grid_rowconfigure(0,weight=1)
        self.sidebar=Sidebar(self,self); self.sidebar.grid(row=0,column=0,sticky='ns')
        right=ctk.CTkFrame(self,fg_color=BG,corner_radius=0); right.grid(row=0,column=1,sticky='nsew')
        self.content=ctk.CTkFrame(right,fg_color=BG,corner_radius=0); self.content.pack(fill='both',expand=True)
        self.factories={'Home':lambda:Home(self.content,self),'Contas':lambda:Accounts(self.content,self),
            'Categorias':lambda:Catalog(self.content,self,'categories'),'Métodos':lambda:Catalog(self.content,self,'methods'),
            'Movimentações':lambda:Movements(self.content,self),'Transferências':lambda:Movements(self.content,self,True),
            'Cartões':lambda:CardScreen(self.content,self),'Faturas':lambda:Invoices(self.content,self),
            'Compromissos':lambda:CommitmentScreen(self.content,self),'Investimentos':lambda:Investments(self.content,self),
            'Planejamento':lambda:Planning(self.content,self),'Notificações':lambda:Notifications(self.content,self),
            'Relatórios':lambda:Home(self.content,self,True),'Configurações':lambda:Settings(self.content,self)}
        self.navigate('Home')

    def navigate(self,name):
        if self.busy:return
        if not self.controller.auth.authenticated:self.login_screen(); return
        def show():
            if name not in self.screens:self.screens[name]=self.factories[name]()
            if self.active:self.screens[self.active].pack_forget()
            screen=self.screens[name]; screen.pack(fill='both',expand=True); screen.refresh()
            self.active=name; self.sidebar.select(name)
            if hasattr(screen,'title_label'):
                screen.motion.animate('enter',250,lambda t:screen.title_label.configure(text_color=blend(MUTED,TEXT,t)))
            self.selection_changed(getattr(screen,'grid',None))
        self.guard(show)

    def selection_changed(self,grid):
        if self.active:
            screen=self.screens[self.active]
            if hasattr(screen,'update_actions'):screen.update_actions()

    def refresh_all(self):
        if self.active:self.screens[self.active].refresh()

    def toast(self,message,kind='info'):
        if self.toast_widget and self.toast_widget.winfo_exists():self.toast_widget.destroy()
        self.toast_widget=Toast(self,message,kind)

    def guard(self,callback):
        try:return callback()
        except sqlite3.IntegrityError:messagebox.showwarning('Revise o cadastro','Nome já utilizado ou vínculo inválido. Revise os dados.',parent=self)
        except (ValueError,TypeError) as exc:messagebox.showwarning('Revise os dados',str(exc),parent=self)
        except Exception as exc:
            logging.getLogger('safira').error('Falha em ação: %s',type(exc).__name__)
            messagebox.showerror('Não foi possível concluir','Não foi possível concluir a operação. Consulte o log local.',parent=self)

    def background(self,work,done,error=None):
        if self.busy:return
        self.busy=True
        self.overlay=SapphireModal(self,'Processando',width=440,height=350)
        label(self.overlay,'Estamos cuidando dos seus dados.',13,MUTED).pack(pady=16)
        self.progress=ctk.CTkProgressBar(self.overlay,mode='indeterminate',progress_color=BLUE,fg_color=SURFACE,width=330)
        self.progress.pack(padx=30,pady=14); self.progress.start()
        self.overlay.protocol('WM_DELETE_WINDOW',lambda:None); self.overlay.bind('<Escape>',lambda _:None)
        self.overlay.close=lambda:None
        def run():
            try:result=(True,work())
            except Exception as exc:result=(False,exc)
            self.tasks.put((result,done,error))
        threading.Thread(target=run,daemon=True).start()

    def poll(self):
        try:(ok,result),done,error=self.tasks.get_nowait()
        except queue.Empty:pass
        else:
            self.progress.stop(); self.overlay.destroy(); self.busy=False; self.touch()
            if ok:self.guard(lambda:done(result))
            elif error:error(result)
            else:self.guard(lambda:(_ for _ in ()).throw(result))
        self.after(80,self.poll)

    def check_lock(self):
        if not self.busy and self.controller.auth.authenticated and time.monotonic()-self.last_activity>=int(self.controller.setting('auto_lock','300')):self.lock()
        self.after(1000,self.check_lock)

    def lock(self):
        if self.busy:return
        self.controller.auth.lock(); self.login_screen()
    def callback_error(self,exc_type,exc,tb):
        logging.getLogger('safira').error('Falha de interface: %s',exc_type.__name__)
        messagebox.showerror('SAFIRA','Ocorreu um erro de interface. Consulte o log local.',parent=self)
    def close(self):
        if self.busy:self.toast('Aguarde a operação em andamento.'); return
        self.controller.auth.lock(); self.destroy()
