from safira.presentation_dates import date_br,month_br
from datetime import date,timedelta
from tkinter import filedialog
from safira.domain import add_months,brl
from safira.reports import export_pdf
from safira.dashboard_view import active_account_analytics
from safira.planning_service import planning_for
from .budget_chart import BudgetComparison
from .planning_dialogs import budget_panel,salary_panel,calendar_panel
from safira.ui.finance_screens import Screen,TODAY
from safira.ui.widgets import *


class Home(Screen):
    def __init__(self,parent,app,reports=False):
        self.reports=reports
        super().__init__(parent,app,'Relatórios' if reports else 'Visão geral',
            'Explore o período e exporte suas informações.' if reports else 'Seu dinheiro em perspectiva. Cada decisão começa com clareza.')
        if reports:
            self.action('Exportar PDF',self.export,secondary=False)
        else:
            self.toolbar.pack_forget()
            button(self.head,'Nova movimentação',lambda:self.app.guard(lambda:app.navigate('Movimentações')),
                width=166).pack(side='right',padx=(8,0))
            button(self.head,'Exportar PDF',lambda:self.app.guard(self.export),True,
                width=166).pack(side='right')
        self.period=Period(self.body,lambda:self.app.guard(self.refresh))
        if not reports:
            self.account_scope=SapphireTabs(self.period,values=['Somente contas ativas','Todas as contas'],
                command=lambda _:self.app.guard(self.refresh))
            self.account_scope.set('Somente contas ativas'); self.account_scope.pack(side='right',padx=16,pady=10)
        self.scroll=SapphireScrollFrame(self.body,fg_color='transparent',scrollbar_button_color=BORDER,scrollbar_button_hover_color=HOVER)
        self.scroll.pack(fill='both',expand=True)
        self.kpis=[]
        if not reports:self.build_dashboard()
        else:self.build_reports()

    def build_dashboard(self):
        self.top=ctk.CTkFrame(self.scroll,fg_color='transparent'); self.top.pack(fill='x',pady=(4,14))
        self.top.grid_columnconfigure(0,weight=5,uniform='hero'); self.top.grid_columnconfigure(1,weight=6,uniform='hero')
        self.hero=SapphireCard(self.top)
        self.hero.grid(row=0,column=0,sticky='nsew',padx=(0,8))
        surface=self.hero.content
        surface.configure(fg_color=SELECTED,border_width=1,border_color=blend(BLUE,PANEL,.65))
        header=ctk.CTkFrame(surface,fg_color='transparent'); header.pack(fill='x',padx=24,pady=(22,4))
        label(header,'SALDO REAL DISPONÍVEL',11,MUTED,True).pack(side='left')
        label(header,'',image=icon('wallet',BRIGHT,22)).pack(side='right')
        self.available=label(surface,'R$ 0,00',38,TEXT,True,anchor='w'); self.available.pack(fill='x',padx=24,pady=(6,4))
        self.available.configure(font=font(38,True,numeric=True))
        self.projection=label(surface,'',12,MUTED,anchor='w'); self.projection.pack(fill='x',padx=24,pady=(2,14))
        self.networth=label(surface,'',11,MUTED,anchor='w'); self.networth.pack(fill='x',padx=24,pady=(0,20))
        self.stat_area=ctk.CTkFrame(self.top,fg_color='transparent'); self.stat_area.grid(row=0,column=1,sticky='nsew')
        self.stat_area.grid_columnconfigure((0,1),weight=1,uniform='stats')
        for i,(name,key,color,image) in enumerate([('Receitas','income_cents',GREEN,'up'),('Despesas','expense_cents',RED,'down'),
                ('Investido','invested_cents',VIOLET,'invest'),('Resultado','result_cents',BRIGHT,'activity')]):
            card=StatCard(self.stat_area,name,0,color,image,'No período' if i!=2 else 'Posição atual')
            card.grid(row=i//2,column=i%2,sticky='nsew',padx=5,pady=(0,9 if i<2 else 0))
            self.kpis.append((card,key,color))
        self.chart_area=ctk.CTkFrame(self.scroll,fg_color='transparent'); self.chart_area.pack(fill='x',pady=(0,14))
        self.chart_area.grid_columnconfigure(0,weight=3,uniform='charts'); self.chart_area.grid_columnconfigure(1,weight=2,uniform='charts')
        self.budget_comparison=BudgetComparison(self.chart_area)
        self.budget_comparison.grid(row=0,column=0,sticky='nsew',padx=(0,8))
        self.evolution=Chart(self.scroll,'Saldo por mês (mês atual até hoje)',[],kind='line',height=255)

        self.distribution=Chart(self.chart_area,'Despesas por categoria',[],kind='donut',height=255)
        self.distribution.grid(row=0,column=1,sticky='nsew',padx=(8,0))
        self.lower=ctk.CTkFrame(self.scroll,fg_color='transparent'); self.lower.pack(fill='x',pady=(0,12))
        self.lower.grid_columnconfigure(0,weight=3,uniform='lower'); self.lower.grid_columnconfigure(1,weight=2,uniform='lower')
        recent=ctk.CTkFrame(self.lower,fg_color='transparent'); recent.grid(row=0,column=0,sticky='nsew',padx=(0,8))
        row=ctk.CTkFrame(recent,fg_color='transparent'); row.pack(fill='x',pady=3)
        label(row,'Atividade recente',16,TEXT,True).pack(side='left')
        button(row,'Ver todas',lambda:self.app.navigate('Movimentações'),True,width=94,height=30).pack(side='right')
        self.recent=Grid(recent,[('description','Descrição',260),('state','Estado',110),('amount','Valor',140)])
        self.cash=Chart(self.lower,'Competência e fluxo de caixa',[],height=260)
        self.cash.grid(row=0,column=1,sticky='nsew',padx=(8,0),pady=(34,0))
        self.evolution.pack(fill='x',pady=(0,14),before=self.lower)
        self.alerts=ctk.CTkFrame(self.scroll,fg_color=PANEL,corner_radius=18); self.alerts.pack(fill='x',pady=(0,10))
        label(self.alerts,'No seu radar',15,TEXT,True).pack(anchor='w',padx=22,pady=(18,4))
        self.alert_text=label(self.alerts,'',12,MUTED,justify='left',anchor='w',wraplength=850)
        self.alert_text.pack(fill='x',padx=22,pady=(6,18))
        self.top.bind('<Configure>',self._responsive)

    def _responsive(self,event):
        compact=event.width<850
        if getattr(self,'_compact',None)==compact:return
        self._compact=compact
        if compact:
            self.hero.grid(row=0,column=0,columnspan=2,sticky='nsew',padx=0)
            self.stat_area.grid(row=1,column=0,columnspan=2,sticky='nsew',pady=(8,0))
            self.distribution.grid(row=1,column=0,columnspan=2,sticky='nsew',padx=0,pady=(12,0))
            self.budget_comparison.grid(row=0,column=0,columnspan=2,sticky='nsew',padx=0)
        else:
            self.hero.grid(row=0,column=0,columnspan=1,sticky='nsew',padx=(0,8))
            self.stat_area.grid(row=0,column=1,columnspan=1,sticky='nsew',pady=0)
            self.budget_comparison.grid(row=0,column=0,columnspan=1,sticky='nsew',padx=(0,8))
            self.distribution.grid(row=0,column=1,columnspan=1,sticky='nsew',padx=(8,0),pady=0)

    def build_reports(self):
        row=ctk.CTkFrame(self.scroll,fg_color='transparent'); row.pack(fill='x',pady=6)
        row.grid_columnconfigure((0,1,2),weight=1,uniform='reports')
        for i,(name,key,color) in enumerate([('Receitas por competência','income_cents',GREEN),('Despesas por competência','expense_cents',RED),('Resultado do período','result_cents',BLUE)]):
            card=StatCard(row,name,0,color,note='Período selecionado'); card.grid(row=0,column=i,sticky='nsew',padx=5)
            self.kpis.append((card,key,color))
        row=ctk.CTkFrame(self.scroll,fg_color='transparent'); row.pack(fill='x',pady=12)
        row.grid_columnconfigure((0,1),weight=1,uniform='reportcharts')
        self.cash=Chart(row,'Fluxo efetivo de caixa',[],height=235); self.cash.grid(row=0,column=0,sticky='nsew',padx=(0,6))
        self.distribution=Chart(row,'Classificação das despesas',[],kind='donut',height=235); self.distribution.grid(row=0,column=1,sticky='nsew',padx=(6,0))
        label(self.scroll,'Registros do período',16,TEXT,True).pack(anchor='w',pady=6)
        self.recent=Grid(self.scroll,[('date','Data',100),('description','Descrição',240),('type','Tipo',150),('state','Estado',110),('amount','Valor',140)])

    def refresh(self):
        service=planning_for(self.c)
        service.generate(max(add_months(TODAY(),11,28),self.period.get()[1]))
        analytics=self.c.analytics if self.reports or self.account_scope.get()=='Todas as contas' else active_account_analytics(self.c)
        report=analytics.report(*self.period.get()); self.snapshot=report
        for card,key,color in self.kpis:card.update_value(report[key],color)
        categories=[(k,v,CHART_COLORS[i%len(CHART_COLORS)]) for i,(k,v) in enumerate(sorted(report['categories'].items(),key=lambda p:-p[1]))]
        self.distribution.update_series(categories)
        self.cash.update_series([('Receitas',report['income_cents'],GREEN),('Despesas',report['expense_cents'],RED),
            ('Entradas de caixa',report['cash_in_cents'],BLUE),('Saídas de caixa',report['cash_out_cents'],VIOLET)])
        if not self.reports:
            self.available.configure(text=brl(report['available_cents']),text_color=TEXT if report['available_cents']>=0 else RED)
            forecast=analytics.forecast((date.today()+timedelta(days=7)).isoformat())
            self.projection.configure(text='Previsto em 7 dias  '+brl(forecast['projected_cents']))
            self.networth.configure(text='Patrimônio líquido  '+brl(report['net_cents'])+'   ·   posição atual')
            start,end=self.period.get()
            month=end[:7]
            self.budget_comparison.update_data(service.comparison(month,analytics,end),month_br(month),date_br(end))
            monthly=analytics.monthly()
            self.evolution.update_series([(r['month'],r['cash'],BLUE) for r in monthly])
            self.recent.load(report['operations'][:5],lambda r:[r['description'],LABELS[r['status']],brl(r['amount_cents'])])
            alerts=analytics.notifications()
            self.alert_text.configure(text='\n'.join(f"{date_br(r['due'])}  ·  {r['title']}  ·  {brl(r['amount_cents'])}" for r in alerts[:4]) or 'Nenhuma obrigação próxima ou vencida. Tudo em dia por aqui.')
        else:self.recent.load(report['operations'],lambda r:[date_br(r['occurred']),r['description'],LABELS[r['kind']],LABELS[r['status']],brl(r['amount_cents'])])

    def export(self):
        start,end=self.period.get()
        planning_for(self.c).generate(max(add_months(TODAY(),11,28),end))
        report=self.c.analytics.report(start,end); report['forecast']=self.c.analytics.forecast(max(end,TODAY()))
        commitments=self.c.commitments.list(start,end); invoices=[i for i in self.c.cards.invoices() if start<=i['due']<=end]
        path=filedialog.asksaveasfilename(parent=self,title='Exportar relatório',defaultextension='.pdf',filetypes=[('PDF','*.pdf')],initialfile=f'SAFIRA-{start}-{end}.pdf')
        if path:self.app.background(lambda:export_pdf(path,report,commitments,invoices),lambda _:self.app.toast('Relatório PDF exportado.','success'))


class Planning(Screen):
    def __init__(self,parent,app):
        super().__init__(parent,app,'Planejamento','Antecipe seus próximos passos. Projeções ficam separadas do saldo real.')
        self.action('Orçamento por categoria',lambda:budget_panel(self),secondary=False)
        self.action('Receitas recorrentes',lambda:salary_panel(self))
        self.action('Calendário Ariquemes/RO',lambda:calendar_panel(self))
        bar=ctk.CTkFrame(self.body,fg_color='transparent'); bar.pack(fill='x')
        label(bar,'HORIZONTE',10,QUIET,True).pack(side='left',padx=(0,14))
        self.horizon=SapphireSelect(bar,values=['7 dias','30 dias','Mês atual','Próximo mês'],command=lambda _:self.app.guard(self.refresh))
        self.horizon.pack(side='left')
        self.metrics=ctk.CTkFrame(self.body,fg_color='transparent'); self.metrics.pack(fill='x',pady=16)
        self.real=StatCard(self.metrics,'Saldo real hoje',icon_name='wallet',note='Confirmado nas contas disponíveis')
        self.real.pack(side='left',fill='x',expand=True,padx=(0,6))
        self.projected=StatCard(self.metrics,'Saldo previsto',color=VIOLET,icon_name='plan',note='Inclui obrigações em aberto')
        self.projected.pack(side='left',fill='x',expand=True,padx=(6,0))
        self.comparison=label(self.body,'',12,MUTED,wraplength=900,justify='left'); self.comparison.pack(anchor='w',pady=6)
        self.grid=Grid(self.body,[('due','Vencimento',110),('source','Origem',150),('title','Descrição',280),('value','Efeito previsto',150)])

    def refresh(self):
        service=planning_for(self.c)
        service.generate(add_months(TODAY(),11,28))
        today=TODAY(); choice=self.horizon.get()
        if choice=='7 dias':end=(date.today()+timedelta(days=7)).isoformat()
        elif choice=='30 dias':end=(date.today()+timedelta(days=30)).isoformat()
        elif choice=='Mês atual':end=(date.fromisoformat(add_months(today,1,1))-timedelta(days=1)).isoformat()
        else:end=(date.fromisoformat(add_months(today,2,1))-timedelta(days=1)).isoformat()
        result=self.c.analytics.forecast(end)
        self.real.update_value(result['real_cents']); self.projected.update_value(result['projected_cents'],note='Projeção até '+date_br(end))
        realized=self.c.analytics.report(date.today().replace(day=1).isoformat(),TODAY())
        self.comparison.configure(text='Realizado no mês: receitas '+brl(realized['income_cents'])+'  ·  despesas '+brl(realized['expense_cents']))
        self.grid.load(result['events'],lambda r:[date_br(r['due']),r['source'],r['title'],brl(r['delta'])])


class Notifications(Screen):
    def __init__(self,parent,app):
        super().__init__(parent,app,'Notificações','O que merece sua atenção. Obrigações resolvidas deixam de aparecer automaticamente.')
        self.action('Abrir item relacionado',self.open,secondary=False); self.action('Atualizar',self.refresh)
        self.context=label(self.body,'',13,MUTED,anchor='w'); self.context.pack(fill='x',pady=(6,12))
        self.grid=Grid(self.body,[('due','Vencimento',110),('module','Módulo',150),('title','Descrição',250),('value','Valor',140),('state','Situação',130)])

    def refresh(self):
        planning_for(self.c).generate(add_months(TODAY(),11,28))
        alerts=self.c.analytics.notifications()
        self.context.configure(text=f'{len(alerts)} itens no seu radar' if alerts else 'Tudo em dia. Nenhuma obrigação exigindo atenção.')
        self.grid.load(alerts,lambda r:[date_br(r['due']),r['module'],f"#{r['id']} · {r['title']}",brl(r['amount_cents']),'Vencido' if r['overdue'] else 'Próximo'])

    def open(self):
        row=self.grid.selected(); self.app.navigate(row['module']); screen=self.app.screens[row['module']]
        if row['module']=='Compromissos':
            screen.period.start.delete(0,'end'); screen.period.start.insert(0,row['due'])
            screen.period.end.delete(0,'end'); screen.period.end.insert(0,row['due']); screen.refresh()
        for key,item in screen.grid.records.items():
            if item['id']==row['id']:screen.grid.selection_set(key); screen.grid.see(key); break
