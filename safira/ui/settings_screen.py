from tkinter import filedialog
from .finance_screens import Screen
from .widgets import *


class Settings(Screen):
    def __init__(self,parent,app):
        super().__init__(parent,app,'Configurações','Do seu jeito. Preferências, acesso e cuidado com os dados.')
        self.area=SapphireScrollFrame(self.body,fg_color='transparent',scrollbar_button_color=BORDER,scrollbar_button_hover_color=HOVER)
        self.area.pack(fill='both',expand=True)
        self.area.grid_columnconfigure((0,1),weight=1,uniform='settings')
        self.cards=[]
        def card(title,description,image,actions):
            surface=ctk.CTkFrame(self.area,fg_color=PANEL,corner_radius=18)
            label(surface,'',image=icon(image,BRIGHT,25)).pack(anchor='w',padx=22,pady=(22,10))
            label(surface,title,18,TEXT,True).pack(anchor='w',padx=22)
            label(surface,description,12,MUTED,wraplength=370,justify='left',anchor='w').pack(fill='x',padx=22,pady=(8,18))
            for text,callback in actions:
                button(surface,text,lambda cb=callback:self.app.guard(cb),True,height=36).pack(fill='x',padx=22,pady=(0,9))
            label(surface,'',height=6).pack()
            self.cards.append(surface)
        card('Aparência e movimento','Ajuste a escala e escolha uma experiência com menos animações.','settings',[
            ('Personalizar interface',self.preferences)])
        card('Senha e acesso','Seu perfil usa senha mestra e bloqueio automático por inatividade.','lock',[
            ('Alterar senha mestra',self.password),('Bloquear agora',app.lock)])
        card('Seus backups','Exporte uma cópia consistente. A restauração exige confirmação e preserva a base anterior.','download',[
            ('Exportar backup',self.backup),('Restaurar um backup',self.restore)])
        card('Armazenamento local','SAFIRA 3.1.0. Funciona offline. O banco e os backups não são criptografados.','report',[
            ('Ver localização dos dados',self.location),('Consultar log local',self.logs)])
        self.area.bind('<Configure>',self.layout_cards)

    def layout_cards(self,event):
        columns=1 if event.width<800 else 2
        for i,card in enumerate(self.cards):card.grid(row=i//columns,column=i%columns,sticky='nsew',padx=6,pady=6)

    def refresh(self):pass

    def password(self):
        def save(v):
            self.app.background(lambda:self.c.auth.change(v['current_password'],v['new_password'],v['confirm_password']),
                lambda _:self.app.toast('Senha alterada com sucesso.','success'))
        self.form('Alterar senha mestra',[
            ('current_password','Senha atual','',None),('new_password','Nova senha (10+ caracteres)','',None),
            ('confirm_password','Confirme a nova senha','',None)],save)

    def backup(self):
        path=filedialog.asksaveasfilename(parent=self,title='Backup SAFIRA',defaultextension='.sqlite',filetypes=[('Banco SQLite','*.sqlite')],initialfile='SAFIRA-backup.sqlite')
        if path:self.app.background(lambda:self.c.backup.export(path),lambda _:self.app.toast('Backup exportado e validado.','success'))

    def restore(self):
        path=filedialog.askopenfilename(parent=self,title='Restaurar SAFIRA',filetypes=[('Backup SQLite','*.sqlite *.db')])
        if not path:return
        if messagebox.askyesno('Restaurar seus dados','Os dados atuais serão substituídos, com cópia anterior preservada. Depois, entre com a senha do backup. Continuar?',parent=self):
            def done(safety):
                self.app.lock(); self.app.toast('Backup restaurado. Entre com a senha correspondente.','success')
            self.app.background(lambda:self.c.backup.restore(path,True),done)

    def preferences(self):
        def save(v):
            self.c.set_setting('auto_lock',int(v['lock']))
            self.app.preferences.save(v['reduced'],v['scale'])
            Motion.set_reduced(v['reduced']); ctk.set_widget_scaling(v['scale']/100)
        self.form('Personalizar interface',[
            ('lock','Bloqueio automático (segundos: 60–3600)',self.c.setting('auto_lock','300'),None),
            ('scale','Escala da interface',self.app.preferences.values['scale'],[(f'{x}%',x) for x in (90,100,110,125,150)]),
            ('reduced','Movimento',self.app.preferences.values['reduce_motion'],[('Animações suaves',False),('Reduzir movimento',True)])],save)

    def location(self):
        show_details(self,'Armazenamento',f'Base financeira:\n{self.c.store.path}\n\nPreferências visuais:\n{self.app.preferences.path}\n\nO local da base foi preservado. Backups não incluem as preferências visuais desta máquina.')

    def logs(self):
        path=self.c.store.path.parent/'logs'/'safira.log'
        content=path.read_text(encoding='utf-8')[-15000:] if path.exists() else 'Nenhum log registrado.'
        show_details(self,'Log local',content)
