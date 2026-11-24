"""Run explicitly on Windows: python tests/ui_smoke.py. Uses disposable V3 data."""
import sys
import tempfile
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from safira.controller import Controller
from safira.ui.app import App
from safira.ui.widgets import Form


def run():
    root=Path(__file__).resolve().parents[1]/'.test-tmp'
    root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as folder:
        c=Controller(Path(folder)/'ui.sqlite')
        app=App(c); errors=[]
        app.report_callback_exception=lambda *args:errors.append(repr(args[1]))
        app.update()
        assert not c.auth.authenticated
        c.auth.setup('smoke-test-password','smoke-test-password')
        a=c.finance.account('Banco de teste','bank',100000,'2026-01-01')
        c.finance.account('Corretora','brokerage',0,'2026-01-01')
        cat=next(r['id'] for r in c.finance.catalogs('categories',1) if r['kind']=='expense')
        c.finance.movement(a,'expense','Teste UI',1000,'2026-01-02',cat)
        app.shell(); app.update()
        for name in app.factories:
            app.navigate(name); app.update()
            assert name in app.screens
            app.screens[name].refresh(); app.update()
            print('UI OK:',name)
        def descendants(widget):
            result=[]
            for child in widget.winfo_children():
                result.append(child); result.extend(descendants(child))
            return result
        def save_form(action,values):
            action(); app.update()
            form=next(w for w in descendants(app) if isinstance(w,Form))
            for key,value in values.items():
                field=form.fields[key]
                if key in form.choices:
                    caption=next(label for label,actual in form.choices[key].items() if actual==value)
                    field.choose(caption)
                else:
                    field.delete(0,'end'); field.insert(0,str(value))
            form.save(); app.update()
            assert not form.winfo_exists(), 'Form save failed'
        today=date.today().isoformat()
        app.navigate('Contas')
        save_form(app.screens['Contas'].edit,{'name':'Criada pela UI','initial':'100,00','opened':'2026-01-01'})
        assert len(c.finance.catalogs('accounts'))==3
        app.navigate('Movimentações')
        save_form(app.screens['Movimentações'].edit,{'account':a,'kind':'expense','description':'Salva pelo formulário',
            'amount':'12,34','date':today,'competence':today,'confirmed':today,'category':cat})
        assert any(r['description']=='Salva pelo formulário' for r in c.finance.movements('2026-01-01',today))
        app.navigate('Cartões')
        save_form(app.screens['Cartões'].edit,{'name':'Débito UI','kind':'debit','account':a,'limit':'0,00','closing':'10','due':'20'})
        card=c.finance.catalogs('cards')[0]['id']
        save_form(app.screens['Cartões'].purchase,{'card':card,'description':'Compra UI','amount':'5,00','category':cat,'count':'1','date':today})
        assert len(c.cards.purchases())==1
        app.navigate('Compromissos')
        save_form(app.screens['Compromissos'].create,{'title':'Compromisso UI','amount':'10,00','due':today,'account':a,'category':cat})
        screen=app.screens['Compromissos']
        screen.grid.tree.selection_set(next(iter(screen.grid.records)))
        save_form(screen.pay,{'date':today})
        assert c.commitments.list(today,today)[0]['state']=='paid'
        for dimensions in ('980x600','1440x900'):
            app.geometry(dimensions); app.update()
            for name in app.factories:
                app.navigate(name); app.update()
        print('UI FORMS AND RESIZE PASSED')
        app.lock(); app.update()
        assert not c.auth.authenticated
        app.destroy()
        if errors: raise AssertionError(errors)
        print('UI SMOKE PASSED')


if __name__=='__main__': run()
