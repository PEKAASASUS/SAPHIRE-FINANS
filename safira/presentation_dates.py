"""Date formatting at presentation boundaries; storage remains ISO 8601."""
from datetime import date, datetime
import re


def date_iso(value):
    text=str(value).strip()
    try:
        if re.fullmatch(r'\d{2}/\d{2}/\d{4}',text):
            return datetime.strptime(text,'%d/%m/%Y').date().isoformat()
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}',text):
            return date.fromisoformat(text).isoformat()
    except ValueError:
        pass
    raise ValueError('Informe uma data válida no formato DD/MM/AAAA.')


def date_br(value):
    if value is None:return ''
    try:
        parsed=date.fromisoformat(date_iso(value))
        return f'{parsed.day:02d}/{parsed.month:02d}/{parsed.year:04d}'
    except ValueError:
        return str(value)


def month_br(value):
    text=str(value)
    if re.fullmatch(r'\d{4}-\d{2}',text):
        try:
            parsed=date.fromisoformat(text+'-01')
            return f'{parsed.month:02d}/{parsed.year:04d}'
        except ValueError:pass
    return text
