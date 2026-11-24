import logging
import os
import sqlite3
import tempfile
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from safira.domain import ValidationError


def data_dir():
    explicit=os.environ.get('SAFIRA_DATA_DIR')
    if explicit:
        return Path(explicit).expanduser().resolve()
    if os.name=='nt':
        return Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData'/'Local'))/'SAFIRA'
    return Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local'/'share'))/'safira'


def configure_logging(folder):
    folder.mkdir(parents=True,exist_ok=True)
    logger=logging.getLogger('safira')
    if not logger.handlers:
        handler=RotatingFileHandler(folder/'safira.log',maxBytes=1_000_000,backupCount=3,encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class InstanceLock:
    """Keep a Windows byte-range lock for the process lifetime, including restore."""
    def __init__(self,folder):
        self.path=Path(folder)/'safira.lock'
        self.file=None

    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.file=self.path.open('a+b',buffering=0)
        try:
            self.file.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.file.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            if os.fstat(self.file.fileno()).st_size==0:
                self.file.write(b'0')
        except OSError:
            self.file.close()
            raise ValidationError('O SAFIRA já está aberto para este diretório de dados.') from None
        return self

    def __exit__(self,*args):
        if self.file:
            if os.name=='nt':
                import msvcrt
                self.file.seek(0)
                msvcrt.locking(self.file.fileno(),msvcrt.LK_UNLCK,1)
            self.file.close()


class Backup:
    def __init__(self,store):
        self.store=store

    @staticmethod
    def validate(path):
        path=Path(path)
        if not path.is_file():
            raise ValidationError('Arquivo de backup não encontrado.')
        conn=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
        try:
            if conn.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or conn.execute('PRAGMA foreign_key_check').fetchall():
                raise ValidationError('Integridade do backup inválida.')
            version=conn.execute('SELECT max(version) FROM schema_migrations').fetchone()[0]
            if version!=1:
                raise ValidationError('Versão de backup incompatível.')
            required={'profile','settings','accounts','categories','methods','operations','entries','positions','cards','invoices','purchases','installments','invoice_payments','series','commitments'}
            actual={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not required<=actual or conn.execute('SELECT count(*) FROM profile WHERE id=1').fetchone()[0]!=1:
                raise ValidationError('Não é um backup completo do SAFIRA.')
            for table,column in [('operations','amount_cents'),('entries','delta_cents'),('accounts','initial_cents')]:
                if conn.execute(f"SELECT 1 FROM {table} WHERE typeof({column})!='integer' LIMIT 1").fetchone():
                    raise ValidationError('Valores monetários inválidos no backup.')
            invalid=conn.execute('''SELECT o.id FROM operations o LEFT JOIN entries e ON e.operation_id=o.id
                GROUP BY o.id HAVING count(e.id)=0 OR
                (o.kind='transfer' AND (count(e.id)!=2 OR sum(e.delta_cents)!=0 OR max(e.delta_cents)!=o.amount_cents)) OR
                (o.kind!='transfer' AND (count(e.id)!=1 OR abs(sum(e.delta_cents))!=o.amount_cents)) OR
                (o.kind='income' AND sum(e.delta_cents)<=0) OR
                (o.kind IN ('expense','invoice_payment') AND sum(e.delta_cents)>=0)''').fetchone()
            if invalid:
                raise ValidationError('Operações inconsistentes no backup.')
            if conn.execute('''SELECT p.id FROM purchases p JOIN cards c ON c.id=p.card_id
                LEFT JOIN installments s ON s.purchase_id=p.id WHERE c.kind='credit'
                GROUP BY p.id HAVING coalesce(sum(s.amount_cents),0)!=p.amount_cents''').fetchone():
                raise ValidationError('Parcelamento inconsistente no backup.')
            if conn.execute('''SELECT k.id FROM commitments k LEFT JOIN operations o ON o.id=k.operation_id
                WHERE k.state='paid' AND (o.id IS NULL OR o.status!='confirmed' OR o.kind!='expense'
                OR o.source!='commitment' OR o.amount_cents!=k.amount_cents)''').fetchone():
                raise ValidationError('Compromisso pago sem movimentação válida.')
        except sqlite3.DatabaseError:
            raise ValidationError('Arquivo inválido ou esquema incompatível.') from None
        finally:
            conn.close()

    def export(self,destination):
        destination=Path(destination).resolve()
        if destination==self.store.path.resolve():
            raise ValidationError('Escolha outro arquivo para o backup.')
        destination.parent.mkdir(parents=True,exist_ok=True)
        handle,tmp=tempfile.mkstemp(dir=destination.parent,suffix='.sqlite')
        os.close(handle)
        source=self.store.connect()
        target=sqlite3.connect(tmp)
        try:
            source.backup(target)
            target.close()
            self.validate(tmp)
            os.replace(tmp,destination)
        finally:
            source.close(); target.close()
            Path(tmp).unlink(missing_ok=True)

    def restore(self,source,confirmed=False):
        if not confirmed:
            raise ValidationError('Confirme a substituição antes de restaurar.')
        source=Path(source).resolve()
        if source==self.store.path.resolve():
            raise ValidationError('Selecione um backup externo à base ativa.')
        self.validate(source)
        handle,tmp=tempfile.mkstemp(dir=self.store.path.parent,suffix='.restore')
        os.close(handle)
        try:
            src=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)
            dst=sqlite3.connect(tmp)
            try:
                src.backup(dst)
            finally:
                src.close(); dst.close()
            self.validate(tmp)
            safety=self.store.path.parent/('antes-restauracao-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.sqlite')
            self.export(safety)
            conn=self.store.connect()
            try:
                result=conn.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
                if result[0]:
                    raise ValidationError('Base ocupada. Feche outras instâncias e tente novamente.')
                conn.execute('PRAGMA journal_mode=DELETE')
            finally:
                conn.close()
            os.replace(tmp,self.store.path)
            self.store.migrate()
            return safety
        finally:
            Path(tmp).unlink(missing_ok=True)
