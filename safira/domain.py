"""Pure monetary and calendar rules; no UI or persistence dependencies."""
import calendar
import re
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


class ValidationError(ValueError):
    pass


LABELS={'bank':'Banco','wallet':'Carteira','reserve':'Reserva','brokerage':'Corretora',
 'income':'Receita','expense':'Despesa','transfer':'Transferência','invoice_payment':'Pagamento de fatura',
 'investment':'Aporte / resgate','pending':'Pendente','confirmed':'Confirmado','cancelled':'Cancelado',
 'paid':'Pago','ignored':'Ignorado','postponed':'Adiado','credit':'Crédito','debit':'Débito'}


def money(value: str | Decimal | int) -> int:
    """Reais to cents. Integer input means reais; floats deliberately rejected."""
    if isinstance(value, bool) or isinstance(value, float):
        raise ValidationError('Informe dinheiro como texto, nunca float.')
    text = str(value).strip().replace('R$', '').replace(' ', '')
    if ',' in text:
        if not re.fullmatch(r'[+-]?(?:\d{1,3}(?:\.\d{3})+|\d+),\d{1,2}', text):
            raise ValidationError('Valor inválido. Exemplo: 1.250,90.')
        text = text.replace('.', '').replace(',', '.')
    elif not re.fullmatch(r'[+-]?\d+(?:\.\d{1,2})?', text):
        raise ValidationError('Valor inválido. Exemplo: 1250,90.')
    try:
        result = int((Decimal(text) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError):
        raise ValidationError('Valor monetário inválido.') from None
    if abs(result) > 10**14:
        raise ValidationError('Valor acima do limite suportado.')
    return result


def cents(value: int, positive=False) -> int:
    if type(value) is not int or abs(value) > 10**14 or (positive and value <= 0):
        raise ValidationError('Valor em centavos inválido.')
    return value


def brl(value: int) -> str:
    sign = '-' if value < 0 else ''
    whole, fraction = divmod(abs(value), 100)
    return f'{sign}R$ {whole:,}'.replace(',', '.') + f',{fraction:02d}'


def iso(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except (ValueError, TypeError):
        raise ValidationError('Data inválida. Use AAAA-MM-DD.') from None


def add_months(value: str, count: int, day: int | None = None) -> str:
    original = date.fromisoformat(iso(value))
    month = original.year * 12 + original.month - 1 + count
    year, index = divmod(month, 12)
    month = index + 1
    return date(year, month, min(day or original.day, calendar.monthrange(year, month)[1])).isoformat()


def split_installments(amount: int, count: int) -> list[int]:
    cents(amount, True)
    if type(count) is not int or not 1 <= count <= 120 or count > amount:
        raise ValidationError('Parcelamento inválido (1 a 120, sem parcelas zeradas).')
    part, remainder = divmod(amount, count)
    return [part + (index < remainder) for index in range(count)]


def invoice_dates(purchased: str, closing_day: int, due_day: int) -> tuple[str, str]:
    if not (1 <= closing_day <= 31 and 1 <= due_day <= 31):
        raise ValidationError('Dias de fechamento/vencimento: 1 a 31.')
    current = date.fromisoformat(iso(purchased))
    close = add_months(purchased, 0, closing_day)
    if purchased >= close:
        close = add_months(purchased, 1, closing_day)
    due = add_months(close, 0, due_day)
    if due <= close:
        due = add_months(close, 1, due_day)
    return close, due
