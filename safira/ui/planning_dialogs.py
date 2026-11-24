"""Planning configuration and salary confirmation, without SQL in the UI."""
from datetime import date
from safira.domain import money,brl,add_months
from safira.presentation_dates import date_br,month_br
from safira.planning_service import planning_for
from .widgets import *
from .finance_screens import currency_input


def salary_panel(screen):
    service=planning_for(screen.c)
    win=SapphireModal(screen,'Receitas recorrentes',width=900,height=720)
    label(win,'5º dia útil · Ariquemes/RO · sem sábados, domingos e feriados',12,MUTED).pack(fill='x',padx=24,pady=(0,8))
    label(win,'Previsões não alteram o saldo real. Confirme somente depois de receber.',12,MUTED).pack(fill='x',padx=24,pady=(0,8))
    bar=ctk.CTkFrame(win,fg_color='transparent');bar.pack(fill='x',padx=24)
    area=ctk.CTkFrame(win,fg_color='transparent');area.pack(fill='both',expand=True,padx=24)
    tabs=SapphireTabs(area,values=['Recebimentos','Cadastros'],command=lambda _:show())
    tabs.pack(anchor='w',pady=8)
    host=ctk.CTkFrame(area,fg_color='transparent');host.pack(fill='both',expand=True);host.pack_propagate(False)
    grid=Grid(host,[('date','Data / início',115),('name','Descrição',170),('account','Conta',150),('value','Valor',130),('state','Estado',110)])
    grid.pack_configure(fill='both',expand=True)
    def refresh():
        service.generate(add_months(date.today().isoformat(),11,28))
        if tabs.get()=='Cadastros':
            grid.load(service.salaries(),lambda r:[month_br(r['start_month']),r['name'],r['account'],brl(r['amount_cents']),'Ativa' if r['active'] else 'Parada'])
        else:
            grid.load(service.occurrences(),lambda r:[date_br(r['occurred']),r['description'],r['account'],brl(r['amount_cents']),LABELS[r['status']]])
    def show():
        confirm.configure(state='normal' if tabs.get()=='Recebimentos' else 'disabled')
        stop.configure(state='normal' if tabs.get()=='Cadastros' else 'disabled')
        refresh()
    def new():
        def save(v):
            service.salary(v['name'],v['account'],v['category'],money(v['amount']),v['date'][:7])
            refresh();screen.app.refresh_all()
        Form(win,'Salário recorrente',[
            ('name','Descrição','Salário',None),('account','Conta de destino',None,screen.choices('accounts')),
            ('category','Categoria de receita',None,screen.choices('categories','income')),
            ('amount','Valor mensal previsto (R$)','',None),
            ('date','Primeiro mês (o dia será calculado)',date.today().isoformat(),None)],save)
    def receive():
        row=grid.selected()
        def save(v):
            service.confirm_salary(row['id'],money(v['amount']),v['date']);refresh();screen.app.refresh_all()
        Form(win,'Confirmar recebimento',[
            ('amount','Valor realmente recebido (R$)',currency_input(row['amount_cents']),None),
            ('date','Data real do recebimento',date.today().isoformat(),None)],save)
    def pause():
        row=grid.selected()
        if messagebox.askyesno('Parar receita recorrente','Parar a geração e cancelar as previsões futuras ainda pendentes deste cadastro?',parent=win):
            service.stop_salary(row['id']);refresh();screen.app.refresh_all()
    button(bar,'+ Receita recorrente',lambda:screen.app.guard(new),width=172).pack(side='left',padx=(0,8))
    confirm=button(bar,'Confirmar recebimento',lambda:screen.app.guard(receive),True,width=180);confirm.pack(side='left',padx=(0,8))
    stop=button(bar,'Parar recorrência',lambda:screen.app.guard(pause),True,width=150);stop.pack(side='left')
    show()
    return win


def calendar_panel(screen):
    service=planning_for(screen.c)
    win=SapphireModal(screen,'Calendário · Ariquemes/RO',width=730,height=620)
    label(win,'Feriados nacionais, 04/01 (RO), 04/10 e 11/10 (Ariquemes).',12,MUTED).pack(fill='x',padx=24,pady=(0,6))
    label(win,'Pontos facultativos não são excluídos automaticamente. Ajustes valem para novas previsões;\nprevisões já geradas podem ser ajustadas em Movimentações.',12,MUTED,justify='left').pack(fill='x',padx=24,pady=(0,12))
    def add():
        def save(v):
            service.calendar_override(v['date'],v['working'],v['note']);refresh()
        Form(win,'Exceção de calendário',[
            ('date','Data',date.today().isoformat(),None),
            ('working','Contagem',False,[('Não contar como dia útil',False),('Contar como dia útil',True)]),
            ('note','Motivo','',None)],save)
    button(win,'Adicionar / substituir exceção',lambda:screen.app.guard(add),True).pack(anchor='w',padx=24)
    area=ctk.CTkFrame(win,fg_color='transparent');area.pack(fill='both',expand=True,padx=24)
    grid=Grid(area,[('date','Data',120),('type','Contagem',150),('name','Motivo',260)])
    def refresh():grid.load(service.calendar(),lambda r:[date_br(r['day']),'Dia útil' if r['working'] else 'Não útil',r['note']])
    refresh()
    return win


def budget_panel(screen):
    service=planning_for(screen.c)
    win=SapphireModal(screen,'Orçamento mensal por categoria',width=820,height=680)
    label(win,'Limites fixos a partir do mês escolhido. Alterações preservam os meses anteriores.',12,MUTED,wraplength=740).pack(fill='x',padx=24,pady=(0,10))
    bar=ctk.CTkFrame(win,fg_color='transparent');bar.pack(fill='x',padx=24)
    month=SapphireDatePicker(bar,width=170);month.insert(0,date.today().replace(day=1).isoformat());month.pack(side='left')
    area=ctk.CTkFrame(win,fg_color='transparent');area.pack(fill='both',expand=True,padx=24)
    grid=Grid(area,[('name','Categoria',200),('planned','Planejado',150),('actual','Realizado',150),('rest','Restante',150)])
    def refresh():
        key=month.get()[:7]
        grid.load(service.comparison(key),lambda r:[r['name'],'Sem limite' if r['planned'] is None else brl(r['planned']),brl(r['actual']),
            '—' if r['planned'] is None else brl(r['planned']-r['actual'])])
    def edit():
        row=grid.selected() if grid.selection() else {}
        def save(v):service.budget(month.get()[:7],v['category'],money(v['amount']));refresh();screen.app.refresh_all()
        Form(win,'Limite fixo a partir de '+month_br(month.get()[:7]),[
            ('category','Categoria de despesa',row.get('id'),screen.choices('categories','expense')),
            ('amount','Limite mensal de '+month_br(month.get()[:7])+' em diante (R$)',currency_input(row.get('planned') or 0),None)],save)
    def remove():
        row=grid.selected()
        if messagebox.askyesno('Remover limite','Remover o limite desta categoria de '+month_br(month.get()[:7])+' em diante? Os meses anteriores serão preservados.',parent=win):
            service.remove_budget(month.get()[:7],row['id']);refresh();screen.app.refresh_all()
    button(bar,'Aplicar mês',lambda:screen.app.guard(refresh),True,width=105).pack(side='left',padx=8)
    button(bar,'Definir / editar limite',lambda:screen.app.guard(edit),width=170).pack(side='left',padx=8)
    button(bar,'Remover limite',lambda:screen.app.guard(remove),True,width=130).pack(side='left')
    refresh()

    return win
