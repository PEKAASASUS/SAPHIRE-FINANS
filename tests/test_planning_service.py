from datetime import date,timedelta
from concurrent.futures import ThreadPoolExecutor
import pytest
from safira.controller import Controller
from safira.planning_service import FinancialPlanning
from safira.business_calendar import fifth_business_day,holidays
from safira.domain import ValidationError,add_months

TODAY=date.today().isoformat()

@pytest.fixture
def setup(tmp_path):
    c=Controller(tmp_path/'planning.sqlite')
    c.auth.setup('planning-synthetic-test','planning-synthetic-test')
    a=c.finance.account('Sintética','bank',10000,'2020-01-01')
    income=next(r['id'] for r in c.finance.catalogs('categories') if r['kind']=='income')
    expense=next(r['id'] for r in c.finance.catalogs('categories') if r['kind']=='expense')
    return c,FinancialPlanning(c),a,income,expense

@pytest.mark.parametrize('year,month,expected',[(2026,1,'2026-01-08'),(2026,4,'2026-04-08'),
    (2026,5,'2026-05-08'),(2026,11,'2026-11-09'),(2027,1,'2027-01-11'),(2027,10,'2027-10-08')])
def test_fifth_business_day_without_saturdays_and_local_holidays(year,month,expected):
    assert fifth_business_day(year,month)==expected
    assert date(year,10,4) in holidays(year)
    assert date(year,10,11) in holidays(year)


def test_calendar_exception(setup):
    c,p,a,i,e=setup
    p.calendar_override('2026-01-02',False,'Folga do empregador')
    assert fifth_business_day(2026,1,{r['day']:bool(r['working']) for r in p.calendar()})=='2026-01-09'
    p.calendar_override('2026-01-02',True,'Expediente normal')
    assert len(p.calendar())==1
    assert fifth_business_day(2026,1,{r['day']:bool(r['working']) for r in p.calendar()})=='2026-01-08'


def test_salary_generation_idempotent_forecast_and_confirmation(setup):
    c,p,a,i,e=setup
    p.salary('Salário',a,i,150000,'2026-01')
    p.generate('2026-03-31');p.generate('2026-03-31')
    rows=p.occurrences();assert len(rows)==3
    assert all(r['status']=='pending' for r in rows)
    assert c.finance.balances()[0]['balance_cents']==10000
    forecast=c.analytics.forecast('2026-01-31',today='2026-01-01')
    assert forecast['projected_cents']==160000
    first=rows[0]
    p.confirm_salary(first['id'],149000,'2026-01-08')
    assert c.finance.balances()[0]['balance_cents']==159000
    assert c.analytics.forecast('2026-01-31',today='2026-01-08')['projected_cents']==159000
    p.generate('2026-03-31');assert len(p.occurrences())==3
    assert p.occurrences()[0]['amount_cents']==149000
    with pytest.raises(ValidationError):p.confirm_salary(first['id'],149000,'2026-01-08')


def test_cancelled_occurrence_is_not_recreated_and_archived_account_not_generated(setup):
    c,p,a,i,e=setup
    p.salary('Salário',a,i,10000,'2026-01');p.generate('2026-01-31')
    row=p.occurrences()[0];c.finance.cancel_operation(row['id'])
    p.generate('2026-01-31');assert len(p.occurrences())==1
    assert p.occurrences()[0]['status']=='cancelled'
    c.finance.activate('accounts',a,False);p.generate('2026-02-28')
    assert len(p.occurrences())==1


def test_concurrent_generation_is_unique(setup):
    c,p,a,i,e=setup
    p.salary('Salário',a,i,10000,'2026-01')
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _:p.generate('2026-12-31'),range(2)))
    assert len(p.occurrences())==12


def test_stop_cancels_only_future_pending(setup):
    c,p,a,i,e=setup
    month=TODAY[:7];s=p.salary('Salário',a,i,10000,month)
    end=add_months(TODAY,3,28);p.generate(end)
    p.stop_salary(s);p.generate(end)
    for row in p.occurrences():
        assert row['status']==('cancelled' if row['occurred']>=TODAY else 'pending')


def test_budget_comparison_confirmation_competence_credit_and_no_double_count(setup):
    c,p,a,i,e=setup
    p.budget('2026-01',e,5000)
    c.finance.movement(a,'expense','Pendente',900,'2026-01-02',e,status='pending')
    c.finance.movement(a,'expense','Compra',2000,'2026-01-02',e)
    c.finance.movement(a,'expense','Outro mês',3000,'2026-02-01',e)
    card=c.cards.save('Sintético','credit',a,100000,10,20)
    c.cards.purchase(card,'Crédito',1000,'2026-01-02',e)
    before=c.analytics.forecast('2026-01-31',today='2026-01-01')['projected_cents']
    row=p.comparison('2026-01')[0]
    assert (row['planned'],row['actual'])==(5000,3000)
    p.budget('2026-01',e,0)
    assert p.comparison('2026-01')[0]['planned']==0
    assert c.analytics.forecast('2026-01-31',today='2026-01-01')['projected_cents']==before
    p.remove_budget('2026-01',e)
    assert p.comparison('2026-01')[0]['planned'] is None
    assert p.comparison('2026-01',until='2026-01-01')==[]
    with pytest.raises(ValueError):p.budget('2026-01',i,500)
    with pytest.raises(ValueError):p.budget('2026-01',e,1.5)


def test_migration_preserves_core_and_backup_roundtrip(setup,tmp_path):
    c,p,a,i,e=setup
    p.salary('Salário',a,i,12300,'2026-01');p.generate('2026-01-31');p.budget('2026-01',e,10000)
    p.calendar_override('2027-01-02',False,'Exceção sintética')
    FinancialPlanning(c)
    assert c.store.one('SELECT max(version) v FROM schema_migrations')['v']==1
    backup=tmp_path/'backup.sqlite';c.backup.export(backup)
    p.budget('2026-01',e,99900)
    c.backup.restore(backup,True)
    p=FinancialPlanning(c)
    assert p.comparison('2026-01')[0]['planned']==10000
    assert len(p.salaries())==len(p.occurrences())==len(p.calendar())==1
    assert c.store.rows('PRAGMA foreign_key_check')==[]


def test_restore_legacy_backup_recreates_empty_extension(setup,tmp_path):
    c,p,a,i,e=setup
    legacy=Controller(tmp_path/'legacy.sqlite')
    legacy.auth.setup('legacy-synthetic-profile','legacy-synthetic-profile')
    snapshot=tmp_path/'legacy-backup.sqlite';legacy.backup.export(snapshot)
    p.salary('Salário',a,i,12300,'2026-01');p.generate('2026-01-31')
    c.backup.restore(snapshot,True)
    p=FinancialPlanning(c)
    assert p.salaries()==p.occurrences()==p.calendar()==[]
    assert c.store.rows('PRAGMA foreign_key_check')==[]


def test_budget_realized_respects_active_account_scope(setup):
    from safira.dashboard_view import active_account_analytics
    c,p,a,i,e=setup
    other=c.finance.account('Arquivada','bank',10000,'2020-01-01')
    c.finance.movement(a,'expense','Ativa',1000,'2026-01-02',e)
    c.finance.movement(other,'expense','Arquivada',3000,'2026-01-02',e)
    p.budget('2026-01',e,5000)
    c.finance.activate('accounts',other,False)
    assert p.comparison('2026-01')[0]['actual']==4000
    scoped=p.comparison('2026-01',active_account_analytics(c))[0]
    assert scoped['planned']==5000 and scoped['actual']==1000


def test_fixed_budget_effective_history_and_removal(setup):
    c,p,a,i,e=setup
    p.budget('2026-01',e,50000)
    assert p.comparison('2025-12')==[]
    assert p.comparison('2026-02')[0]['planned']==50000
    assert p.comparison('2027-12')[0]['planned']==50000
    p.budget('2026-04',e,65000)
    assert p.comparison('2026-03')[0]['planned']==50000
    assert p.comparison('2026-04')[0]['planned']==65000
    assert p.comparison('2027-01')[0]['planned']==65000
    p.budget('2026-06',e,0)
    assert p.comparison('2026-05')[0]['planned']==65000
    assert p.comparison('2026-07')[0]['planned']==0
    p.remove_budget('2026-08',e)
    assert p.comparison('2026-07')[0]['planned']==0
    assert p.comparison('2026-08')==p.comparison('2027-01')==[]
    p.budget('2026-10',e,70000)
    assert p.comparison('2026-09')==[]
    assert p.comparison('2026-12')[0]['planned']==70000
    # A new change replaces any future schedule from that month onward.
    p.budget('2026-04',e,55000)
    assert p.comparison('2026-03')[0]['planned']==50000
    assert p.comparison('2026-12')[0]['planned']==55000


def test_monthly_budget_migration_preserves_past_reports_and_adopts_future(setup):
    c,p,a,i,e=setup
    month=TODAY[:7]
    old=add_months(TODAY,-3,1)[:7];gap=add_months(TODAY,-2,1)[:7]
    recent=add_months(TODAY,-1,1)[:7];future=add_months(TODAY,2,1)[:7]
    with c.store.transaction() as conn:
        conn.execute('DROP TABLE planning_budget_rules')
        conn.execute('DELETE FROM planning_migrations WHERE version=2')
        conn.executemany('INSERT INTO planning_budgets VALUES(?,?,?)',[(old,e,10000),(recent,e,20000),(future,e,30000)])
    p=FinancialPlanning(c)
    assert p.comparison(old)[0]['planned']==10000
    assert p.comparison(gap)==[]
    assert p.comparison(recent)[0]['planned']==20000
    assert p.comparison(month)[0]['planned']==20000
    assert p.comparison(future)[0]['planned']==30000
    p.budget(month,e,25000)
    assert p.comparison(old)[0]['planned']==10000
    assert p.comparison(gap)==[]
    assert p.comparison(recent)[0]['planned']==20000
    assert p.comparison(future)[0]['planned']==25000
    FinancialPlanning(c)
    assert c.store.one('SELECT max(version) v FROM planning_migrations')['v']==2
