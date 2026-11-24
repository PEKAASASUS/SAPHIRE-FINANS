"""Additive planning features, using the existing financial writer and validators.

Independent feature migration leaves the original engine/schema version intact.
All financial configuration stays in the same SQLite file and its normal backups.
"""
from datetime import date, timedelta
from safira.domain import add_months, iso, cents, ValidationError
from safira.services import title
from safira.business_calendar import fifth_business_day


class FinancialPlanning:
    def __init__(self,controller):
        self.c=controller; self.store=controller.store
        self.migrate()

    def migrate(self):
        with self.store.transaction() as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS planning_migrations(version INTEGER PRIMARY KEY)')
            version=conn.execute('SELECT coalesce(max(version),0) FROM planning_migrations').fetchone()[0]
            if version>2:raise ValidationError('Planejamento criado por versão mais recente.')
            if version<1:
                statements=(
                    '''CREATE TABLE planning_budgets(month TEXT NOT NULL,category_id INTEGER NOT NULL REFERENCES categories(id),
                        amount_cents INTEGER NOT NULL CHECK(typeof(amount_cents)='integer' AND amount_cents>=0),
                        PRIMARY KEY(month,category_id))''',
                    '''CREATE TABLE planning_salaries(id INTEGER PRIMARY KEY,name TEXT NOT NULL,account_id INTEGER NOT NULL REFERENCES accounts(id),
                        category_id INTEGER NOT NULL REFERENCES categories(id),amount_cents INTEGER NOT NULL
                        CHECK(typeof(amount_cents)='integer' AND amount_cents>0),start_month TEXT NOT NULL,
                        active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)))''',
                    '''CREATE TABLE planning_salary_months(salary_id INTEGER NOT NULL REFERENCES planning_salaries(id),
                        month TEXT NOT NULL,operation_id INTEGER NOT NULL UNIQUE REFERENCES operations(id),PRIMARY KEY(salary_id,month))''',
                    '''CREATE TABLE planning_calendar(day TEXT PRIMARY KEY,working INTEGER NOT NULL CHECK(working IN (0,1)),note TEXT NOT NULL)''')
                for statement in statements:conn.execute(statement)
                conn.execute('INSERT INTO planning_migrations VALUES(1)')
            if version<2:
                conn.execute('''CREATE TABLE planning_budget_rules(month TEXT NOT NULL,
                    category_id INTEGER NOT NULL REFERENCES categories(id),
                    amount_cents INTEGER CHECK(amount_cents IS NULL OR (typeof(amount_cents)='integer' AND amount_cents>=0)),
                    PRIMARY KEY(month,category_id))''')
                current=date.today().strftime('%Y-%m')
                # Adopt the last known limit from this month forward, without
                # filling historical gaps in the old per-month reports.
                conn.execute('''INSERT INTO planning_budget_rules(month,category_id,amount_cents)
                    SELECT ?,b.category_id,b.amount_cents FROM planning_budgets b
                    WHERE b.month=(SELECT max(x.month) FROM planning_budgets x
                        WHERE x.category_id=b.category_id AND x.month<=?)''',(current,current))
                conn.execute('''INSERT INTO planning_budget_rules(month,category_id,amount_cents)
                    SELECT month,category_id,amount_cents FROM planning_budgets WHERE month>?''',(current,))
                conn.execute('INSERT INTO planning_migrations VALUES(2)')

    @staticmethod
    def month(value):
        value=str(value)
        try:
            day=date.fromisoformat(value+'-01')
            if day.strftime('%Y-%m')!=value:raise ValueError
        except ValueError:raise ValidationError('Informe o mês no formato MM/AAAA.') from None
        return value

    def calendar(self):
        return self.store.rows('SELECT * FROM planning_calendar ORDER BY day')

    def calendar_override(self,day,working,note):
        iso(day)
        with self.store.transaction() as conn:
            conn.execute('INSERT INTO planning_calendar VALUES(?,?,?) ON CONFLICT(day) DO UPDATE SET working=excluded.working,note=excluded.note',
                         (day,int(bool(working)),title(note)))
        # Existing monthly forecasts are preserved; adjust a pending occurrence explicitly.

    def budget(self,month,category_id,amount):
        month=self.month(month); cents(amount)
        if amount<0:raise ValidationError('Orçamento não pode ser negativo.')
        with self.store.transaction() as conn:
            self.c.finance._category(conn,category_id,'expense')
            # Replace this category's schedule from the selected month onward.
            conn.execute('DELETE FROM planning_budget_rules WHERE category_id=? AND month>=?',(category_id,month))
            conn.execute('INSERT INTO planning_budget_rules VALUES(?,?,?)',(month,category_id,amount))

    def remove_budget(self,month,category_id):
        with self.store.transaction() as conn:
            month=self.month(month)
            conn.execute('DELETE FROM planning_budget_rules WHERE category_id=? AND month>=?',(category_id,month))
            conn.execute('INSERT INTO planning_budget_rules VALUES(?,?,NULL)',(month,category_id))

    def comparison(self,month,analytics=None,until=None):
        month=self.month(month); start=month+'-01'
        end=(date.fromisoformat(add_months(start,1,1))-timedelta(days=1)).isoformat()
        if until:end=min(end,iso(until))
        # Key by category id, not label, and retain categories without budgets.
        engine=analytics or self.c.analytics
        report=engine.report(start,end)
        budgets=self.store.rows('''SELECT c.id,c.name,b.amount_cents FROM planning_budgets b
            JOIN categories c ON c.id=b.category_id WHERE b.month=?''',(month,))
        # Legacy monthly snapshots remain exact until a new recurring rule takes over.
        effective={r['id']:r for r in budgets}
        rules=self.store.rows('''SELECT c.id,c.name,b.amount_cents FROM planning_budget_rules b
            JOIN categories c ON c.id=b.category_id WHERE b.month=(
                SELECT max(r.month) FROM planning_budget_rules r WHERE r.category_id=b.category_id AND r.month<=?)''',(month,))
        for rule in rules:
            if rule['amount_cents'] is None:effective.pop(rule['id'],None)
            else:effective[rule['id']]=rule
        rows={r['id']:dict(id=r['id'],name=r['name'],planned=r['amount_cents'],actual=0) for r in effective.values()}
        # Engine already computes confirmed expenditure plus credit consumption by competence.
        categories={r['name']:r['id'] for r in self.c.finance.catalogs('categories') if r['kind']=='expense'}
        for name,amount in report['categories'].items():
            key=categories.get(name,'unclassified')
            rows.setdefault(key,dict(id=key,name=name,planned=None,actual=0))['actual']+=amount
        return sorted(rows.values(),key=lambda r:r['name'].casefold())

    def salaries(self):
        return self.store.rows('''SELECT s.*,a.name account,c.name category FROM planning_salaries s
            JOIN accounts a ON a.id=s.account_id JOIN categories c ON c.id=s.category_id ORDER BY s.active DESC,s.name''')

    def salary(self,name,account_id,category_id,amount,start_month):
        cents(amount,True); start_month=self.month(start_month)
        with self.store.transaction() as conn:
            self.c.finance._account(conn,account_id,start_month+'-28')
            self.c.finance._category(conn,category_id,'income')
            # Disallow duplicate active templates accidentally created by repeated clicks.
            if conn.execute('SELECT 1 FROM planning_salaries WHERE name=? AND account_id=? AND active=1',(title(name),account_id)).fetchone():
                raise ValidationError('Já existe uma receita recorrente ativa com este nome nesta conta.')
            identity=conn.execute('INSERT INTO planning_salaries(name,account_id,category_id,amount_cents,start_month) VALUES(?,?,?,?,?)',
                (title(name),account_id,category_id,amount,start_month)).lastrowid
        return identity

    def generate(self,until):
        limit=date.fromisoformat(iso(until)); overrides={r['day']:bool(r['working']) for r in self.calendar()}
        with self.store.transaction() as conn:
            salaries=conn.execute('''SELECT s.* FROM planning_salaries s JOIN accounts a ON a.id=s.account_id
                JOIN categories c ON c.id=s.category_id WHERE s.active=1 AND a.active=1 AND c.active=1''').fetchall()
            for s in salaries:
                start=date.fromisoformat(s['start_month']+'-01')
                months=(limit.year-start.year)*12+limit.month-start.month
                if months>1200:raise ValidationError('Horizonte máximo: 100 anos.')
                for n in range(max(0,months+1)):
                    month=add_months(start.isoformat(),n,1)[:7]
                    if conn.execute('SELECT 1 FROM planning_salary_months WHERE salary_id=? AND month=?',(s['id'],month)).fetchone():continue
                    y,m=map(int,month.split('-')); due=fifth_business_day(y,m,overrides)
                    if due>until:continue
                    account=conn.execute('SELECT opened FROM accounts WHERE id=?',(s['account_id'],)).fetchone()
                    if due<account['opened']:continue
                    operation=self.c.finance._write(conn,kind='income',description=s['name'],amount=s['amount_cents'],
                        occurred=due,competence=due,status='pending',category_id=s['category_id'],
                        entries=[(s['account_id'],s['amount_cents'])],token=f'planning-salary:{s["id"]}:{month}')
                    conn.execute('INSERT INTO planning_salary_months VALUES(?,?,?)',(s['id'],month,operation))

    def occurrences(self):
        return self.store.rows('''SELECT o.*,s.name salary,a.name account,m.month FROM planning_salary_months m
            JOIN planning_salaries s ON s.id=m.salary_id JOIN operations o ON o.id=m.operation_id
            JOIN accounts a ON a.id=s.account_id ORDER BY o.occurred,o.id''')

    def confirm_salary(self,operation_id,amount,received):
        row=self.store.one('''SELECT o.* FROM planning_salary_months m JOIN operations o ON o.id=m.operation_id WHERE o.id=?''',(operation_id,))
        if not row or row['status']!='pending':raise ValidationError('Selecione um recebimento pendente.')
        self.c.finance.edit_operation(operation_id,amount,row['description'],iso(received),row['competence'],'confirmed',received)

    def stop_salary(self,identity):
        with self.store.transaction() as conn:
            conn.execute('UPDATE planning_salaries SET active=0 WHERE id=?',(identity,))
            # Cancel future pending occurrences only; retain history and overdue receivables.
            ids=conn.execute('''SELECT o.id FROM planning_salary_months m JOIN operations o ON o.id=m.operation_id
                WHERE m.salary_id=? AND o.status='pending' AND o.occurred>=?''',(identity,date.today().isoformat())).fetchall()
            for row in ids:conn.execute("UPDATE operations SET status='cancelled' WHERE id=?",(row['id'],))


def planning_for(controller):
    # Revalidate extension after restoring an older backup in the same app session.
    return FinancialPlanning(controller)
