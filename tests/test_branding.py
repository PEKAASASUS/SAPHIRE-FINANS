from pathlib import Path
from PIL import Image
from safira.branding import brand_file


def test_brand_assets_and_frozen_resource_layout(monkeypatch,tmp_path):
    for kind in ('logo','icon','ico'):
        assert brand_file(kind).is_file()
        with Image.open(brand_file(kind)) as image:
            image.verify()
    monkeypatch.setattr('sys._MEIPASS',str(tmp_path),raising=False)
    assert brand_file('logo')==tmp_path/'assets'/'brand'/'safira-logo-horizontal-transparente.png'
    assert brand_file('ico')==tmp_path/'assets'/'brand'/'favicon-transparente.ico'


def test_current_brand_keeps_source_transparency():
    for kind in ('logo','icon','ico'):
        with Image.open(brand_file(kind)) as image:
            assert image.mode=='RGBA'
            assert image.getchannel('A').getextrema()==(0,255)
