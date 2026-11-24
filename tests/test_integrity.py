from concurrent.futures import ThreadPoolExecutor
from datetime import date,timedelta
from pathlib import Path
import sqlite3
import pytest
from safira.controller import Controller
from safira.domain import ValidationError
from safira.infrastructure import Backup,InstanceLock
from test_finance import account,category,balance,TODAY,PAST


@pytest.fixture
def app(tmp_path): return Controller(tmp_path/'integrity.sqlite')


def test_concurrent_payment_exactly_once(app):
    a=account(app)
    k=app.commitments.create('Concorrente',15000,TODAY,a,category(app,'expense'))
    with ThreadPoolExecutor(max_workers=4) as executor:
        results=list(executor.map(lambda _:app.commitments.pay(k,TODAY),range(4)))
    assert len(set(results))==1
    assert balance(app,a)==85000
    assert len(app.store.rows('SELECT * FROM operations'))==1


def test_transfer_rollback_on_second_entry_failure(app):
    a=account(app); b=account(app,0,'Destino')
    with app.store.transaction() as conn:
        conn.execute(f'''CREATE TRIGGER fail_destination BEFORE INSERT ON entries WHEN NEW.account_id={b}
            BEGIN SELECT RAISE(ABORT,'test failure'); END''')
    with pytest.raises(sqlite3.IntegrityError): app.finance.transfer(a,b,30000,TODAY)
    assert balance(app,a)==100000 and balance(app,b)==0
    assert not app.store.rows('SELECT * FROM operations')


def test_edit_rollback(app):
    a=account(app)
    op=app.finance.movement(a,'expense','Original',1000,TODAY,category(app,'expense'))
    with pytest.raises(ValueError): app.finance.edit_operation(op,2000,'Original','invalid')
    assert balance(app,a)==99000
    assert app.store.get('operations',op)['amount_cents']==1000


def test_future_and_competence(app):
    a=account(app)
    future=(date.today()+timedelta(days=10)).isoformat()
    with pytest.raises(ValueError): app.finance.movement(a,'expense','Futuro',1000,future,category(app,'expense'))
    app.finance.movement(a,'expense','Pendente',1000,future,category(app,'expense'),status='pending')
    assert balance(app,a)==100000
    assert app.analytics.forecast(future)['projected_cents']==99000
    app.finance.movement(a,'expense','Competência anterior',2000,TODAY,category(app,'expense'),competence='2026-01-02')
    r=app.analytics.report(TODAY,TODAY)
    assert r['cash_out_cents']==2000
    if TODAY!='2026-01-02': assert r['expense_cents']==0


def test_filters_and_archival(app):
    a=account(app); b=account(app,0,'B')
    cat=category(app,'expense')
    app.finance.movement(a,'expense','Pesquisa única',1000,TODAY,cat)
    app.finance.movement(b,'income','Outra',1000,TODAY,category(app,'income'))
    assert len(app.finance.movements(PAST,TODAY,a,cat,'expense','única'))==1
    app.finance.activate('accounts',a,False)
    with pytest.raises(ValueError): app.finance.movement(a,'expense','Bloqueada',1000,TODAY,cat)
    assert balance(app,a)==99000


def test_opening_immutable_with_history(app):
    a=account(app)
    app.finance.movement(a,'expense','Histórico',100,TODAY,category(app,'expense'))
    with pytest.raises(ValueError): app.finance.account('Banco','bank',200000,PAST,a)
    app.finance.account('Banco renomeado','bank',100000,PAST,a)
    assert balance(app,a)==99900


def test_catalog_uniqueness_methods_no_credit(app):
    with pytest.raises(ValueError): app.finance.catalog('categories','salário','income')
    with pytest.raises(ValueError): app.finance.catalog('methods','Cartão de crédito')
    method=app.finance.catalog('methods','Meu método')
    app.finance.activate('methods',method,False)
    a=account(app)
    with pytest.raises(ValueError): app.finance.movement(a,'expense','Método inativo',100,TODAY,category(app,'expense'),method)


def test_card_limits_dates_and_cancel_guard(app):
    a=account(app); cat=category(app,'expense')
    c=app.cards.save('Crédito','credit',a,10000,10,20)
    with pytest.raises(ValueError): app.cards.purchase(c,'Excede',10001,'2026-01-01',cat)
    assert not app.cards.purchases()
    p=app.cards.purchase(c,'Válida',10000,'2026-01-01',cat)
    invoice=app.cards.invoices()[0]
    with pytest.raises(ValueError): app.cards.pay(invoice['id'],a,100,'2026-01-09')
    app.cards.pay(invoice['id'],a,1000,'2026-01-20')
    with pytest.raises(ValueError): app.cards.cancel(p)
    with pytest.raises(ValueError): app.finance.cancel_operation(app.cards.payments(invoice['id'])[0]['id'])
    assert balance(app,a)==99000


def test_closed_invoice_no_retroactive_purchase(app):
    a=account(app); cat=category(app,'expense')
    c=app.cards.save('Fechado','credit',a,100000,10,20)
    app.cards.purchase(c,'Primeira',1000,'2026-01-01',cat)
    i=app.cards.invoices()[0]; app.cards.close(i['id'])
    with pytest.raises(ValueError): app.cards.purchase(c,'Retroativa',1000,'2026-01-02',cat)
    assert len(app.cards.purchases())==1


def test_recurring_ignored_postponed_stop(app):
    a=account(app)
    k=app.commitments.create('Série',1000,'2026-01-31',a,category(app,'expense'),True)
    app.commitments.generate('2026-02-28')
    app.commitments.ignore(k)
    with pytest.raises(ValueError): app.commitments.pay(k,TODAY)
    row=app.store.get('commitments',k)
    app.commitments.stop_series(row['series_id'])
    app.commitments.generate('2026-12-31')
    assert len(app.store.rows('SELECT * FROM commitments'))==2


def test_paid_invoice_alert_resolves(app):
    a=account(app); c=app.cards.save('Alerta','credit',a,100000,10,20)
    app.cards.purchase(c,'Compra',10000,'2026-01-01',category(app,'expense'))
    assert len(app.analytics.notifications())==1
    i=app.cards.invoices()[0]
    app.cards.pay(i['id'],a,10000,'2026-01-20')
    assert app.analytics.notifications()==[]


def test_auth_throttle_persisted(app,monkeypatch):
    clock=[10000]
    monkeypatch.setattr('safira.security.time.time',lambda:clock[0])
    app.auth.setup('long-password-test','long-password-test')
    for _ in range(3):
        with pytest.raises(ValueError): app.auth.login('wrong')
    restarted=Controller(app.store.path)
    with pytest.raises(ValueError,match='Aguarde'): restarted.auth.login('long-password-test')
    assert restarted.store.one('SELECT failures FROM profile')['failures']==3
    clock[0]+=2
    restarted.auth.login('long-password-test')
    assert restarted.auth.authenticated


def test_instance_lock(app):
    with InstanceLock(app.store.path.parent):
        with pytest.raises(ValueError):
            with InstanceLock(app.store.path.parent): pass
    with InstanceLock(app.store.path.parent): pass


def test_backup_semantic_corruption(app,tmp_path):
    app.auth.setup('long-password-test','long-password-test')
    a=account(app); b=account(app,0,'B')
    op=app.finance.transfer(a,b,5000,TODAY)
    target=tmp_path/'semantic.sqlite'; app.backup.export(target)
    conn=sqlite3.connect(target)
    conn.execute('UPDATE entries SET delta_cents=1 WHERE delta_cents>0'); conn.commit(); conn.close()
    with pytest.raises(ValueError,match='inconsistentes'): app.backup.restore(target,True)
    assert balance(app,a)==95000


def test_idempotency_token_conflict(app):
    a=account(app); b=account(app,0,'Destino')
    first=app.finance.transfer(a,b,1000,TODAY,token='transfer-key')
    assert app.finance.transfer(a,b,1000,TODAY,token='transfer-key')==first
    with pytest.raises(ValueError): app.finance.transfer(a,b,2000,TODAY,token='transfer-key')
    assert balance(app,a)==99000


def test_account_evolution(app):
    a=account(app)
    app.finance.movement(a,'expense','Hoje',1000,TODAY,category(app,'expense'))
    points=app.finance.account_evolution(a)
    assert len(points)==6
    assert points[-1]['balance_cents']==99000


def test_malformed_migration_rolls_back(tmp_path):
    from safira.persistence import Store
    path=tmp_path/'old.sqlite'
    conn=sqlite3.connect(path)
    conn.execute('CREATE TABLE accounts(id INTEGER)'); conn.commit(); conn.close()
    with pytest.raises(sqlite3.OperationalError): Store(path)
    conn=sqlite3.connect(path)
    try:
        names={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert names=={'accounts'}
    finally: conn.close()


def test_unicode_duplicates(app):
    with pytest.raises(ValueError): app.finance.catalog('categories','SAÚDE','expense')
    account(app,name='Conta Ágil')
    with pytest.raises(ValueError): account(app,name='CONTA ÁGIL')


def test_distinct_confirmation_date(app):
    a=account(app)
    op=app.finance.movement(a,'expense','Confirmada depois',1000,'2026-01-02',category(app,'expense'),
        competence='2026-01-02',confirmed='2026-02-02')
    january=next(r for r in app.finance.balances('2026-01-31') if r['id']==a)
    assert january['balance_cents']==100000
    assert balance(app,a)==99000
    app.finance.edit_operation(op,2000,'Confirmada depois','2026-01-02','2026-01-02','confirmed','2026-02-02')
    assert app.analytics.report('2026-02-01','2026-02-28')['cash_out_cents']==2000
    assert app.analytics.report('2026-01-01','2026-01-31')['expense_cents']==2000
    app.finance.edit_operation(op,3000,'Alterar apenas valor','2026-01-02','2026-01-02')
    assert app.store.get('operations',op)['confirmed']=='2026-02-02'
