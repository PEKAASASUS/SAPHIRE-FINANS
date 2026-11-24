"""Visual review with synthetic profile. Never opens the personal database."""
import sys,tempfile
from pathlib import Path
from datetime import date,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from safira.controller import Controller
from safira.ui.app import App

root=Path(__file__).resolve().parents[1]
(root/'.test-tmp').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=root/'.test-tmp') as folder:
    c=Controller(Path(folder)/'preview.sqlite')
    c.auth.setup('preview-synthetic-profile','preview-synthetic-profile')
    today=date.today().isoformat()
    bank=c.finance.account('Conta principal','bank',325000,'2026-01-01')
    wallet=c.finance.account('Carteira','wallet',25000,'2026-01-01')
    broker=c.finance.account('Patrimônio investido','brokerage',100000,'2026-01-01')
    c.finance.position(broker,'Renda fixa',1250000,1300000)
    categories=c.finance.catalogs('categories',1)
    income=next(r['id'] for r in categories if r['kind']=='income')
    expense=next(r['id'] for r in categories if r['name']=='Alimentação')
    home=next(r['id'] for r in categories if r['name']=='Moradia')
    health=next(r['id'] for r in categories if r['name']=='Saúde')
    # Historical events make the real chart meaningful, without production demo data.
    for month in range(5,11):
        occurred=f'2026-{month:02d}-05'
        if occurred<=today:c.finance.movement(bank,'income','Receita mensal',480000,occurred,income)
        occurred=f'2026-{month:02d}-08'
        if occurred<=today:c.finance.movement(bank,'expense','Moradia',160000,occurred,home)
    for description,amount,category in [('Mercado da semana',42390,expense),('Consulta médica',23000,health),('Café e almoço',8490,expense)]:
        c.finance.movement(bank,'expense',description,amount,today,category)
    c.finance.transfer(bank,wallet,10000,today)
    c.commitments.create('Internet residencial',12990,(date.today()+timedelta(days=2)).isoformat(),bank,home)
    card=c.cards.save('Meu cartão','credit',bank,800000,10,20)
    c.cards.purchase(card,'Compra parcelada',60000,'2026-10-01',expense,3)
    app=App(c); app.title('SAFIRA 3.1 • QA VISUAL • Dados sintéticos')
    app.guard=lambda callback:callback()
    app.shell()
    print('PREVIEW',app.winfo_screenwidth(),app.winfo_screenheight(),'scale',app._get_window_scaling(),app.geometry(),flush=True)
    app.after(900000,app.destroy)
    app.mainloop()
