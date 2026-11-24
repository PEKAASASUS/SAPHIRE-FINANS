from safira.presentation_dates import date_br,month_br
from datetime import date
import customtkinter as ctk
from safira.domain import money,brl
from safira.branding import apply_window_icon
from safira.ui.widgets import *

TODAY=lambda:date.today().isoformat()


class Screen(ctk.CTkFrame):
    def __init__(self,parent,app,name,subtitle):
        super().__init__(parent,fg_color=BG,corner_radius=0)
        self.app=app; self.c=app.controller; self.motion=Motion(self)
        self.head=ctk.CTkFrame(self,fg_color='transparent')
        self.head.pack(fill='x',padx=28,pady=(12,3))
        self.title_label=label(self.head,name,28,TEXT,True)
        self.title_label.pack(side='left')
        self.subtitle=label(self,subtitle,12,MUTED,anchor='w',wraplength=1000,justify='left')
        self.subtitle.pack(fill='x',padx=28,pady=(0,12))
        self.toolbar=ctk.CTkFrame(self,fg_color='transparent')
        self.toolbar.pack(fill='x',padx=24,pady=(0,12))
        self.actions=[]
        self.toolbar.bind('<Configure>',lambda event:self.layout_actions(event.width))
        self.body=ctk.CTkFrame(self,fg_color='transparent')
        self.body.pack(fill='both',expand=True,padx=28,pady=(0,20))

    def action(self,text,callback,parent=None,secondary=True):
        selected=text in ('Editar','Arquivar / reativar','Histórico','Evolução','Desativar / reativar',
            'Cancelar operação','Detalhes','Atualizar avaliação','Aportar','Resgatar','Editar cartão','Ativar / desativar',
            'Cancelar compra selecionada','Pagar fatura','Fechar período','Histórico de pagamentos','Marcar pago',
            'Editar / adiar','Ignorar','Parar recorrência','Abrir item relacionado')
        variant='secondary' if secondary else 'primary'
        if text in ('Cancelar operação','Cancelar compra selecionada','Ignorar','Parar recorrência'):variant='danger'
        widget=button(self.toolbar,text,lambda:self.app.guard(callback),secondary,variant=variant,width=166)
        widget.requires_selection=selected; widget.action_text=text
        self.actions.append(widget); self.layout_actions(max(self.toolbar.winfo_width(),740))
        if selected:widget.configure(state='disabled')
        return widget

    def layout_actions(self,width):
        columns=max(1,width//178)
        for index,widget in enumerate(self.actions):
            widget.grid(row=index//columns,column=index%columns,padx=4,pady=4,sticky='w')

    def update_actions(self):
        for widget in self.actions:
            if not widget.requires_selection:continue
            grid=getattr(self,'purchases',None) if widget.action_text=='Cancelar compra selecionada' else getattr(self,'grid',None)
            selection=bool(grid and grid.selection())
            widget.configure(state='normal' if selection else 'disabled')

    def choices(self,table,kind=None):
        return [(r['name'],r['id']) for r in self.c.finance.catalogs(table,1) if not kind or r.get('kind')==kind]

    def form(self,title,fields,save,**options):
        def complete(values):
            save(values)
            self.app.guard(self.app.refresh_all)
        return Form(self,title,fields,complete,**options)

    def confirm(self,message,callback):
        if messagebox.askyesno('Confirmar ação',message,parent=self):
            callback(); self.app.refresh_all(); self.app.toast('Operação concluída.','success')

    def refresh(self):pass


class Accounts(Screen):
    def __init__(self,parent,app):
        super().__init__(parent,app,'Contas','Cada conta tem seu saldo. Reservas e investimentos ficam separados do dinheiro livre.')
        self.action('+ Nova conta',lambda:self.edit(),secondary=False)
        self.action('Editar',lambda:self.edit(self.grid.selected()))
        self.action('Arquivar / reativar',self.toggle)
        self.action('Histórico',self.history)
        self.action('Evolução',self.evolution)
        self.account_context=label(self.body,'Suas contas, cada uma com seu propósito.',13,MUTED,anchor='w')
        self.account_context.pack(fill='x',pady=(4,8))
        self.grid=Grid(self.body,[('name','Conta',220),('kind','Tipo',140),('balance','Saldo em caixa',140),('invested','Investido',140),('active','Estado',120)])

    def refresh(self):
        self.grid.load(self.c.finance.balances(),lambda r:[r['name'],LABELS[r['kind']],brl(r['balance_cents']),brl(r['invested_cents']),'Ativa' if r['active'] else 'Arquivada'])

    def edit(self,row=None):
        row=row or {}
        self.form('Editar conta' if row else 'Nova conta',[
            ('name','Nome',row.get('name',''),None),
            ('kind','Tipo',row.get('kind','bank'),[(LABELS[k],k) for k in ('bank','wallet','reserve','brokerage')]),
            ('initial','Saldo inicial (R$) — não é receita',currency_input(row.get('initial_cents',0)),None),
            ('opened','Data de abertura (DD/MM/AAAA)',row.get('opened',TODAY()),None)],
            lambda v:self.c.finance.account(v['name'],v['kind'],money(v['initial']),v['opened'],row.get('id')))

    def toggle(self):
        row=self.grid.selected()
        self.confirm('Alterar o estado desta conta? O histórico e os saldos serão preservados.',lambda:self.c.finance.activate('accounts',row['id'],not row['active']))

    def history(self):
        row=self.grid.selected()
        self.app.navigate('Movimentações')
        screen=self.app.screens['Movimentações']
        screen.account_filter.set(next((name for name,i in screen.account_map.items() if i==row['id']),'Todas'))
        screen.period.start.delete(0,'end'); screen.period.start.insert(0,row['opened'])
        screen.refresh()

    def evolution(self):
        row=self.grid.selected()
        win=ctk.CTkToplevel(self); apply_window_icon(win); win.title('Evolução • '+row['name']); win.geometry('720x360')
        points=self.c.finance.account_evolution(row['id'])
        Chart(win,'Saldo de caixa no fim de cada mês',[(r['date'][:7],r['balance_cents'],BLUE) for r in points]).pack(fill='both',expand=True,padx=20,pady=20)


class Catalog(Screen):
    def __init__(self,parent,app,table):
        self.table=table
        super().__init__(parent,app,'Categorias' if table=='categories' else 'Métodos de pagamento',
            'Cadastros preservam o histórico. Padrões podem ser desativados e reativados.')
        self.action('+ Novo',lambda:self.edit(),secondary=False)
        self.action('Editar',lambda:self.edit(self.grid.selected()))
        self.action('Desativar / reativar',self.toggle)
        filters=ctk.CTkFrame(self.body,fg_color='transparent')
        filters.pack(fill='x')
        self.state=SapphireTabs(filters,values=['Ativos','Inativos','Todos'],command=lambda _:self.refresh())
        self.state.set('Ativos'); self.state.pack(side='left')
        if self.table=='categories':
            self.kind_filter=SapphireTabs(filters,values=['Despesas','Receitas'],command=lambda _:self.refresh())
            self.kind_filter.set('Despesas'); self.kind_filter.pack(side='right')
        self.grid=Grid(self.body,[('name','Nome',300),('type','Tipo',160),('standard','Origem',140),('active','Estado',120)])

    def refresh(self):
        active={'Ativos':1,'Inativos':0,'Todos':None}[self.state.get()]
        rows=self.c.finance.catalogs(self.table,active)
        if self.table=='categories':
            kind='income' if self.kind_filter.get()=='Receitas' else 'expense'
            rows=[r for r in rows if r['kind']==kind]
        self.grid.load(rows,lambda r:[r['name'],LABELS.get(r.get('kind'),'Ambos'),'Padrão' if r['standard'] else 'Personalizado','Ativo' if r['active'] else 'Inativo'])

    def edit(self,row=None):
        row=row or {}
        if row.get('standard'):
            raise ValueError('Categoria/método padrão pode ser desativado ou reativado; não editado.')
        fields=[('name','Nome',row.get('name',''),None)]
        if self.table=='categories':
            fields.append(('kind','Tipo',row.get('kind','income' if self.kind_filter.get()=='Receitas' else 'expense'),[(LABELS[k],k) for k in ('income','expense')]))
        self.form('Editar cadastro' if row else 'Novo cadastro',fields,
            lambda v:self.c.finance.catalog(self.table,v['name'],v.get('kind'),row.get('id')))

    def toggle(self):
        row=self.grid.selected()
        self.c.finance.activate(self.table,row['id'],not row['active']); self.app.refresh_all()


class Movements(Screen):
    def __init__(self,parent,app,transfers=False):
        self.transfers=transfers
        super().__init__(parent,app,'Transferências' if transfers else 'Movimentações',
            'Transferências preservam o patrimônio e não geram receitas/despesas.' if transfers else 'Receitas e despesas reais. Pendências afetam apenas a projeção.')
        self.action('Transferir' if transfers else 'Nova movimentação',lambda:self.edit(),secondary=False)
        self.action('Editar',lambda:self.edit(self.grid.selected()))
        self.action('Cancelar operação',self.cancel)
        self.action('Detalhes',self.details)
        self.action('Limpar filtros',self.clear_filters)
        self.period=Period(self.body,lambda:self.app.guard(self.refresh))
        filters=ctk.CTkFrame(self.body,fg_color='transparent'); filters.pack(fill='x',pady=4)
        filters.grid_columnconfigure((0,1,2,3),weight=1)
        self.account_map={'Todas':None}; self.category_map={'Todas categorias':None}
        self.account_filter=SapphireSelect(filters,values=['Todas'],width=170,command=lambda _:self.app.guard(self.refresh))
        self.account_filter.grid(row=0,column=0,sticky='ew',padx=(0,8),pady=4)
        self.category_filter=SapphireSelect(filters,values=['Todas categorias'],width=190,command=lambda _:self.app.guard(self.refresh))
        self.category_filter.grid(row=0,column=1,sticky='ew',padx=(0,8),pady=4)
        self.kind_filter=SapphireSelect(filters,values=['Todos tipos','Receita','Despesa'],width=140,command=lambda _:self.app.guard(self.refresh))
        if not transfers:self.kind_filter.grid(row=0,column=2,sticky='ew',padx=(0,8),pady=4)
        self.search=SapphireInput(filters,placeholder_text='Pesquisar descrição',width=190,height=30)
        self.search.grid(row=0,column=3,sticky='ew',pady=4)
        self.filter_bar=filters
        filters.bind('<Configure>',self.layout_filters)
        self.search.bind('<Return>',lambda _:self.app.guard(self.refresh))
        columns=[('date','Data',100),('description','Descrição',220),('account','Contas',160),('category','Categoria',140),('state','Estado',110),('amount','Valor',140)]
        self.movement_grids={}
        if transfers:
            self.grid=Grid(self.body,columns)
            self.movement_grids['transfer']=self.grid
        else:
            tables=ctk.CTkFrame(self.body,fg_color='transparent')
            tables.pack(fill='both',expand=True,pady=(10,0))
            tables.grid_columnconfigure(0,weight=1)
            tables.grid_rowconfigure((0,1),weight=1,uniform='movement_tables')
            for index,(kind,title) in enumerate((('income','Receitas'),('expense','Despesas'))):
                panel=ctk.CTkFrame(tables,fg_color='transparent')
                panel.grid(row=index,column=0,sticky='nsew',pady=(0,8))
                panel.grid_propagate(False); panel.grid_columnconfigure(0,weight=1)
                panel.grid_rowconfigure(1,weight=1)
                label(panel,title,16,GREEN if kind=='income' else RED,True).grid(row=0,column=0,sticky='w',pady=(0,4))
                host=ctk.CTkFrame(panel,fg_color='transparent')
                host.grid(row=1,column=0,sticky='nsew'); host.pack_propagate(False)
                grid=Grid(host,columns,on_select=lambda row,k=kind:self.select_movement_grid(k,row))
                grid.pack_configure(fill='both',expand=True,pady=0)
                self.movement_grids[kind]=grid
            self.grid=self.movement_grids['income']
        for grid in self.movement_grids.values():
            grid.context_actions=[('Visualizar',lambda:self.app.guard(self.details)),('Editar',lambda:self.app.guard(lambda:self.edit(self.grid.selected()))),('Cancelar operação',lambda:self.app.guard(self.cancel))]

    def select_movement_grid(self,kind,row):
        if row is None:return
        self.grid=self.movement_grids[kind]
        for other in self.movement_grids.values():
            if other is not self.grid and other.selected_key is not None:
                other.selected_key=None; other.render()


    def layout_filters(self,event):
        if event.width<820:
            self.account_filter.grid(row=0,column=0,columnspan=2,sticky='ew',padx=(0,8))
            self.category_filter.grid(row=0,column=2,columnspan=2,sticky='ew')
            if not self.transfers:self.kind_filter.grid(row=1,column=0,columnspan=2,sticky='ew',padx=(0,8))
            self.search.grid(row=1,column=2,columnspan=2,sticky='ew')
        else:
            self.account_filter.grid(row=0,column=0,columnspan=1,sticky='ew',padx=(0,8))
            self.category_filter.grid(row=0,column=1,columnspan=1,sticky='ew',padx=(0,8))
            if not self.transfers:self.kind_filter.grid(row=0,column=2,columnspan=1,sticky='ew',padx=(0,8))
            self.search.grid(row=0,column=3,columnspan=1,sticky='ew')

    def clear_filters(self):
        self.account_filter.set('Todas'); self.category_filter.set('Todas categorias'); self.kind_filter.set('Todos tipos')
        self.search.delete(0,'end')
        self.refresh()

    def refresh(self):
        from safira.planning_service import planning_for
        from safira.domain import add_months
        planning_for(self.c).generate(max(add_months(TODAY(),11,28),self.period.get()[1]))
        selected=self.account_filter.get(); category=self.category_filter.get()
        self.account_map={'Todas':None,**{r['name']:r['id'] for r in self.c.finance.catalogs('accounts')}}
        self.category_map={'Todas categorias':None,**{f"{r['name']} · {LABELS[r['kind']]}":r['id'] for r in self.c.finance.catalogs('categories')}}
        self.account_filter.configure(values=list(self.account_map)); self.category_filter.configure(values=list(self.category_map))
        self.account_filter.set(selected if selected in self.account_map else 'Todas')
        self.category_filter.set(category if category in self.category_map else 'Todas categorias')
        start,end=self.period.get()
        kind='transfer' if self.transfers else {'Receita':'income','Despesa':'expense'}.get(self.kind_filter.get())
        rows=self.c.finance.movements(start,end,self.account_map[self.account_filter.get()],self.category_map[self.category_filter.get()],kind,self.search.get())
        for table_kind,grid in self.movement_grids.items():
            grid.load([r for r in rows if r['kind']==table_kind],lambda r:[date_br(r['occurred']),r['description'],r['accounts'],r['category'] or '—',LABELS[r['status']],brl(r['amount_cents'])])

    def edit(self,row=None):
        row=row or {}
        if row:
            self.form('Editar operação',[
                ('description','Descrição',row['description'],None),('amount','Valor (R$)',currency_input(row['amount_cents']),None),
                ('date','Data da operação',row['occurred'],None),('competence','Data de competência',row['competence'],None),
                ('confirmed','Data de confirmação (ignorada se pendente)',row['confirmed'] or TODAY(),None),
                ('status','Estado',row['status'],[('Confirmado','confirmed'),('Pendente','pending')])],
                lambda v:self.c.finance.edit_operation(row['id'],money(v['amount']),v['description'],v['date'],v['competence'],v['status'],v['confirmed']))
            return
        accounts=self.choices('accounts')
        if not accounts:
            raise ValueError('Cadastre uma conta ativa primeiro.')
        if self.transfers:
            self.form('Nova transferência',[
                ('origin','Conta de origem',None,accounts),('destination','Conta de destino',None,accounts),
                ('amount','Valor (R$)','',None),('date','Data',TODAY(),None),('description','Descrição','Transferência',None)],
                lambda v:self.c.finance.transfer(v['origin'],v['destination'],money(v['amount']),v['date'],v['description']))
        else:
            categories=self.c.finance.catalogs('categories',1)
            form=self.form('Nova movimentação',[
                ('account','Conta',None,accounts),('kind','Tipo','',[('Selecione Despesa ou Receita',''),('Despesa','expense'),('Receita','income')]),
                ('description','Descrição','',None),('amount','Valor (R$)','',None),('date','Data da operação',TODAY(),None),
                ('competence','Data de competência',TODAY(),None),('category','Categoria',None,
                    []),
                ('method','Método',None,self.choices('methods')),('status','Estado','confirmed',[('Confirmado','confirmed'),('Pendente','pending')]),
                ('confirmed','Data de confirmação (ignorada se pendente)',TODAY(),None)],
                lambda v:self.c.finance.movement(v['account'],v['kind'],v['description'],money(v['amount']),v['date'],v['category'],v['method'],v['status'],v['competence'],confirmed=v['confirmed']),
                layout=[('account','kind'),('description',),('amount','method'),
                    ('category','status'),('date','competence'),('confirmed',)])

            def update_categories(_):
                kind=form.choices['kind'][form.fields['kind'].get()]
                choices={'Selecione uma categoria':None}
                choices.update({r['name']:r['id'] for r in categories if r['kind']==kind})
                form.choices['category']=choices
                category=form.fields['category']
                if category.popup and category.popup.winfo_exists():category.popup.destroy()
                category.configure(values=list(choices)); category.set('Selecione uma categoria')
                form.set_field_visible('category',bool(kind))
            form.fields['kind'].configure(command=update_categories)
            update_categories(None)

    def cancel(self):
        row=self.grid.selected()
        self.confirm('Cancelar a operação e neutralizar seus efeitos financeiros?',lambda:self.c.finance.cancel_operation(row['id']))

    def details(self):
        row=self.grid.selected()
        show_details(self,'Detalhes da operação',f"#{row['id']} · {row['description']}\n\nOperação: {date_br(row['occurred'])}\nCompetência: {date_br(row['competence'])}\nConfirmação: {date_br(row['confirmed']) or 'Pendente'}\nOrigem: {row['source']}\nCategoria: {row['category'] or '—'}\nMétodo: {row['method'] or '—'}\nValor: {brl(row['amount_cents'])}\nEstado: {LABELS[row['status']]}")


class Investments(Screen):
    def __init__(self,parent,app):
        super().__init__(parent,app,'Investimentos','Posições locais e avaliação manual. Aportes e resgates usam o caixa da corretora.')
        self.action('+ Posição inicial',lambda:self.edit(),secondary=False)
        self.action('Atualizar avaliação',lambda:self.edit(self.grid.selected()))
        self.action('Aportar',lambda:self.flow(False))
        self.action('Resgatar',lambda:self.flow(True))
        self.grid=Grid(self.body,[('name','Posição',250),('account','Corretora',160),('cost','Custo registrado',140),('value','Valor atual',140)])

    def refresh(self):
        accounts={r['id']:r['name'] for r in self.c.finance.catalogs('accounts')}
        self.grid.load(self.c.finance.catalogs('positions'),lambda r:[r['name'],accounts.get(r['account_id']),brl(r['cost_cents']),brl(r['value_cents'])])

    def edit(self,row=None):
        row=row or {}
        choices=self.choices('accounts','brokerage')
        if not choices: raise ValueError('Cadastre uma corretora primeiro.')
        self.form('Avaliação da posição' if row else 'Posição inicial — não gera aporte',[
            ('account','Corretora',row.get('account_id'),choices),('name','Ativo / posição',row.get('name',''),None),
            ('cost','Custo registrado (R$)',currency_input(row.get('cost_cents',0)),None),
            ('value','Valor atual (R$)',currency_input(row.get('value_cents',0)),None)],
            lambda v:self.c.finance.position(v['account'],v['name'],money(v['cost']),money(v['value']),row.get('id')))

    def flow(self,redeem):
        row=self.grid.selected()
        self.form('Resgate' if redeem else 'Aporte',[
            ('amount','Valor (R$)','',None),('date','Data',TODAY(),None)],
            lambda v:self.c.finance.invest(row['id'],money(v['amount']),v['date'],redeem))
