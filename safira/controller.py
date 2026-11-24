from safira.persistence import Store
from safira.services import Finance
from safira.cards import Cards
from safira.commitments import Commitments
from safira.analytics import Analytics
from safira.security import Auth
from safira.infrastructure import Backup


class Controller:
    def __init__(self,path):
        self.store=Store(path)
        self.finance=Finance(self.store)
        self.cards=Cards(self.store,self.finance)
        self.commitments=Commitments(self.store,self.finance)
        self.analytics=Analytics(self.store,self.finance,self.cards,self.commitments)
        self.auth=Auth(self.store)
        self.backup=Backup(self.store)

    def setting(self,key,default):
        row=self.store.one('SELECT value FROM settings WHERE key=?',(key,))
        return row['value'] if row else default

    def set_setting(self,key,value):
        if key not in ('auto_lock','scale'):
            raise ValueError('Preferência inválida.')
        value=int(value)
        if key=='auto_lock' and not 60<=value<=3600:
            raise ValueError('Bloqueio: entre 60 e 3600 segundos.')
        if key=='scale' and value not in (90,100,110,125):
            raise ValueError('Escala inválida.')
        with self.store.transaction() as conn:
            conn.execute('INSERT INTO settings VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,str(value)))
