from types import SimpleNamespace
import pytest
from safira.presentation_dates import date_br,date_iso,month_br
from safira.ui.controls import SapphireDatePicker


@pytest.mark.parametrize('raw,iso,display',[
    ('04/11/2026','2026-11-04','04/11/2026'),
    ('2026-11-04','2026-11-04','04/11/2026'),
    ('03/04/2026','2026-04-03','03/04/2026'),
    ('29/02/2024','2024-02-29','29/02/2024'),
])
def test_dates_roundtrip_and_datepicker_contract(raw,iso,display):
    assert date_iso(raw)==iso
    assert date_br(raw)==display
    inserted=[]
    picker=SimpleNamespace(entry=SimpleNamespace(get=lambda:display,
        insert=lambda index,value:inserted.append((index,value))))
    assert SapphireDatePicker.get(picker)==iso
    SapphireDatePicker.insert(picker,0,iso)
    assert inserted==[(0,display)]


@pytest.mark.parametrize('raw',['29/02/2025','31/04/2026','04/31/2026','4/11/2026','2026-13-01','abc'])
def test_invalid_dates_have_brazilian_format_hint(raw):
    with pytest.raises(ValueError,match='DD/MM/AAAA'):
        date_iso(raw)


def test_months_optional_dates_and_non_date_labels():
    assert month_br('2026-11')=='11/2026'
    assert date_br(None)==''
    assert date_br('Pendente')=='Pendente'
    picker=SimpleNamespace(entry=SimpleNamespace(get=lambda:''))
    assert SapphireDatePicker.get(picker)==''


def test_form_keeps_save_available_after_invalid_date():
    from safira.ui.dialogs import Form
    state={'state':'normal'}
    errors=[]
    def invalid():
        return date_iso('31/02/2026')
    form=SimpleNamespace(
        save_button=SimpleNamespace(cget=lambda key:state[key],configure=lambda **kw:state.update(kw)),
        choices={},fields={'date':SimpleNamespace(get=invalid)},
        on_save=lambda _:pytest.fail('Invalid date reached financial service'),
        error=SimpleNamespace(configure=lambda **kw:errors.append(kw['text'])))
    Form.save(form)
    assert state['state']=='normal'
    assert len(errors)==1 and 'DD/MM/AAAA' in errors[0]
