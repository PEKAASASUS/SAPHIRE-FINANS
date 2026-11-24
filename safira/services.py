"""Application cases. Every composite change is one database transaction."""
from datetime import date
from uuid import uuid4
import unicodedata
from safira.domain import ValidationError, cents, iso


def title(value):
    value = unicodedata.normalize('NFKC',value.strip())
    if not value or len(value) > 180:
        raise ValidationError('Nome/descrição obrigatório, até 180 caracteres.')
    return value


def unique_name(conn,table,name,kind=None,identity=None):
    if table not in ('accounts','categories','methods','cards'):
        raise ValidationError('Cadastro inválido.')
    name=title(name)
    for row in conn.execute(f'SELECT * FROM {table}'):
        if row['id']==identity or (kind and row['kind']!=kind):
            continue
        if title(row['name']).casefold()==name.casefold():
            raise ValidationError('Já existe um cadastro com este nome e tipo.')
    return name


class Finance:
    def __init__(self, store):
        self.store = store

    def account(self, name, kind, initial=0, opened=None, identity=None):
        cents(initial)
        if kind not in ('bank','wallet','reserve','brokerage'):
            raise ValidationError('Tipo de conta inválido.')
        opened = iso(opened or date.today().isoformat())
        with self.store.transaction() as conn:
            name=unique_name(conn,'accounts',name,identity=identity)
            if identity:
                old = self.store.get('accounts', identity, conn)
                if conn.execute('SELECT 1 FROM entries WHERE account_id=?', (identity,)).fetchone():
                    if (initial,opened,kind) != (old['initial_cents'],old['opened'],old['kind']):
                        raise ValidationError('Com histórico, saldo inicial, abertura e tipo são imutáveis.')
                if conn.execute('SELECT 1 FROM positions WHERE account_id=?',(identity,)).fetchone() and kind != 'brokerage':
                    raise ValidationError('Conta com investimentos deve permanecer corretora.')
                conn.execute('UPDATE accounts SET name=?,kind=?,initial_cents=?,opened=? WHERE id=?', (title(name),kind,initial,opened,identity))
                return identity
            return conn.execute('INSERT INTO accounts(name,kind,initial_cents,opened) VALUES (?,?,?,?)',(title(name),kind,initial,opened)).lastrowid

    def catalog(self, table, name, kind=None, identity=None):
        if table not in ('categories','methods'):
            raise ValidationError('Cadastro inválido.')
        if table == 'categories' and kind not in ('income','expense'):
            raise ValidationError('Tipo inválido.')
        if table == 'methods' and any(w in name.casefold() for w in ('crédito','credito','cartão','cartao')):
            raise ValidationError('Use o módulo de cartões para compras no cartão.')
        with self.store.transaction() as conn:
            name=unique_name(conn,table,name,kind if table=='categories' else None,identity)
            if identity:
                old = self.store.get(table,identity,conn)
                if old['standard']:
                    raise ValidationError('Padrões somente podem ser desativados ou reativados.')
                if table == 'categories' and old['kind'] != kind:
                    raise ValidationError('O tipo de categoria existente é imutável.')
                conn.execute(f'UPDATE {table} SET name=? WHERE id=?',(title(name),identity))
                return identity
            if table == 'categories':
                return conn.execute('INSERT INTO categories(name,kind) VALUES (?,?)',(title(name),kind)).lastrowid
            return conn.execute('INSERT INTO methods(name) VALUES (?)',(title(name),)).lastrowid

    def activate(self, table, identity, active):
        if table not in ('accounts','categories','methods','cards'):
            raise ValidationError('Cadastro inválido.')
        with self.store.transaction() as conn:
            self.store.get(table,identity,conn)
            conn.execute(f'UPDATE {table} SET active=? WHERE id=?',(int(bool(active)),identity))

    def _account(self, conn, identity, occurred):
        account = self.store.get('accounts',identity,conn)
        if not account['active']:
            raise ValidationError('Conta arquivada. Reative para registrar operações.')
        if occurred < account['opened']:
            raise ValidationError('Data anterior à abertura da conta.')
        return account

    def _category(self, conn, identity, kind):
        category = self.store.get('categories',identity,conn)
        if not category['active'] or category['kind'] != kind:
            raise ValidationError('Categoria inativa ou incompatível com a operação.')

    def _write(self, conn, *, kind, description, amount, occurred, competence=None,
               confirmed=None, status='confirmed', category_id=None, method_id=None,
               entries, source='manual', token=None):
        token = token or str(uuid4())
        existing = conn.execute('SELECT * FROM operations WHERE token=?',(token,)).fetchone()
        if existing:
            actual_entries=sorted((r['account_id'],r['delta_cents']) for r in conn.execute('SELECT account_id,delta_cents FROM entries WHERE operation_id=?',(existing['id'],)))
            if ((existing['kind'],existing['amount_cents'],existing['description'],existing['occurred'],existing['competence'],existing['status'],existing['category_id'],existing['method_id'])
                != (kind,amount,title(description),occurred,competence or occurred,status,category_id,method_id) or actual_entries!=sorted(entries)):
                raise ValidationError('Chave de operação já usada com outros dados.')
            return existing['id']
        cents(amount,True)
        occurred = iso(occurred)
        competence = iso(competence or occurred)
        if status not in ('pending','confirmed'):
            raise ValidationError('Estado inválido.')
        confirmed = iso(confirmed or occurred) if status == 'confirmed' else None
        if status == 'confirmed' and confirmed<occurred:
            raise ValidationError('Confirmação não pode ser anterior à operação.')
        if status == 'confirmed' and (occurred > date.today().isoformat() or confirmed > date.today().isoformat()):
            raise ValidationError('Eventos futuros devem permanecer pendentes.')
        for account_id, delta in entries:
            self._account(conn,account_id,occurred)
            cents(delta)
        if kind in ('income','expense'):
            self._category(conn,category_id,kind)
        if method_id and not self.store.get('methods',method_id,conn)['active']:
            raise ValidationError('Método desativado.')
        cursor = conn.execute('''INSERT INTO operations(token,kind,description,amount_cents,occurred,
            competence,confirmed,status,category_id,method_id,source) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (token,kind,title(description),amount,occurred,competence,confirmed,status,category_id,method_id,source))
        identity = cursor.lastrowid
        conn.executemany('INSERT INTO entries(operation_id,account_id,delta_cents) VALUES (?,?,?)',[(identity,a,d) for a,d in entries])
        return identity

    def movement(self, account_id, kind, description, amount, occurred, category_id,
                 method_id=None, status='confirmed', competence=None, token=None,confirmed=None):
        if kind not in ('income','expense'):
            raise ValidationError('Use o módulo de transferências/cartões.')
        with self.store.transaction() as conn:
            return self._write(conn,kind=kind,description=description,amount=amount,occurred=occurred,
                competence=competence,confirmed=confirmed,status=status,category_id=category_id,method_id=method_id,
                entries=[(account_id,amount if kind=='income' else -amount)],token=token)

    def transfer(self, origin, destination, amount, occurred, description='Transferência', token=None):
        if origin == destination:
            raise ValidationError('Origem e destino devem ser diferentes.')
        with self.store.transaction() as conn:
            return self._write(conn,kind='transfer',description=description,amount=amount,occurred=occurred,
                entries=[(origin,-amount),(destination,amount)],token=token)

    def edit_operation(self, identity, amount, description, occurred, competence=None, status='confirmed',confirmed=None):
        cents(amount,True)
        with self.store.transaction() as conn:
            old = self.store.get('operations',identity,conn)
            if old['source'] != 'manual' or old['kind'] not in ('income','expense','transfer') or old['status']=='cancelled':
                raise ValidationError('Edite operações vinculadas no módulo de origem; canceladas são imutáveis.')
            if confirmed is None and status=='confirmed':
                confirmed=old['confirmed']
            rows = conn.execute('SELECT account_id,delta_cents FROM entries WHERE operation_id=?',(identity,)).fetchall()
            conn.execute('DELETE FROM entries WHERE operation_id=?',(identity,))
            # Reuse the same validator and preserve operation identity and token.
            temp = self._write(conn,kind=old['kind'],description=description,amount=amount,occurred=occurred,
                competence=competence,confirmed=confirmed,status=status,category_id=old['category_id'],method_id=old['method_id'],
                entries=[(r['account_id'],amount if r['delta_cents']>0 else -amount) for r in rows])
            updated = self.store.get('operations',temp,conn)
            conn.execute('UPDATE operations SET description=?,amount_cents=?,occurred=?,competence=?,confirmed=?,status=? WHERE id=?',
                (updated['description'],amount,updated['occurred'],updated['competence'],updated['confirmed'],status,identity))
            conn.execute('UPDATE entries SET operation_id=? WHERE operation_id=?',(identity,temp))
            conn.execute('DELETE FROM operations WHERE id=?',(temp,))

    def cancel_operation(self, identity):
        with self.store.transaction() as conn:
            old = self.store.get('operations',identity,conn)
            if old['source'] != 'manual':
                raise ValidationError('Operação vinculada: utilize o módulo de origem.')
            conn.execute("UPDATE operations SET status='cancelled' WHERE id=?",(identity,))

    def balances(self, as_of=None):
        as_of = iso(as_of or date.today().isoformat())
        return self.store.rows('''SELECT a.*, CASE WHEN a.opened<=? THEN a.initial_cents ELSE 0 END +
            coalesce((SELECT sum(e.delta_cents) FROM entries e JOIN operations o ON o.id=e.operation_id
            WHERE e.account_id=a.id AND o.status='confirmed' AND o.confirmed<=?),0) balance_cents,
            coalesce((SELECT sum(value_cents) FROM positions p WHERE p.account_id=a.id AND p.active=1),0) invested_cents
            FROM accounts a ORDER BY a.name''',(as_of,as_of))

    def movements(self, start, end, account_id=None, category_id=None, kind=None, search=''):
        start,end=iso(start),iso(end)
        if start>end:
            raise ValidationError('Período invertido.')
        return self.store.rows('''SELECT o.*, c.name category, m.name method,
            (SELECT group_concat(a.name, ' → ') FROM entries e JOIN accounts a ON a.id=e.account_id WHERE e.operation_id=o.id) accounts
            FROM operations o LEFT JOIN categories c ON c.id=o.category_id LEFT JOIN methods m ON m.id=o.method_id
            WHERE o.occurred BETWEEN ? AND ? AND (? IS NULL OR o.category_id=?)
            AND (? IS NULL OR o.kind=?) AND instr(lower(o.description),lower(?))>0
            AND (? IS NULL OR EXISTS(SELECT 1 FROM entries e WHERE e.operation_id=o.id AND e.account_id=?))
            ORDER BY o.occurred DESC,o.id DESC''',(start,end,category_id,category_id,kind,kind,search,account_id,account_id))

    def catalogs(self, table, active=None):
        if table not in ('accounts','categories','methods','cards','positions'):
            raise ValidationError('Cadastro inválido.')
        return self.store.rows(f'SELECT * FROM {table} WHERE (? IS NULL OR active=?) ORDER BY name',(active,active))

    def position(self, account_id, name, cost, value, identity=None):
        cents(cost); cents(value)
        if min(cost,value)<0:
            raise ValidationError('Posições não podem ser negativas.')
        with self.store.transaction() as conn:
            account=self.store.get('accounts',account_id,conn)
            if account['kind']!='brokerage' or not account['active']:
                raise ValidationError('Selecione uma corretora ativa.')
            if identity:
                previous=self.store.get('positions',identity,conn)
                if previous['account_id']!=account_id:
                    raise ValidationError('A corretora da posição não pode ser alterada.')
                conn.execute('UPDATE positions SET name=?,cost_cents=?,value_cents=? WHERE id=?',(title(name),cost,value,identity))
                return identity
            # Opening position is a separate initial asset, not a cash contribution.
            return conn.execute('INSERT INTO positions(account_id,name,cost_cents,value_cents) VALUES (?,?,?,?)',
                (account_id,title(name),cost,value)).lastrowid

    def invest(self, position_id, amount, occurred, redeem=False):
        cents(amount,True)
        with self.store.transaction() as conn:
            pos=self.store.get('positions',position_id,conn)
            self._account(conn,pos['account_id'],occurred)
            if redeem and amount>pos['value_cents']:
                raise ValidationError('Resgate superior ao valor da posição.')
            if not redeem and next(a for a in self.balances() if a['id']==pos['account_id'])['balance_cents']<amount:
                raise ValidationError('Caixa insuficiente na corretora para aporte.')
            delta=-amount if redeem else amount
            conn.execute('UPDATE positions SET value_cents=value_cents+?,cost_cents=max(0,cost_cents+?) WHERE id=?',(delta,delta,position_id))
            return self._write(conn,kind='investment',description=('Resgate: ' if redeem else 'Aporte: ')+pos['name'],
                amount=amount,occurred=occurred,source='investment',entries=[(pos['account_id'],-delta)])

    def account_evolution(self,identity,months=6):
        from datetime import timedelta
        from safira.domain import add_months
        self.store.get('accounts',identity)
        today=date.today().isoformat()
        points=[]
        for offset in range(-months+1,1):
            start=add_months(today,offset,1)
            end=(date.fromisoformat(add_months(start,1,1))-timedelta(days=1)).isoformat()
            as_of=min(today,end)
            row=next(a for a in self.balances(as_of) if a['id']==identity)
            points.append({'date':as_of,'balance_cents':row['balance_cents']})
        return points
