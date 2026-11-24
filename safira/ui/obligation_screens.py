from safira.presentation_dates import date_br,month_br
from safira.domain import money,brl
from safira.ui.finance_screens import Screen,TODAY
from safira.ui.widgets import *


class CardScreen(Screen):
    def __init__(self,parent,app):
        super().__init__(parent,app,'Cartões','Crédito gera consumo por competência. O saldo bancário muda no pagamento da fatura.')
        self.action('+ Cartão',lambda:self.edit(),secondary=False)
        self.action('Editar cartão',lambda:self.edit(self.grid.selected()))
        self.action('Ativar / desativar',self.toggle)
        self.action('+ Compra',self.purchase,secondary=False)
        self.action('Faturas',lambda:self.app.navigate('Faturas'))
        self.deck=ctk.CTkFrame(self.body,fg_color=SELECTED,corner_radius=18)
        self.deck.pack(fill='x',pady=(4,12))
        label(self.deck,'SEUS CARTÕES',10,BRIGHT,True).pack(anchor='w',padx=20,pady=(14,3))
        self.card_summary=label(self.deck,'Crédito e débito, organizados.',19,TEXT,True,anchor='w')
        self.card_summary.pack(fill='x',padx=20,pady=(0,14))
        self.table_tabs=SapphireTabs(self.body,values=['Cartões','Compras'],command=self.switch_table)
        self.table_tabs.set('Cartões'); self.table_tabs.pack(anchor='w',pady=4)
        self.grid=Grid(self.body,[('name','Cartão',200),('kind','Tipo',100),('limit','Limite',140),('free','Disponível',140),('close','Fecha',80),('due','Vence',80),('active','Estado',100)])

        self.action('Cancelar compra selecionada',self.cancel_purchase,self.body)
        self.purchases=Grid(self.body,[('date','Data',100),('name','Compra',220),('card','Cartão',140),('count','Parcelas',80),('amount','Valor total',130),('state','Estado',100)])
        self.purchases.pack_forget()

    def switch_table(self,value):
        self.grid.pack_forget(); self.purchases.pack_forget()
        target=self.grid if value=='Cartões' else self.purchases
        target.pack(fill='x',pady=(14,0))
        self.update_actions()

    def update_actions(self):
        super().update_actions()
        if not hasattr(self,'table_tabs'):return
        for action in self.actions:
            if self.table_tabs.get()=='Compras' and action.action_text in ('Editar cartão','Ativar / desativar'):
                action.configure(state='disabled')
            if self.table_tabs.get()=='Cartões' and action.action_text=='Cancelar compra selecionada':
                action.configure(state='disabled')

    def refresh(self):
        rows=[]
        for row in self.c.finance.catalogs('cards'):
            row['free']=row['limit_cents']-self.c.cards.outstanding(row['id'])
            rows.append(row)
        self.card_summary.configure(text=f'{len(rows)} cartões no seu espaço' if rows else 'Seu primeiro cartão começa aqui.')
        self.grid.load(rows,lambda r:[r['name'],LABELS[r['kind']],brl(r['limit_cents']) if r['kind']=='credit' else '—',brl(r['free']) if r['kind']=='credit' else 'Conta vinculada',r['closing_day'],r['due_day'],'Ativo' if r['active'] else 'Inativo'])
        self.purchases.load(self.c.cards.purchases(),lambda r:[date_br(r['occurred']),r['description'],r['card'],r['installments'] or 'Débito',brl(r['amount_cents']),'Cancelada' if r['cancelled'] else 'Registrada'])

    def edit(self,row=None):
        row=row or {}
        self.form('Editar cartão' if row else 'Novo cartão',[
            ('name','Nome (não informe número completo ou CVV)',row.get('name',''),None),
            ('kind','Tipo',row.get('kind','credit'),[('Crédito','credit'),('Débito','debit')]),
            ('account','Conta associada',row.get('account_id'),[('Sem conta associada',None)]+self.choices('accounts')),
            ('limit','Limite de crédito (R$)',currency_input(row.get('limit_cents',0)),None),
            ('closing','Dia de fechamento (1–31)',row.get('closing_day',10),None),
            ('due','Dia de vencimento (1–31)',row.get('due_day',20),None)],
            lambda v:self.c.cards.save(v['name'],v['kind'],v['account'],money(v['limit']),int(v['closing']),int(v['due']),row.get('id')))

    def toggle(self):
        row=self.grid.selected()
        self.c.finance.activate('cards',row['id'],not row['active']); self.app.refresh_all()

    def purchase(self):
        choices=self.choices('cards')
        if not choices: raise ValueError('Cadastre um cartão ativo primeiro.')
        self.form('Registrar compra',[
            ('card','Cartão',None,choices),('description','Descrição','',None),('amount','Valor total (R$)','',None),
            ('date','Data da compra',TODAY(),None),('category','Categoria',None,self.choices('categories','expense')),
            ('count','Número de parcelas (débito: 1)','1',None)],
            lambda v:self.c.cards.purchase(v['card'],v['description'],money(v['amount']),v['date'],v['category'],int(v['count'])))

    def cancel_purchase(self):
        row=self.purchases.selected()
        self.confirm('Cancelar a compra? Compras em faturas com pagamento exigem estorno conciliado e não podem ser canceladas aqui.',lambda:self.c.cards.cancel(row['id']))


class Invoices(Screen):
    def __init__(self,parent,app):
        super().__init__(parent,app,'Faturas','Total, pagamentos e restante preservados por ciclo. Pagamento parcial não calcula juros automaticamente.')
        self.action('Pagar fatura',self.pay,secondary=False)
        self.action('Fechar período',self.close)
        self.action('Histórico de pagamentos',self.history)
        self.grid=Grid(self.body,[('card','Cartão',180),('close','Fechamento',110),('due','Vencimento',110),('total','Total',140),('paid','Pago',140),('rest','Restante',140),('state','Estado',110)])

    def refresh(self):
        self.grid.load(self.c.cards.invoices(),lambda r:[r['card'],date_br(r['closing']),date_br(r['due']),brl(r['total_cents']),brl(r['paid_cents']),brl(r['remaining_cents']),
            'Quitada' if r['remaining_cents']==0 else ('Vencida' if r['due']<TODAY() else 'Fechada' if r['closed'] or r['closing']<=TODAY() else 'Aberta')])

    def pay(self):
        row=self.grid.selected()
        self.form('Pagamento da fatura',[
            ('account','Conta pagadora',None,self.choices('accounts')),('amount','Valor a pagar (R$)',currency_input(row['remaining_cents']),None),
            ('date','Data do pagamento',TODAY(),None)],
            lambda v:self.c.cards.pay(row['id'],v['account'],money(v['amount']),v['date']))

    def close(self):
        row=self.grid.selected()
        self.confirm('Fechar esta fatura e impedir novas compras neste período?',lambda:self.c.cards.close(row['id']))

    def history(self):
        row=self.grid.selected(); payments=self.c.cards.payments(row['id'])
        text='\n'.join(f"{date_br(p['occurred'])} • {brl(p['amount_cents'])} • operação #{p['id']}" for p in payments) or 'Nenhum pagamento registrado.'
        show_details(self,'Pagamentos • '+row['card'],text)


class CommitmentScreen(Screen):
    def __init__(self,parent,app):
        super().__init__(parent,app,'Compromissos','Checklist financeiro. Somente a confirmação de pagamento gera despesa e saída de caixa.')
        self.action('+ Compromisso',self.create,secondary=False)
        self.action('Marcar pago',self.pay,secondary=False)
        self.action('Editar / adiar',self.edit)
        self.action('Ignorar',self.ignore)
        self.action('Parar recorrência',self.stop)
        self.period=Period(self.body,lambda:self.app.guard(self.refresh))
        self.grid=Grid(self.body,[('due','Vencimento',110),('title','Compromisso',230),('amount','Valor',130),('account','Conta',150),('state','Estado',120),('recurring','Recorrência',100)])

    def refresh(self):
        self.grid.load(self.c.commitments.list(*self.period.get()),lambda r:[date_br(r['due']),r['title'],brl(r['amount_cents']),r['account'],LABELS[r['state']],'Mensal' if r['series_id'] else 'Única'])

    def create(self):
        self.form('Novo compromisso',[
            ('title','Descrição','',None),('amount','Valor (R$)','',None),('due','Vencimento',TODAY(),None),
            ('account','Conta pagadora',None,self.choices('accounts')),('category','Categoria',None,self.choices('categories','expense')),
            ('recurring','Recorrência',False,[('Uma vez',False),('Mensal',True)])],
            lambda v:self.c.commitments.create(v['title'],money(v['amount']),v['due'],v['account'],v['category'],v['recurring']))

    def pay(self):
        row=self.grid.selected()
        self.form('Confirmar pagamento',[
            ('date',f"Data do pagamento de {brl(row['amount_cents'])}",TODAY(),None)],
            lambda v:self.c.commitments.pay(row['id'],v['date']))

    def edit(self):
        row=self.grid.selected()
        self.form('Editar somente esta ocorrência',[
            ('title','Descrição',row['title'],None),('amount','Valor (R$)',currency_input(row['amount_cents']),None),
            ('due','Novo vencimento',row['due'],None)],
            lambda v:self.c.commitments.edit(row['id'],v['title'],money(v['amount']),v['due']))

    def ignore(self):
        row=self.grid.selected()
        self.confirm('Ignorar somente esta ocorrência, sem movimentar dinheiro?',lambda:self.c.commitments.ignore(row['id']))

    def stop(self):
        row=self.grid.selected()
        if not row['series_id']: raise ValueError('Este compromisso não é recorrente.')
        self.confirm('Parar a geração de novas ocorrências? As já existentes serão preservadas e podem ser ignoradas individualmente.',lambda:self.c.commitments.stop_series(row['series_id']))
