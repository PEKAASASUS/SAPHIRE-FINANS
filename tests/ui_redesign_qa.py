"""Explicit Windows UI QA, synthetic data only. python tests/ui_redesign_qa.py"""
import sys,tempfile,time,json,hashlib,traceback,faulthandler
from contextlib import nullcontext
from uuid import uuid4
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from safira.controller import Controller
from safira.ui.app import App
from safira.ui.widgets import Form,SapphireDatePicker,SapphireSelect
from safira.ui.motion import Motion
from safira.ui.preferences import Preferences


def run():
    faulthandler.dump_traceback_later(45,repeat=True)
    root=Path(__file__).resolve().parents[1]
    (root/'.test-tmp').mkdir(exist_ok=True)
    results={'navigation':[],'viewport_tests':[]}
    folder=root/'.test-tmp'/('qa-retained-'+uuid4().hex)
    print('QA directory:',folder,flush=True)
    with nullcontext(folder) as folder:
        c=Controller(Path(folder)/'qa.sqlite')
        c.auth.setup('qa-local-disposable','qa-local-disposable')
        # A long automated stress run has no real user activity. Keep the supported
        # timeout at one hour in this disposable profile; exercise locking below.
        c.set_setting('auto_lock',3600)
        a=c.finance.account('Conta de homologação','bank',100000,'2026-01-01')
        expense=next(r['id'] for r in c.finance.catalogs('categories',1) if r['kind']=='expense')
        today=date.today().isoformat()
        c.finance.movement(a,'expense','Homologação',1000,today,expense)
        app=App(c); errors=[]
        app.guard=lambda callback:callback()
        app.report_callback_exception=lambda typ,exc,tb:errors.append(''.join(traceback.format_exception(typ,exc,tb)))
        app.shell(); app.update()
        for name in app.factories:
            app.navigate(name); app.update(); results['navigation'].append(name)
        print('Navigation passed',flush=True)
        # Test layout independently from decorative frames; motion is stressed
        # again below, after returning to 100%.
        Motion.set_reduced(True)
        for scale in (1,1.25,1.5):
            import customtkinter as ctk
            ctk.set_widget_scaling(scale)
            for size in ('1366x768','1600x900','1920x1080'):
                app.geometry(size); app.update()
                for name in ('Home','Movimentações','Cartões','Configurações'):
                    app.navigate(name); app.update()
                results['viewport_tests'].append({'size':size,'widget_scale':scale})
                print('Viewport passed:',scale,size,flush=True)
        print('Viewports passed',flush=True)
        Motion.set_reduced(False)
        ctk.set_widget_scaling(1); app.geometry('1366x768'); app.navigate('Movimentações'); app.update()
        screen=app.screens['Movimentações']; grid=screen.grid
        rows=[{'id':i,'occurred':today,'description':f'Registro sintético {i}','kind':'expense',
               'account':'Conta de homologação','category':'Alimentação','status':'confirmed','amount_cents':1234} for i in range(10000)]
        formatter=lambda r:[r['occurred'],r['description'],'Despesa',r['account'],r['category'],'Confirmado','R$ 12,34']
        start=time.perf_counter(); grid.load(rows,formatter); app.update()
        results['grid_10000_load_ms']=round((time.perf_counter()-start)*1000,2)
        results['canvas_items']=len(grid.canvas.find_all())
        assert results['canvas_items']<1500,'Grid should render only the viewport'
        grid.selection_set('5000'); grid.see('5000'); app.update()
        assert grid.selected()['id']==5000
        grid.load(list(reversed(rows)),formatter); app.update()
        assert grid.selected()['id']==5000,'Selection must follow identity, not row index'
        grid.canvas.focus_force(); grid.canvas.event_generate('<Down>'); app.update()
        assert grid.selected()['id']==4999
        grid.canvas.event_generate('<Home>'); app.update(); assert grid.selected()['id']==9999
        grid.canvas.event_generate('<End>'); app.update(); assert grid.selected()['id']==0
        grid.load([],formatter); app.update(); assert not grid.selection()
        print('Grid and keyboard passed',flush=True)
        screen.refresh(); app.update()
        app.sidebar.toggle(); app.sidebar.toggle(); app.sidebar.toggle(); app.update()
        for _ in range(20):
            for name in ('Home','Movimentações','Planejamento','Configurações'):
                app.navigate(name); app.update()
        print('Rapid navigation passed',flush=True)
        app.navigate('Movimentações'); screen.edit(); app.update()
        form=next(w for w in screen.winfo_children() if isinstance(w,Form))
        form.fields['amount'].insert(0,'inválido'); form.save(); app.update()
        assert form.winfo_exists() and form.error.cget('text')
        picker=form.fields['date']; picker.open(); app.update(); picker.choose(today); app.update()
        assert picker.get()==today
        select=form.fields['account']; select.open(); app.update(); select.choose(select.values[0]); app.update()
        form.close()
        deadline=time.perf_counter()+.4
        while time.perf_counter()<deadline:app.update()
        assert not form.winfo_exists()
        app.preferences.save(True,125); Motion.set_reduced(True)
        assert Preferences(c.store.path.parent).values=={'reduce_motion':True,'scale':125}
        app.navigate('Home'); app.update()
        app.lock(); app.update()
        assert not c.auth.authenticated
        deadline=time.perf_counter()+.8
        while time.perf_counter()<deadline:app.update()
        assert not Motion.active,repr(Motion.active)
        app.destroy()
        assert not errors,errors
        results['callback_errors']=errors; results['motion_jobs_after_lock']=len(Motion.active)
        results['result']='PASS'
    (root/'artifacts').mkdir(exist_ok=True)
    (root/'artifacts'/'ui-qa-metrics.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))
    faulthandler.cancel_dump_traceback_later()


if __name__=='__main__':run()
