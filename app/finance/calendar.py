"""Datas, horizonte de projeção e ciclo de fatura de cartão."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal

HorizonPreset = Literal[
    "end_of_month",
    "next_7_days",
    "next_30_days",
    "next_3_months",
    "custom",
]


def parse_iso_date(value: str) -> date:
    text = value.strip()
    if "/" in text:
        day, month, year = text.split("/")
        return date(int(year), int(month), int(day))
    return date.fromisoformat(text[:10])


def to_iso(value: date | str) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return parse_iso_date(value).isoformat()


def add_months(base: date, months: int) -> date:
    year = base.year + (base.month - 1 + months) // 12
    month = (base.month - 1 + months) % 12 + 1
    day = min(base.day, _days_in_month(year, month))
    return date(year, month, day)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        nxt = date(year + 1, 1, 1)
    else:
        nxt = date(year, month + 1, 1)
    return (nxt - timedelta(days=1)).day


def clamp_day(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, _days_in_month(year, month)))


def last_day_of_month(value: date) -> date:
    return clamp_day(value.year, value.month, 31)


@dataclass(frozen=True)
class ForecastHorizon:
    preset: HorizonPreset
    start: date
    end: date

    def contains(self, value: date) -> bool:
        return self.start <= value <= self.end


def build_horizon(
    preset: HorizonPreset,
    today: date,
    custom_end: date | None = None,
) -> ForecastHorizon:
    """O horizonte altera somente a projeção — nunca o saldo atual.

    O saldo previsto considera eventos com data > today e <= end,
    além de obrigações já vencidas e ainda não pagas (até `end`).
    """
    start = today + timedelta(days=1)
    if preset == "end_of_month":
        end = last_day_of_month(today)
        if end <= today:
            end = last_day_of_month(add_months(today, 1))
    elif preset == "next_7_days":
        end = today + timedelta(days=7)
    elif preset == "next_30_days":
        end = today + timedelta(days=30)
    elif preset == "next_3_months":
        end = add_months(today, 3)
    elif preset == "custom":
        if custom_end is None:
            raise ValueError("Horizonte personalizado exige data final.")
        end = custom_end
    else:
        raise ValueError(f"Horizonte desconhecido: {preset}")

    if end < today:
        end = today
    return ForecastHorizon(preset=preset, start=start, end=end)


@dataclass(frozen=True)
class InvoiceCycle:
    closing_date: date
    due_date: date
    period_year: int
    period_month: int


def invoice_cycle_for_purchase(purchase_date: date, closing_day: int, due_day: int) -> InvoiceCycle:
    """Determina a fatura que recebe uma compra na data informada."""
    if purchase_date.day <= closing_day:
        closing = clamp_day(purchase_date.year, purchase_date.month, closing_day)
    else:
        nxt = add_months(date(purchase_date.year, purchase_date.month, 1), 1)
        closing = clamp_day(nxt.year, nxt.month, closing_day)
    return _cycle_from_closing(closing, due_day)


def shift_cycle(cycle: InvoiceCycle, months: int, due_day: int) -> InvoiceCycle:
    closing = add_months(cycle.closing_date, months)
    closing = clamp_day(closing.year, closing.month, cycle.closing_date.day)
    # Prefer the card's closing_day rather than overflow from add_months
    return _cycle_from_closing(clamp_day(closing.year, closing.month, cycle.closing_date.day), due_day)


def _cycle_from_closing(closing: date, due_day: int) -> InvoiceCycle:
    if due_day > closing.day:
        due = clamp_day(closing.year, closing.month, due_day)
    else:
        nxt = add_months(closing, 1)
        due = clamp_day(nxt.year, nxt.month, due_day)
    return InvoiceCycle(
        closing_date=closing,
        due_date=due,
        period_year=closing.year,
        period_month=closing.month,
    )


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat(sep=" ")
