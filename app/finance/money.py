"""
Representação monetária do SAFIRA.

Valores financeiros são sempre inteiros em centavos. Nenhum cálculo
de saldo usa float. Conversão de texto (pt-BR) usa Decimal apenas na
borda de entrada/saída.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


class MoneyError(ValueError):
    """Valor monetário inválido informado pelo usuário."""


def reais_to_cents(value: str | int | Decimal) -> int:
    """Converte reais para centavos (inteiro).

    Aceita `int` já em centavos somente quando o chamador usa a API
    interna. Strings do usuário são interpretadas em reais (pt-BR ou
    ponto decimal).
    """
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        quantized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return int(quantized * 100)

    text = str(value).strip().replace("R$", "").strip()
    if not text:
        raise MoneyError("Informe um valor.")
    text = text.replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        quantized = Decimal(text).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise MoneyError("Valor monetário inválido.") from exc
    return int(quantized * 100)


def cents_to_decimal(cents: int) -> Decimal:
    return (Decimal(int(cents)) / Decimal(100)).quantize(Decimal("0.01"))


def format_brl(cents: int) -> str:
    """Formata centavos como R$ 1.234,56 (sinal à esquerda se negativo)."""
    negative = cents < 0
    cents = abs(int(cents))
    whole, frac = divmod(cents, 100)
    whole_txt = f"{whole:,}".replace(",", ".")
    formatted = f"R$ {whole_txt},{frac:02d}"
    return f"-{formatted}" if negative else formatted
