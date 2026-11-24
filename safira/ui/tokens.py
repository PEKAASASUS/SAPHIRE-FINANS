"""Sapphire Tech Finance semantic design tokens; no financial rules."""
BG='#090F1B'
SIDEBAR='#0D1424'
PANEL='#121C2D'
SURFACE='#19253A'
HOVER='#22334D'
BORDER='#27354B'
BLUE='#3478FF'
BRIGHT='#4C8DFF'
VIOLET='#8665FF'
CYAN='#27C9EF'
GREEN='#22D3A0'
RED='#FF6078'
YELLOW='#F5B942'
TEXT='#F3F7FF'
MUTED='#9BAEC8'
QUIET='#7185A2'
SELECTED='#182E53'
SHADOW='#050914'
POS_BG='#12342F'
NEG_BG='#352134'
WARN_BG='#352D20'
FONT='Segoe UI'
NUMBER_FONT='Consolas'
RADIUS=18
SPACE=8
DURATION={'hover':150,'state':200,'enter':260,'modal':220,'chart':480}
CHART_COLORS=(BLUE,VIOLET,CYAN,'#648EFF','#B098FF')

def font(size=13,bold=False,numeric=False):
    return (NUMBER_FONT if numeric else FONT,size,'bold' if bold else 'normal')

def blend(a,b,t):
    t=max(0,min(1,t))
    return '#'+''.join(f'{round(int(a[i:i+2],16)*(1-t)+int(b[i:i+2],16)*t):02x}' for i in (1,3,5))
