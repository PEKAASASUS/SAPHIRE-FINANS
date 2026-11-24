import time
from argon2 import PasswordHasher,Type
from argon2.exceptions import VerifyMismatchError,VerificationError,InvalidHashError
from safira.domain import ValidationError


class Auth:
    def __init__(self,store):
        self.store=store
        self.hasher=PasswordHasher(time_cost=3,memory_cost=65536,parallelism=4,type=Type.ID)
        self.authenticated=False

    def configured(self):
        return self.store.one('SELECT id FROM profile WHERE id=1') is not None

    def setup(self,password,confirmation):
        if password!=confirmation or len(password)<10:
            raise ValidationError('Use pelo menos 10 caracteres e confirme a mesma senha.')
        verifier=self.hasher.hash(password)
        with self.store.transaction() as conn:
            if conn.execute('SELECT 1 FROM profile').fetchone():
                raise ValidationError('Senha já configurada.')
            conn.execute('INSERT INTO profile(id,verifier) VALUES(1,?)',(verifier,))
        self.authenticated=True

    def login(self,password):
        row=self.store.one('SELECT * FROM profile WHERE id=1')
        if not row:
            raise ValidationError('Configure a senha mestra.')
        if row['retry_at']>int(time.time()):
            raise ValidationError('Aguarde alguns segundos antes de tentar novamente.')
        try:
            self.hasher.verify(row['verifier'],password)
        except (VerifyMismatchError,VerificationError,InvalidHashError):
            failures=row['failures']+1
            with self.store.transaction() as conn:
                conn.execute('UPDATE profile SET failures=?,retry_at=? WHERE id=1',
                    (failures,int(time.time())+min(60,2**min(failures-3,6)) if failures>=3 else 0))
            raise ValidationError('Senha incorreta.') from None
        with self.store.transaction() as conn:
            conn.execute('UPDATE profile SET failures=0,retry_at=0 WHERE id=1')
            if self.hasher.check_needs_rehash(row['verifier']):
                conn.execute('UPDATE profile SET verifier=? WHERE id=1',(self.hasher.hash(password),))
        self.authenticated=True

    def change(self,current,new,confirmation):
        self.login(current)
        if new!=confirmation or len(new)<10:
            raise ValidationError('Nova senha: ao menos 10 caracteres e confirmação igual.')
        with self.store.transaction() as conn:
            conn.execute('UPDATE profile SET verifier=? WHERE id=1',(self.hasher.hash(new),))

    def lock(self):
        self.authenticated=False
