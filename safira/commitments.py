from datetime import date
from safira.domain import ValidationError,cents,iso,add_months
from safira.services import title


class Commitments:
    def __init__(self,store,finance):
        self.store,self.finance=store,finance

    def create(self,name,amount,due,account_id,category_id,recurring=False):
        cents(amount,True); iso(due)
        with self.store.transaction() as conn:
            self.finance._account(conn,account_id,due)
            self.finance._category(conn,category_id,'expense')
            series=None
            if recurring:
                series=conn.execute('INSERT INTO series(title,amount_cents,account_id,category_id,start) VALUES (?,?,?,?,?)',
                    (title(name),amount,account_id,category_id,due)).lastrowid
            identity=conn.execute('''INSERT INTO commitments(series_id,occurrence,title,amount_cents,account_id,category_id,due,original_due)
                VALUES (?,?,?,?,?,?,?,?)''',(series,due[:7],title(name),amount,account_id,category_id,due,due)).lastrowid
            return identity

    def generate(self,until):
        iso(until)
        with self.store.transaction() as conn:
            for series in conn.execute('SELECT * FROM series WHERE active=1').fetchall():
                start=date.fromisoformat(series['start'])
                limit=date.fromisoformat(until)
                months=(limit.year-start.year)*12+limit.month-start.month
                if months>1200:
                    raise ValidationError('Horizonte máximo de recorrência: 100 anos.')
                for n in range(max(0,months+1)):
                    due=add_months(series['start'],n,start.day)
                    if due>until:
                        continue
                    conn.execute('''INSERT OR IGNORE INTO commitments(series_id,occurrence,title,amount_cents,account_id,category_id,due,original_due)
                        VALUES (?,?,?,?,?,?,?,?)''',(series['id'],due[:7],series['title'],series['amount_cents'],series['account_id'],series['category_id'],due,due))

    def list(self,start,end):
        iso(start); iso(end)
        self.generate(end)
        return self.store.rows('''SELECT k.*,a.name account,c.name category FROM commitments k
            JOIN accounts a ON a.id=k.account_id JOIN categories c ON c.id=k.category_id
            WHERE k.due BETWEEN ? AND ? ORDER BY k.due,k.id''',(start,end))

    def edit(self,identity,name,amount,due):
        cents(amount,True); iso(due)
        with self.store.transaction() as conn:
            old=self.store.get('commitments',identity,conn)
            if old['state'] in ('paid','ignored'):
                raise ValidationError('Ocorrência concluída é imutável.')
            conn.execute('UPDATE commitments SET title=?,amount_cents=?,due=?,state=? WHERE id=?',
                (title(name),amount,due,'postponed' if due!=old['original_due'] else 'pending',identity))

    def ignore(self,identity):
        with self.store.transaction() as conn:
            old=self.store.get('commitments',identity,conn)
            if old['state']=='paid':
                raise ValidationError('Compromisso já pago.')
            conn.execute("UPDATE commitments SET state='ignored' WHERE id=?",(identity,))

    def stop_series(self,identity):
        with self.store.transaction() as conn:
            self.store.get('series',identity,conn)
            conn.execute('UPDATE series SET active=0 WHERE id=?',(identity,))

    def pay(self,identity,paid):
        iso(paid)
        with self.store.transaction() as conn:
            old=self.store.get('commitments',identity,conn)
            if old['state']=='paid':
                return old['operation_id']
            if old['state']=='ignored':
                raise ValidationError('Ocorrência ignorada não pode ser paga.')
            operation=self.finance._write(conn,kind='expense',description=old['title'],amount=old['amount_cents'],
                occurred=paid,competence=old['original_due'],category_id=old['category_id'],
                entries=[(old['account_id'],-old['amount_cents'])],source='commitment',token=f'commitment:{identity}')
            conn.execute("UPDATE commitments SET state='paid',operation_id=? WHERE id=?",(operation,identity))
            return operation
