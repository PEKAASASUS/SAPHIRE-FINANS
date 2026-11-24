"""Synthetic GUI QA for planning; retain artifacts for diagnosis."""
import sys
from datetime import date
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from safira.controller import Controller
from safira.planning_service import planning_for
from safira.ui.app import App
from safira.ui.widgets import Form,Motion
from safira.ui.tokens import RED
from safira.ui.planning_dialogs import budget_panel,salary_panel,calendar_panel
from PIL import ImageGrab


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def run():
    folder=Path(__file__).resolve().parents[1]/'.test-tmp'/('planning-ui-retained-'+uuid4().hex)
    folder.mkdir(parents=True)
    c=Controller(folder/'synthetic.sqlite')
    c.auth.setup('planning-ui-synthetic','planning-ui-synthetic')
    today=date.today().isoformat();month=today[:7]
    account=c.finance.account('Banco sintético','bank',200000,'2020-01-01')
    cats=c.finance.catalogs('categories');expense=next(r['id'] for r in cats if r['kind']=='expense')
    income=next(r['id'] for r in cats if r['kind']=='income')
    p=planning_for(c);p.budget(month,expense,60000)
    c.finance.movement(account,'expense','Compra sintética',45000,today,expense)
    app=App(c);errors=[]
    app.report_callback_exception=lambda *args:errors.append(repr(args[1]))
    app.guard=lambda fn:fn()
    Motion.set_reduced(True)
    app.shell();app.geometry('1280x900');app.update()
    def snap(name,window=app):
        app.update()
        app.after(300,app.quit);app.mainloop();app.update()
        box=(window.winfo_rootx(),window.winfo_rooty(),window.winfo_rootx()+window.winfo_width(),window.winfo_rooty()+window.winfo_height())
        ImageGrab.grab(bbox=box).save(folder/(name+'.png'))
    try:
        snap('home')
        for name in app.factories:
            app.navigate(name);app.update()
        app.navigate('Planejamento');app.update();screen=app.screens['Planejamento']
        snap('planning')
        def invoke(window,text):
            next(w for w in descendants(window) if hasattr(w,'invoke') and w.cget('text')==text).invoke()
            app.update()
        def save_form(values):
            form=next(w for w in descendants(app) if isinstance(w,Form))
            for key,value in values.items():
                widget=form.fields[key]
                if key in form.choices:
                    caption=next(k for k,v in form.choices[key].items() if v==value)
                    widget.choose(caption)
                else:widget.delete(0,'end');widget.insert(0,str(value))
            form.save();app.update()
            assert not form.winfo_exists(),'Form error: '+form.error.cget('text')
        win=budget_panel(screen);app.update();snap('budgets',win)
        invoke(win,'Definir / editar limite');save_form({'category':expense,'amount':'650,00'})
        assert p.comparison(month)[0]['planned']==65000
        win.destroy();app.update()
        win=salary_panel(screen);app.update()
        invoke(win,'+ Receita recorrente')
        save_form({'name':'Salário sintético','account':account,'category':income,'amount':'3000,00','date':today})
        assert len(p.salaries())==1 and len(p.occurrences())==12
        snap('salary',win);win.destroy();app.update()
        win=calendar_panel(screen);app.update();snap('calendar',win);win.destroy()
        app.navigate('Home');app.update();snap('home-after')
        assert c.finance.balances()[0]['balance_cents']==155000
        assert c.analytics.forecast(today)['real_cents']==155000
        p.budget(month,expense,40000)
        app.screens['Home'].refresh();app.update()
        chart=app.screens['Home'].budget_comparison
        assert any(chart.canvas.itemcget(item,'fill')==RED for item in chart.canvas.find_all())
        snap('home-over-budget')
        import customtkinter as ctk
        for size,scale in (('1000x700',1),('1280x900',1.25)):
            app.geometry(size);ctk.set_widget_scaling(scale);app.update()
            app.after(200,app.quit);app.mainloop();app.update()
            app.screens['Home'].refresh();app.update()
        ctk.set_widget_scaling(1)
        assert not errors,errors
        print('PASS: all screens, budget save, recurring salary save, calendar, unchanged real balance')
        print('Artifacts:',folder)
    finally:app.destroy()

if __name__=='__main__':run()
