from datetime import date
from safira.domain import ValidationError, cents, iso, invoice_dates, add_months, split_installments
from safira.services import title,unique_name
from uuid import uuid4


class Cards:
    def __init__(self, store, finance):
        self.store, self.finance = store, finance

    def save(self,name,kind,account_id,limit,closing_day,due_day,identity=None):
        cents(limit)
        if kind not in ('credit','debit') or limit<0:
            raise ValidationError('Tipo/limite inválido.')
        invoice_dates(date.today().isoformat(),closing_day,due_day)
        with self.store.transaction() as conn:
            name=unique_name(conn,'cards',name,identity=identity)
            if account_id:
                self.finance._account(conn,account_id,date.today().isoformat())
            if kind=='debit' and not account_id:
                raise ValidationError('Débito exige conta associada.')
            if identity:
                old=self.store.get('cards',identity,conn)
                if old['kind'] != kind:
                    raise ValidationError('O tipo do cartão não pode ser alterado.')
                if self.outstanding(identity)>limit and kind=='credit':
                    raise ValidationError('Limite inferior ao saldo devedor.')
                conn.execute('UPDATE cards SET name=?,account_id=?,limit_cents=?,closing_day=?,due_day=? WHERE id=?',
                    (title(name),account_id,limit,closing_day,due_day,identity))
                return identity
            return conn.execute('INSERT INTO cards(name,kind,account_id,limit_cents,closing_day,due_day) VALUES (?,?,?,?,?,?)',
                (title(name),kind,account_id,limit,closing_day,due_day)).lastrowid

    def outstanding(self,card_id):
        return sum(row['remaining_cents'] for row in self.invoices(card_id))

    def invoices(self,card_id=None):
        return self.store.rows('''SELECT i.*,c.name card,
            coalesce((SELECT sum(s.amount_cents) FROM installments s JOIN purchases p ON p.id=s.purchase_id
            WHERE s.invoice_id=i.id AND p.cancelled=0),0) total_cents,
            coalesce((SELECT sum(o.amount_cents) FROM invoice_payments ip JOIN operations o ON o.id=ip.operation_id
            WHERE ip.invoice_id=i.id AND o.status='confirmed'),0) paid_cents,
            coalesce((SELECT sum(s.amount_cents) FROM installments s JOIN purchases p ON p.id=s.purchase_id
            WHERE s.invoice_id=i.id AND p.cancelled=0),0)-coalesce((SELECT sum(o.amount_cents)
            FROM invoice_payments ip JOIN operations o ON o.id=ip.operation_id
            WHERE ip.invoice_id=i.id AND o.status='confirmed'),0) remaining_cents
            FROM invoices i JOIN cards c ON c.id=i.card_id WHERE (? IS NULL OR i.card_id=?) ORDER BY due''',(card_id,card_id))

    def purchase(self,card_id,description,amount,occurred,category_id,count=1,token=None):
        cents(amount,True); iso(occurred)
        if occurred>date.today().isoformat():
            raise ValidationError('Compra futura deve ser registrada como previsão, não compra confirmada.')
        parts=split_installments(amount,count)
        token=token or str(uuid4())
        with self.store.transaction() as conn:
            previous=conn.execute('SELECT * FROM purchases WHERE token=?',(token,)).fetchone()
            if previous:
                old_count=1 if previous['debit_operation_id'] else conn.execute('SELECT count(*) FROM installments WHERE purchase_id=?',(previous['id'],)).fetchone()[0]
                if (previous['card_id'],previous['description'],previous['amount_cents'],previous['occurred'],previous['category_id'],old_count)!=(card_id,title(description),amount,occurred,category_id,count):
                    raise ValidationError('Chave de compra já usada com outros dados.')
                return previous['id']
            card=self.store.get('cards',card_id,conn)
            if not card['active']:
                raise ValidationError('Cartão desativado.')
            self.finance._category(conn,category_id,'expense')
            if card['kind']=='debit' and count!=1:
                raise ValidationError('Débito não permite parcelamento.')
            if card['kind']=='credit' and self.outstanding(card_id)+amount>card['limit_cents']:
                raise ValidationError('Limite de crédito insuficiente.')
            debit=None
            if card['kind']=='debit':
                debit=self.finance._write(conn,kind='expense',description=description,amount=amount,
                    occurred=occurred,category_id=category_id,entries=[(card['account_id'],-amount)],source='debit',token='debit:'+token)
            purchase_id=conn.execute('''INSERT INTO purchases(token,card_id,description,amount_cents,occurred,category_id,debit_operation_id)
                VALUES (?,?,?,?,?,?,?)''',(token,card_id,title(description),amount,occurred,category_id,debit)).lastrowid
            if card['kind']=='credit':
                close,due=invoice_dates(occurred,card['closing_day'],card['due_day'])
                for index,part in enumerate(parts):
                    closing=add_months(close,index,card['closing_day'])
                    due_date=add_months(due,index,card['due_day'])
                    conn.execute('INSERT OR IGNORE INTO invoices(card_id,closing,due) VALUES (?,?,?)',(card_id,closing,due_date))
                    invoice=conn.execute('SELECT * FROM invoices WHERE card_id=? AND closing=?',(card_id,closing)).fetchone()
                    if invoice['closed']:
                        raise ValidationError('Fatura fechada. Não é permitido lançar compra retroativa neste ciclo.')
                    conn.execute('INSERT INTO installments(purchase_id,invoice_id,number,amount_cents,competence) VALUES (?,?,?,?,?)',
                        (purchase_id,invoice['id'],index+1,part,invoice['due']))
            return purchase_id

    def pay(self,invoice_id,account_id,amount,paid,token=None):
        cents(amount,True); iso(paid)
        with self.store.transaction() as conn:
            if token:
                old=conn.execute('''SELECT o.id,o.amount_cents,o.occurred,ip.invoice_id,e.account_id FROM operations o
                    LEFT JOIN invoice_payments ip ON ip.operation_id=o.id LEFT JOIN entries e ON e.operation_id=o.id
                    WHERE o.token=?''',(token,)).fetchone()
                if old:
                    if (old['invoice_id'],old['account_id'],old['amount_cents'],old['occurred'])!=(invoice_id,account_id,amount,paid):
                        raise ValidationError('Chave de pagamento já usada com outros dados.')
                    return old['id']
            invoice=self.store.get('invoices',invoice_id,conn)
            summary=next(i for i in self.invoices() if i['id']==invoice_id)
            if paid<invoice['closing']:
                raise ValidationError('Pagamento disponível a partir do fechamento da fatura.')
            if amount>summary['remaining_cents']:
                raise ValidationError('Pagamento maior que o saldo remanescente.')
            operation=self.finance._write(conn,kind='invoice_payment',description='Pagamento de fatura: '+summary['card'],
                amount=amount,occurred=paid,entries=[(account_id,-amount)],source='invoice',token=token)
            conn.execute('INSERT INTO invoice_payments(invoice_id,operation_id) VALUES (?,?)',(invoice_id,operation))
            conn.execute('UPDATE invoices SET closed=1 WHERE id=?',(invoice_id,))
            return operation

    def close(self,invoice_id):
        with self.store.transaction() as conn:
            invoice=self.store.get('invoices',invoice_id,conn)
            if invoice['closing']>date.today().isoformat():
                raise ValidationError('O período de faturamento ainda não terminou.')
            conn.execute('UPDATE invoices SET closed=1 WHERE id=?',(invoice_id,))

    def cancel(self,purchase_id):
        with self.store.transaction() as conn:
            purchase=self.store.get('purchases',purchase_id,conn)
            paid=conn.execute('''SELECT 1 FROM installments s JOIN invoice_payments ip ON ip.invoice_id=s.invoice_id
                WHERE s.purchase_id=?''',(purchase_id,)).fetchone()
            if paid:
                raise ValidationError('Compra em fatura com pagamentos: estorno conciliado não suportado nesta versão.')
            conn.execute('UPDATE purchases SET cancelled=1 WHERE id=?',(purchase_id,))
            if purchase['debit_operation_id']:
                conn.execute("UPDATE operations SET status='cancelled' WHERE id=?",(purchase['debit_operation_id'],))

    def purchases(self):
        return self.store.rows('''SELECT p.*,c.name card,(SELECT count(*) FROM installments s WHERE s.purchase_id=p.id) installments
            FROM purchases p JOIN cards c ON c.id=p.card_id ORDER BY p.occurred DESC,p.id DESC''')

    def payments(self,invoice_id):
        return self.store.rows('''SELECT o.* FROM invoice_payments ip JOIN operations o ON o.id=ip.operation_id
            WHERE ip.invoice_id=? ORDER BY o.occurred''',(invoice_id,))
