"""Presentation-only preferences; no schema change or financial migrations."""
import json,os,tempfile
from pathlib import Path


def system_reduced_motion():
    try:
        import ctypes
        value=ctypes.c_int(1)
        return bool(ctypes.windll.user32.SystemParametersInfoW(0x1042,0,ctypes.byref(value),0) and not value.value)
    except (AttributeError,OSError):return False


class Preferences:
    def __init__(self,folder):
        self.path=Path(folder)/'ui-preferences.json'
        self.values={'reduce_motion':system_reduced_motion(),'scale':100}
        try:
            data=json.loads(self.path.read_text(encoding='utf-8'))
            if type(data.get('reduce_motion')) is bool:self.values['reduce_motion']=data['reduce_motion']
            if data.get('scale') in (90,100,110,125,150):self.values['scale']=data['scale']
        except (OSError,ValueError,AttributeError):pass

    def save(self,reduced,scale):
        if scale not in (90,100,110,125,150):raise ValueError('Escala inválida.')
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.values={'reduce_motion':bool(reduced),'scale':scale}
        handle,tmp=tempfile.mkstemp(dir=self.path.parent,suffix='.ui-tmp')
        try:
            with os.fdopen(handle,'w',encoding='utf-8') as file:json.dump(self.values,file)
            os.replace(tmp,self.path)
        finally:Path(tmp).unlink(missing_ok=True)
