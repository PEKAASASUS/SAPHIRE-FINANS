from datetime import date

from safira.controller import Controller
from safira.dashboard_view import active_account_analytics


TODAY=date.today().isoformat()
START='2026-01-01'


def test_active_dashboard_excludes_archived_account_without_changing_history(tmp_path):
    app=Controller(tmp_path/'dashboard.sqlite')
    active=app.finance.account('Ativa','bank',10000,START)
    archived=app.finance.account('Arquivada','bank',20000,START)
    income=next(r['id'] for r in app.finance.catalogs('categories') if r['kind']=='income')
    expense=next(r['id'] for r in app.finance.catalogs('categories') if r['kind']=='expense')
    app.finance.movement(active,'income','Receita ativa',1000,TODAY,income)
    app.finance.movement(archived,'expense','Despesa arquivada',5000,TODAY,expense)
    app.commitments.create('Obrigação arquivada',500,TODAY,archived,expense)
    before=app.analytics.report(START,TODAY)
    app.finance.activate('accounts',archived,False)
    view=active_account_analytics(app)
    result=view.report(START,TODAY)
    assert result['available_cents']==11000
    assert result['income_cents']==1000
    assert result['expense_cents']==0
    assert result['cash_in_cents']==1000
    assert result['cash_out_cents']==0
    assert [r['description'] for r in result['operations']]==['Receita ativa']
    assert result['categories']=={}
    assert view.monthly()[-1]['cash']==11000
    assert view.forecast(TODAY)['projected_cents']==11000
    assert view.notifications()==[]
    after=app.analytics.report(START,TODAY)
    for key in ('income_cents','expense_cents','available_cents','operations','categories'):
        assert before[key]==after[key]
    app.finance.activate('accounts',active,False)
    empty=active_account_analytics(app).report(START,TODAY)
    assert empty['available_cents']==empty['income_cents']==empty['expense_cents']==0
    assert empty['operations']==[]


def test_active_dashboard_keeps_transfer_effect_on_remaining_account(tmp_path):
    app=Controller(tmp_path/'transfers.sqlite')
    a=app.finance.account('Ativa','bank',10000,START)
    b=app.finance.account('Arquivada','bank',0,START)
    app.finance.transfer(a,b,2500,TODAY)
    app.finance.activate('accounts',b,False)
    report=active_account_analytics(app).report(START,TODAY)
    assert report['available_cents']==7500
    assert report['cash_in_cents']==report['cash_out_cents']==0
    assert len(report['operations'])==1


def test_active_card_debt_keeps_payments_from_archived_funding_account(tmp_path):
    app=Controller(tmp_path/'cards.sqlite')
    owner=app.finance.account('Conta do cartão','bank',0,START)
    funding=app.finance.account('Pagadora','bank',10000,START)
    expense=next(r['id'] for r in app.finance.catalogs('categories') if r['kind']=='expense')
    card=app.cards.save('Crédito','credit',owner,100000,10,20)
    app.cards.purchase(card,'Compra',6000,START,expense)
    invoice=app.cards.invoices()[0]
    app.cards.pay(invoice['id'],funding,2000,'2026-01-20')
    app.finance.activate('accounts',funding,False)
    view=active_account_analytics(app)
    report=view.report(START,TODAY)
    assert report['expense_cents']==6000
    assert report['debt_cents']==4000
    assert sum(report['categories'].values())==6000
    app.finance.activate('accounts',owner,False)
    report=active_account_analytics(app).report(START,TODAY)
    assert report['debt_cents']==report['expense_cents']==0
