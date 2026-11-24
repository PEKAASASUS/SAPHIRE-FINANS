"""Offline Ariquemes/RO calendar for the user's Monday-Friday salary rule.

Sources and limitations: docs/PLANNING_CALENDAR.md. Optional government closures
are deliberately not classified as employer holidays.
"""
from datetime import date, timedelta


def easter(year):
    a=year%19; b=year//100; c=year%100; d=b//4; e=b%4
    f=(b+8)//25; g=(b-f+1)//3; h=(19*a+b-d-g+15)%30
    i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7; m=(a+11*h+22*l)//451
    return date(year,(h+l-7*m+114)//31,(h+l-7*m+114)%31+1)


def holidays(year):
    fixed=((1,1),(1,4),(4,21),(5,1),(9,7),(10,4),(10,11),(10,12),
           (11,2),(11,15),(11,20),(12,25))
    return {date(year,m,d) for m,d in fixed}|{easter(year)-timedelta(days=2)}


def fifth_business_day(year,month,overrides=None):
    overrides=overrides or {}
    day=date(year,month,1); count=0; closed=holidays(year)
    while count<5:
        working=overrides.get(day.isoformat(),day.weekday()<5 and day not in closed)
        if working:count+=1
        if count<5:day+=timedelta(days=1)
        if day.month!=month:raise ValueError('Calendário sem cinco dias úteis neste mês.')
    return day.isoformat()
