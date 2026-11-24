"""Generate a synthetic multipage QA report without touching a personal profile."""
import sys,tempfile
from datetime import date,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from safira.controller import Controller
from safira.reports import export_pdf

root=Path(__file__).resolve().parents[1]
(root/'.test-tmp').mkdir(exist_ok=True)
(root/'artifacts').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=root/'.test-tmp') as folder:
    c=Controller(Path(folder)/'pdf.sqlite')
    today=date.today().isoformat()
    a=c.finance.account('Conta principal','bank',200000,'2026-01-01')
    expense=next(r['id'] for r in c.finance.catalogs('categories',1) if r['kind']=='expense')
    income=next(r['id'] for r in c.finance.catalogs('categories',1) if r['kind']=='income')
    c.finance.movement(a,'income','Salário',450000,today,income)
    for index in range(50):
        c.finance.movement(a,'expense',f'Despesa de validação {index+1} com descrição detalhada para verificar quebra de linha e repetição do cabeçalho',1234,today,expense)
    c.commitments.create('Internet',12990,(date.today()+timedelta(days=3)).isoformat(),a,expense)
    report=c.analytics.report(date.today().replace(day=1).isoformat(),today)
    report['forecast']=c.analytics.forecast((date.today()+timedelta(days=30)).isoformat())
    assert report['income_cents']==450000 and report['expense_cents']==61700
    path=export_pdf(root/'artifacts'/'relatorio-validacao.pdf',report,c.commitments.list(today,today),c.cards.invoices())
    print(path)
