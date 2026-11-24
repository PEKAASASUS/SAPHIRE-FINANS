import hashlib,json
from pathlib import Path
from safira.ui.tokens import blend,BG,BLUE
from safira.ui.preferences import Preferences
from safira.ui.motion import Motion


def test_engine_is_byte_identical_to_v300():
    root=Path(__file__).resolve().parents[1]
    baseline=json.loads((root/'docs/FINANCIAL_ENGINE_BASELINE.json').read_text())
    for name,expected in baseline.items():
        assert hashlib.sha256((root/'safira'/name).read_bytes()).hexdigest()==expected,name


def test_motion_color_endpoints():
    assert blend(BG,BLUE,0)==BG.lower()
    assert blend(BG,BLUE,1)==BLUE.lower()
    assert blend(BG,BLUE,-1)==BG.lower()
    assert blend(BG,BLUE,2)==BLUE.lower()


def test_presentation_preferences_no_database_change(tmp_path):
    prefs=Preferences(tmp_path)
    prefs.save(True,150)
    assert Preferences(tmp_path).values=={'reduce_motion':True,'scale':150}
    assert not list(tmp_path.glob('*.sqlite'))


def test_invalid_preferences_fallback(tmp_path):
    (tmp_path/'ui-preferences.json').write_text('invalid',encoding='utf-8')
    prefs=Preferences(tmp_path)
    assert prefs.values['scale']==100


def test_reduced_motion_completes_without_after():
    class Widget:
        def bind(self,*args,**kwargs):pass
        def after(self,*args):raise AssertionError('Reduced motion must not schedule frames')
    Motion.set_reduced(True)
    animator=Motion(Widget()); values=[]
    animator.animate('test',250,values.append)
    assert values==[1]
    assert not animator.jobs
    Motion.set_reduced(False)


def test_popover_takes_modal_grab_when_its_window_is_mapped():
    from types import SimpleNamespace
    from safira.ui.controls import Popover

    calls=[]
    popup=SimpleNamespace(grab_set=lambda:calls.append('grab'),
                          focus_force=lambda:calls.append('focus'))
    Popover._activate(popup,SimpleNamespace(widget=object()))
    assert calls==[]
    Popover._activate(popup,SimpleNamespace(widget=popup))
    assert calls==['grab','focus']


def test_sidebar_surface_updates_arrow_background_with_main_button():
    from types import SimpleNamespace
    from safira.ui.sidebar import SidebarItem
    main,arrow={},{}
    row=SimpleNamespace(button=SimpleNamespace(configure=lambda **kw:main.update(kw)),
                        disclosure=SimpleNamespace(configure=lambda **kw:arrow.update(kw)))
    for color in (BG,BLUE):
        SidebarItem.paint(row,color)
        assert main['fg_color']==color
        assert arrow=={'fg_color':color,'bg_color':color,'border_color':color}


def test_popover_outside_click_dismisses_only_popup():
    from types import SimpleNamespace
    from safira.ui.controls import Popover
    closed=[]
    popup=SimpleNamespace(winfo_rootx=lambda:100,winfo_rooty=lambda:200,
        winfo_width=lambda:250,winfo_height=lambda:150,
        destroy=lambda:closed.append('popup'))
    for x,y in ((100,200),(349,349),(200,250)):
        assert Popover._dismiss_outside(popup,SimpleNamespace(x_root=x,y_root=y)) is None
    assert closed==[]
    for x,y in ((99,250),(350,250),(200,199),(200,350)):
        assert Popover._dismiss_outside(popup,SimpleNamespace(x_root=x,y_root=y))=='break'
    assert closed==['popup']*4


def test_movement_tables_keep_only_one_active_selection():
    from types import SimpleNamespace
    from safira.ui.finance_screens import Movements
    rendered=[]
    income=SimpleNamespace(selected_key='income:1',render=lambda:rendered.append('income'))
    expense=SimpleNamespace(selected_key='expense:2',render=lambda:rendered.append('expense'))
    screen=SimpleNamespace(grid=income,movement_grids={'income':income,'expense':expense})
    Movements.select_movement_grid(screen,'expense',{'id':2})
    assert screen.grid is expense
    assert income.selected_key is None
    assert expense.selected_key=='expense:2'
    assert rendered==['income']
    Movements.select_movement_grid(screen,'income',None)
    assert screen.grid is expense


def test_compact_form_reflows_and_hides_dependent_category():
    from types import SimpleNamespace
    from safira.ui.dialogs import Form
    positions={}
    frames={key:SimpleNamespace(grid=lambda k=key,**kw:positions.update({k:kw}),
        grid_remove=lambda k=key:positions.pop(k,None))
        for key in ('account','kind','description','category','status')}
    form=SimpleNamespace(field_layout=[('account','kind'),('description',),('category','status')],
        field_frames=frames,hidden_fields=set(),
        field_area=SimpleNamespace(winfo_width=lambda:720,_get_widget_scaling=lambda:1))
    form._layout_fields=lambda:Form._layout_fields(form)
    Form._layout_fields(form)
    assert positions['account']['row']==positions['kind']['row']==0
    assert positions['kind']['column']==1
    assert positions['description']['columnspan']==2
    Form.set_field_visible(form,'category',False)
    assert 'category' not in positions
    assert positions['status']['columnspan']==2
    Form.set_field_visible(form,'category',True)
    assert positions['status']['column']==1
    # A modal has window scaling only; widget scaling belongs to the field area.
    form.field_area._get_widget_scaling=lambda:1.5
    Form._layout_fields(form,SimpleNamespace(width=660))
    assert positions['kind']['row']==1
    assert all(p['columnspan']==2 for p in positions.values())
