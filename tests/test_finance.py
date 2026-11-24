from datetime import date
import sqlite3
import pytest
from safira.controller import Controller
from safira.domain import money,brl,ValidationError,split_installments,invoice_dates

TODAY=date.today().isoformat()
PAST='2026-01-01'


@pytest.fixture
def app(tmp_path):
    return Controller(tmp_path/'safira.sqlite')


def category(app,kind):
    return next(r['id'] for r in app.finance.catalogs('categories',1) if r['kind']==kind)


def account(app,amount=100000,name='Banco',kind='bank'):
    return app.finance.account(name,kind,amount,PAST)


def balance(app,identity):
    return next(r['balance_cents'] for r in app.finance.balances() if r['id']==identity)


def report(app):
    return app.analytics.report('2026-01-01',TODAY)


@pytest.mark.parametrize('raw,expected',[('R$ 1.250,90',125090),('1234.56',123456),('-150,00',-15000),('0',0),('1.000,00',100000)])
def test_money(raw,expected):
    assert money(raw)==expected


@pytest.mark.parametrize('raw',['abc','1.23,45','',1.25,'NaN','1,234','--1'])
def test_invalid_money(raw):
    with pytest.raises(ValidationError): money(raw)


def test_initial_not_income(app):
    a=account(app)
    assert balance(app,a)==100000
    assert report(app)['income_cents']==0


def test_income_expense(app):
    a=account(app)
    app.finance.movement(a,'income','Salário',50000,TODAY,category(app,'income'))
    app.finance.movement(a,'expense','Compra',20000,TODAY,category(app,'expense'))
    assert balance(app,a)==130000
    assert report(app)['result_cents']==30000


def test_transfer_atomic_and_cancel(app):
    a=account(app); b=account(app,50000,'Carteira','wallet')
    op=app.finance.transfer(a,b,30000,TODAY)
    assert (balance(app,a),balance(app,b))==(70000,80000)
    assert report(app)['income_cents']==report(app)['expense_cents']==0
    app.finance.edit_operation(op,10000,'Ajuste',TODAY)
    assert balance(app,a)==90000
    app.finance.cancel_operation(op); app.finance.cancel_operation(op)
    assert balance(app,a)==100000
    with pytest.raises(ValueError): app.finance.transfer(a,a,10,TODAY)
    with pytest.raises(ValueError): app.finance.transfer(a,999,10,TODAY)
    assert balance(app,a)==100000


def test_commitment_idempotent(app):
    a=account(app)
    k=app.commitments.create('Internet',15000,TODAY,a,category(app,'expense'))
    assert balance(app,a)==100000
    first=app.commitments.pay(k,TODAY)
    assert app.commitments.pay(k,TODAY)==first
    assert balance(app,a)==85000
    assert not app.analytics.notifications()


def test_credit_and_partial_payment(app):
    a=account(app,200000)
    c=app.cards.save('Crédito','credit',a,100000,10,20)
    app.cards.purchase(c,'Compra',60000,'2026-01-01',category(app,'expense'))
    invoice=app.cards.invoices()[0]
    assert balance(app,a)==200000
    assert report(app)['expense_cents']==60000
    app.cards.pay(invoice['id'],a,20000,'2026-01-20',token='partial')
    app.cards.pay(invoice['id'],a,20000,'2026-01-20',token='partial')
    assert balance(app,a)==180000
    app.cards.pay(invoice['id'],a,40000,'2026-01-21')
    assert balance(app,a)==140000
    assert report(app)['expense_cents']==60000
    assert app.cards.outstanding(c)==0
    with pytest.raises(ValueError): app.cards.pay(invoice['id'],a,1,TODAY)


def test_installments_and_closed_dates(app):
    a=account(app); c=app.cards.save('Visa','credit',a,200000,10,20)
    p=app.cards.purchase(c,'Compra',60001,'2026-01-10',category(app,'expense'),3,token='same')
    assert app.cards.purchase(c,'Compra',60001,'2026-01-10',category(app,'expense'),3,token='same')==p
    rows=app.store.rows('SELECT * FROM installments WHERE purchase_id=? ORDER BY number',(p,))
    assert [r['amount_cents'] for r in rows]==[20001,20000,20000]
    assert [r['competence'] for r in rows]==['2026-02-20','2026-03-20','2026-04-20']
    app.cards.save('Visa','credit',a,200000,15,25,identity=c)
    assert app.cards.invoices()[0]['due']=='2026-02-20'


def test_categories_history_and_edit_guard(app):
    a=account(app); cat=category(app,'expense')
    app.finance.movement(a,'expense','Comida',100,TODAY,cat)
    app.finance.activate('categories',cat,False)
    assert cat not in [c['id'] for c in app.finance.catalogs('categories',1)]
    assert app.finance.movements(PAST,TODAY)[0]['category']
    with pytest.raises(ValueError): app.finance.catalog('categories','Novo','expense',cat)
    with pytest.raises(ValueError): app.finance.movement(a,'expense','Outro',100,TODAY,cat)
    app.finance.activate('categories',cat,True)
    assert app.store.get('categories',cat)['active']==1


def test_edit_cancel_expense(app):
    a=account(app)
    op=app.finance.movement(a,'expense','Inicial',10000,TODAY,category(app,'expense'))
    app.finance.edit_operation(op,15000,'Atualizada',TODAY)
    assert balance(app,a)==85000
    app.finance.cancel_operation(op); app.finance.cancel_operation(op)
    assert balance(app,a)==100000


def test_backup_restore_and_restart(app,tmp_path):
    app.auth.setup('senha-segura-123','senha-segura-123')
    a=account(app); b=account(app,0,'Carteira','wallet')
    app.finance.transfer(a,b,10000,TODAY)
    app.commitments.create('Mensal',1000,'2026-01-31',a,category(app,'expense'),True)
    app.commitments.generate('2026-03-31')
    c=app.cards.save('Card','credit',a,100000,10,20)
    app.cards.purchase(c,'Parcela',60000,'2026-01-01',category(app,'expense'),3)
    before=report(app)
    backup=tmp_path/'backup.sqlite'
    app.backup.export(backup)
    app.finance.movement(a,'expense','Depois',1000,TODAY,category(app,'expense'))
    with pytest.raises(ValueError): app.backup.restore(backup)
    safety=app.backup.restore(backup,True)
    assert safety.is_file()
    new=Controller(app.store.path)
    assert report(new)==before
    count=len(new.commitments.list('2026-01-01','2026-03-31'))
    new.commitments.generate('2026-03-31')
    assert len(new.commitments.list('2026-01-01','2026-03-31'))==count
    assert new.store.rows('PRAGMA foreign_key_check')==[]


def test_pending_forecast_and_archived_assets(app):
    a=account(app)
    op=app.finance.movement(a,'income','Prevista',5000,TODAY,category(app,'income'),status='pending')
    k=app.commitments.create('Pendente',15000,TODAY,a,category(app,'expense'))
    assert app.analytics.forecast(TODAY)['projected_cents']==90000
    assert balance(app,a)==100000
    app.commitments.pay(k,TODAY)
    assert app.analytics.forecast(TODAY)['projected_cents']==90000
    app.finance.activate('accounts',a,False)
    assert report(app)['available_cents']==85000


def test_recurrence_month_end(app):
    a=account(app)
    app.commitments.create('Mensal',1000,'2026-01-31',a,category(app,'expense'),True)
    rows=app.commitments.list('2026-01-01','2026-03-31')
    assert [r['due'] for r in rows]==['2026-01-31','2026-02-28','2026-03-31']
    app.commitments.edit(rows[1]['id'],'Adiado',1200,'2026-03-02')
    assert app.store.get('commitments',rows[0]['id'])['due']=='2026-01-31'


def test_debit_cancel_and_investments(app):
    a=account(app); cat=category(app,'expense')
    c=app.cards.save('Débito','debit',a,0,1,10)
    p=app.cards.purchase(c,'Débito',10000,TODAY,cat)
    assert balance(app,a)==90000
    app.cards.cancel(p)
    assert balance(app,a)==100000
    b=account(app,50000,'Corretora','brokerage')
    position=app.finance.position(b,'Tesouro',0,0)
    app.finance.invest(position,10000,TODAY)
    assert balance(app,b)==40000
    assert report(app)['gross_cents']==150000
    assert report(app)['expense_cents']==0


def test_auth_change_and_failures(app):
    with pytest.raises(ValueError): app.auth.setup('curta','curta')
    app.auth.setup('uma-senha-forte','uma-senha-forte')
    app.auth.lock()
    with pytest.raises(ValueError): app.auth.login('errada')
    app.auth.login('uma-senha-forte')
    app.auth.change('uma-senha-forte','outra-senha-forte','outra-senha-forte')
    with pytest.raises(ValueError): app.auth.login('uma-senha-forte')
    app.auth.login('outra-senha-forte')
    assert app.auth.authenticated


def test_migration_reentry_and_constraints(app):
    account(app)
    app.store.migrate()
    assert len(app.finance.balances())==1
    with pytest.raises(sqlite3.IntegrityError):
        with app.store.transaction() as conn:
            conn.execute("INSERT INTO entries(operation_id,account_id,delta_cents) VALUES (999,999,1)")


def test_pdf(app,tmp_path):
    from safira.reports import export_pdf
    account(app)
    pdf=export_pdf(tmp_path/'report.pdf',report(app),[],[])
    assert pdf.read_bytes().startswith(b'%PDF')


def test_invalid_restore_preserves_data(app,tmp_path):
    a=account(app)
    bad=tmp_path/'bad.sqlite'; bad.write_bytes(b'invalid')
    with pytest.raises(ValueError): app.backup.restore(bad,True)
    assert balance(app,a)==100000


def test_calendar_and_split():
    assert split_installments(60000,3)==[20000]*3
    assert invoice_dates('2026-01-31',31,5)==('2026-02-28','2026-03-05')
    assert brl(-123456)=='-R$ 1.234,56'
