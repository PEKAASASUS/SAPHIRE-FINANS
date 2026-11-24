"""Account scope for dashboard reads; financial services remain unchanged."""
from types import SimpleNamespace

from safira.analytics import Analytics
from safira.services import Finance


class ActiveAccountReads:
    """Shadow query sources with active-account views, without database writes."""
    PREFIX = '''WITH
        accounts AS (SELECT * FROM main.accounts WHERE active=1),
        entries AS (SELECT e.* FROM main.entries e JOIN accounts a ON a.id=e.account_id),
        operations AS (SELECT o.* FROM main.operations o
            WHERE EXISTS (SELECT 1 FROM entries e WHERE e.operation_id=o.id)),
        cards AS (SELECT c.* FROM main.cards c JOIN accounts a ON a.id=c.account_id),
        purchases AS (SELECT p.* FROM main.purchases p JOIN cards c ON c.id=p.card_id),
        installments AS (SELECT s.* FROM main.installments s JOIN purchases p ON p.id=s.purchase_id),
        commitments AS (SELECT k.* FROM main.commitments k JOIN accounts a ON a.id=k.account_id),
        positions AS (SELECT p.* FROM main.positions p JOIN accounts a ON a.id=p.account_id)
    '''

    def __init__(self,store):
        self.store=store

    def rows(self,sql,params=()):
        return self.store.rows(self.PREFIX+sql,params)


def active_account_analytics(controller):
    reads=ActiveAccountReads(controller.store)
    finance=Finance(reads)
    # Invoice payments remain complete, even when funded by an archived account.
    def invoices():
        card_ids={r['id'] for r in reads.rows('SELECT id FROM cards')}
        return [r for r in controller.cards.invoices() if r['card_id'] in card_ids]
    cards=SimpleNamespace(invoices=invoices)
    commitments=SimpleNamespace(generate=controller.commitments.generate)
    return Analytics(reads,finance,cards,commitments)
