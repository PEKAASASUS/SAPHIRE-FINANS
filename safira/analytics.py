from datetime import date,timedelta
from safira.domain import iso,ValidationError,add_months


class Analytics:
    def __init__(self,store,finance,cards,commitments):
        self.store,self.finance,self.cards,self.commitments=store,finance,cards,commitments

    def report(self,start,end):
        iso(start); iso(end)
        if start>end:
            raise ValidationError('Período invertido.')
        flows=self.finance.movements(start,end)
        confirmed=[r for r in flows if r['status']=='confirmed']
        consumption=self.store.rows('''SELECT s.competence occurred,p.description,s.amount_cents,c.name category,
            c.id category_id FROM installments s JOIN purchases p ON p.id=s.purchase_id
            JOIN categories c ON c.id=p.category_id WHERE p.cancelled=0 AND s.competence BETWEEN ? AND ?
            ORDER BY s.competence''',(start,end))
        recognized=self.store.rows('''SELECT o.*,c.name category FROM operations o LEFT JOIN categories c ON c.id=o.category_id
            WHERE o.status='confirmed' AND o.kind IN ('income','expense') AND o.competence BETWEEN ? AND ?''',(start,end))
        income=sum(r['amount_cents'] for r in recognized if r['kind']=='income')
        expense=sum(r['amount_cents'] for r in recognized if r['kind']=='expense')+sum(r['amount_cents'] for r in consumption)
        categories={}
        for row in [r for r in recognized if r['kind']=='expense']+consumption:
            key=row['category'] or 'Sem categoria'
            categories[key]=categories.get(key,0)+row['amount_cents']
        # Physical cash uses confirmation/payment date, distinct from competence.
        cash=self.store.rows('''SELECT o.kind,e.delta_cents FROM operations o JOIN entries e ON e.operation_id=o.id
            WHERE o.status='confirmed' AND o.confirmed BETWEEN ? AND ?''',(start,end))
        cash_in=sum(r['delta_cents'] for r in cash if r['delta_cents']>0 and r['kind']!='transfer')
        cash_out=-sum(r['delta_cents'] for r in cash if r['delta_cents']<0 and r['kind']!='transfer')
        balances=self.finance.balances()
        available=sum(a['balance_cents'] for a in balances if a['kind'] in ('bank','wallet'))
        reserved=sum(a['balance_cents'] for a in balances if a['kind']=='reserve')
        invested=sum(a['invested_cents'] for a in balances)
        gross=sum(a['balance_cents']+a['invested_cents'] for a in balances)
        debt=sum(r['remaining_cents'] for r in self.cards.invoices())
        return dict(start=start,end=end,income_cents=income,expense_cents=expense,result_cents=income-expense,
            cash_in_cents=cash_in,cash_out_cents=cash_out,available_cents=available,reserved_cents=reserved,
            invested_cents=invested,gross_cents=gross,debt_cents=debt,net_cents=gross-debt,
            balances=balances,categories=categories,operations=flows,consumption=consumption)

    def forecast(self,end,today=None):
        today=iso(today or date.today().isoformat()); iso(end)
        if end<today:
            raise ValidationError('Fim da projeção deve ser hoje ou futuro.')
        self.commitments.generate(end)
        balances=self.finance.balances(today)
        available=sum(a['balance_cents'] for a in balances if a['kind'] in ('bank','wallet'))
        pending=self.store.rows('''SELECT o.id,o.description,o.occurred due,e.delta_cents FROM operations o
            JOIN entries e ON e.operation_id=o.id JOIN accounts a ON a.id=e.account_id
            WHERE o.status='pending' AND o.occurred<=? AND a.kind IN ('bank','wallet')''',(end,))
        events=[dict(source='Movimentação',id=r['id'],title=r['description'],due=r['due'],delta=r['delta_cents']) for r in pending]
        for row in self.store.rows('''SELECT k.* FROM commitments k JOIN accounts a ON a.id=k.account_id
            WHERE k.state IN ('pending','postponed') AND k.due<=? AND a.kind IN ('bank','wallet')''',(end,)):
            events.append(dict(source='Compromisso',id=row['id'],title=row['title'],due=row['due'],delta=-row['amount_cents']))
        for row in self.cards.invoices():
            if row['due']<=end and row['remaining_cents']>0:
                events.append(dict(source='Fatura',id=row['id'],title=row['card'],due=row['due'],delta=-row['remaining_cents']))
        return dict(real_cents=available,projected_cents=available+sum(e['delta'] for e in events),events=sorted(events,key=lambda e:e['due']))

    def notifications(self,today=None):
        today=iso(today or date.today().isoformat())
        soon=(date.fromisoformat(today)+timedelta(days=7)).isoformat()
        self.commitments.generate(soon)
        alerts=[]
        for row in self.store.rows("SELECT * FROM commitments WHERE state IN ('pending','postponed') AND due<=? ORDER BY due",(soon,)):
            alerts.append(dict(key=f"commitment:{row['id']}",module='Compromissos',id=row['id'],title=row['title'],due=row['due'],amount_cents=row['amount_cents'],overdue=row['due']<today))
        for row in self.cards.invoices():
            if row['remaining_cents']>0 and row['due']<=soon:
                alerts.append(dict(key=f"invoice:{row['id']}",module='Faturas',id=row['id'],title=row['card'],due=row['due'],amount_cents=row['remaining_cents'],overdue=row['due']<today))
        return sorted(alerts,key=lambda a:a['due'])

    def monthly(self,months=6):
        today=date.today().isoformat()
        result=[]
        for offset in range(-months+1,1):
            start=add_months(today,offset,1)
            end=(date.fromisoformat(add_months(start,1,1))-timedelta(days=1)).isoformat()
            report=self.report(start,end)
            result.append(dict(month=start[:7],income=report['income_cents'],expense=report['expense_cents'],
                cash=sum(a['balance_cents'] for a in self.finance.balances(min(end,today)))))
        return result
