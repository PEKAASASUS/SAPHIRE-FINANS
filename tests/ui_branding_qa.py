"""Capture branding with a retained synthetic profile, never the user's database."""
import sys
from pathlib import Path
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from safira.controller import Controller
from safira.ui.app import App
from safira.ui.widgets import Motion
from PIL import ImageGrab

folder=Path(__file__).resolve().parents[1]/'.test-tmp'/('branding-ui-retained-'+uuid4().hex)
folder.mkdir(parents=True)
c=Controller(folder/'synthetic.sqlite')
c.auth.setup('branding-synthetic-qa','branding-synthetic-qa')
app=App(c);errors=[]
app.report_callback_exception=lambda *args:errors.append(repr(args[1]))
app.guard=lambda fn:fn()
Motion.set_reduced(True)
app.geometry('1280x900')
def snap(name):
    app.update();app.after(350,app.quit);app.mainloop();app.update()
    x,y=app.winfo_rootx(),app.winfo_rooty()
    ImageGrab.grab(bbox=(x,y,x+app.winfo_width(),y+app.winfo_height())).save(folder/(name+'.png'))
try:
    snap('login')
    app.shell();snap('sidebar')
    for page in app.factories:app.navigate(page);app.update()
    app.navigate('Movimentações')
    # An account is needed to open a real movement form.
    c.finance.account('Conta sintética','bank',0,'2020-01-01')
    app.screens['Movimentações'].edit();snap('modal')
    assert not errors,errors
    print('PASS: login, sidebar, modal icons, all pages')
    print(folder)
finally:app.destroy()
