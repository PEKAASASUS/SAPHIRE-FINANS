"""Disposable development preview. Synthetic records never enter the real profile."""
import sys,tempfile
from datetime import date,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from safira.controller import Controller
from safira.ui.app import App
from safira.reports import export_pdf

root=Path(__file__).resolve().parents[1]
(root/'.test-tmp').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=root/'.test-tmp') as folder:
    c=Controller(Path(folder)/'preview.sqlite')
    c.auth.setup('preview-local-only','preview-local-only')
    today=date.today().isoformat(); start=date.today().replace(day=1).isoformat()
    a=c.finance.account('Conta principal','bank',200000,'2026-01-01')
    c.finance.account('Carteira','wallet',20000,'2026-01-01')
    b=c.finance.account('Investimentos','brokerage',50000,'2026-01-01')
    c.finance.position(b,'Tesouro e renda fixa',1000000,1030000)
    expense=next(r['id'] for r in c.finance.catalogs('categories',1) if r['kind']=='expense')
    income=next(r['id'] for r in c.finance.catalogs('categories',1) if r['kind']=='income')
    c.finance.movement(a,'income','Salário',450000,today,income)
    c.finance.movement(a,'expense','Compras do mês',123450,today,expense)
    c.commitments.create('Internet',12990,(date.today()+timedelta(days=3)).isoformat(),a,expense)
    app=App(c); app.shell()
    app.title('SAFIRA • PRÉVIA DE TESTE • Dados descartáveis')
    app.geometry('1440x900')
    report=c.analytics.report(start,today); report['forecast']=c.analytics.forecast((date.today()+timedelta(days=30)).isoformat())
    (root/'artifacts').mkdir(exist_ok=True)
    export_pdf(root/'artifacts'/'relatorio-validacao.pdf',report,c.commitments.list(start,today),c.cards.invoices())
    app.after(240000,app.destroy)
    app.mainloop()
