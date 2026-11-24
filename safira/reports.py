from safira.presentation_dates import date_br
from safira.branding import brand_file
from safira.ui.tokens import SIDEBAR
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from safira.domain import brl,LABELS


def export_pdf(path,report,commitments,invoices):
    """One immutable report snapshot, shared with the screen's calculations."""
    styles=getSampleStyleSheet()
    styles['Heading2'].keepWithNext=True
    elements=[]
    def text(value,style='Normal'):
        return Paragraph(escape(str(value)),styles[style])
    def section(name,headers,rows,widths=None):
        elements.extend([Spacer(1,14),text(name,'Heading2')])
        if not rows:
            elements.append(text('Nenhum registro neste período.'))
            return
        table=Table([[text(h) for h in headers]]+[[text(cell) for cell in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDE7FA')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#CCD2DC')),
            ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        elements.append(table)
    logo=Image(str(brand_file('logo')),width=180,height=180*420/1285)
    banner=Table([[logo]],colWidths=[196],hAlign='CENTER')
    banner.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor(SIDEBAR)),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    elements.append(banner)
    elements.extend([Spacer(1,8),text('Relatório financeiro','Title'),text(f"Período: {date_br(report['start'])} a {date_br(report['end'])}"),
        text('Consumo por competência separado do fluxo efetivo de caixa.'),text('Gerado em '+datetime.now().strftime('%d/%m/%Y %H:%M'))])
    section('Resumo do período',['Receitas','Despesas por competência','Resultado','Entradas de caixa','Saídas de caixa'],
        [[brl(report[k]) for k in ('income_cents','expense_cents','result_cents','cash_in_cents','cash_out_cents')]])
    section('Patrimônio atual (data de geração)',['Disponível','Reservas','Investido','Dívida de crédito','Patrimônio líquido'],
        [[brl(report[k]) for k in ('available_cents','reserved_cents','invested_cents','debt_cents','net_cents')]])
    section('Despesas por categoria',['Categoria','Valor'],[[k,brl(v)] for k,v in report['categories'].items()],[500,250])
    section('Saldos atuais por conta',['Conta','Tipo','Caixa','Investido'],
        [[r['name'],LABELS[r['kind']],brl(r['balance_cents']),brl(r['invested_cents'])] for r in report['balances']],[260,190,150,150])
    if report.get('forecast'):
        forecast=report['forecast']
        section('Planejamento: projeção a partir de hoje',['Saldo real','Saldo previsto'],[[brl(forecast['real_cents']),brl(forecast['projected_cents'])]],[375,375])
        section('Eventos previstos',['Vencimento','Origem','Descrição','Efeito'],
            [[date_br(r['due']),r['source'],r['title'],brl(r['delta'])] for r in forecast['events']],[90,150,360,150])
    section('Operações e transferências',['Data','Descrição','Tipo','Contas','Estado','Valor'],
        [[date_br(r['occurred']),r['description'],LABELS[r['kind']],r['accounts'] or '',LABELS[r['status']],brl(r['amount_cents'])] for r in report['operations']], [70,190,90,190,90,120])
    section('Consumo no crédito',['Competência','Descrição','Categoria','Valor'],
        [[date_br(r['occurred']),r['description'],r['category'],brl(r['amount_cents'])] for r in report['consumption']],[90,280,240,140])
    section('Compromissos do período',['Vencimento','Descrição','Estado','Valor'],
        [[date_br(r['due']),r['title'],LABELS[r['state']],brl(r['amount_cents'])] for r in commitments],[90,340,180,140])
    section('Faturas com vencimento no período',['Cartão','Fechamento','Vencimento','Total','Pago','Restante'],
        [[r['card'],date_br(r['closing']),date_br(r['due']),brl(r['total_cents']),brl(r['paid_cents']),brl(r['remaining_cents'])] for r in invoices],[190,90,90,125,125,130])
    def page(canvas,doc):
        canvas.setFont('Helvetica',8)
        canvas.setFillColor(colors.HexColor('#526174'))
        canvas.drawString(34,20,'SAFIRA 3.1.0 • Dados locais • BRL')
        canvas.drawRightString(805,20,f'Página {doc.page}')
    path=Path(path)
    SimpleDocTemplate(str(path),pagesize=landscape(A4),leftMargin=34,rightMargin=34,topMargin=28,bottomMargin=34,
        title='SAFIRA - Relatório financeiro',author='SAFIRA').build(elements,onFirstPage=page,onLaterPages=page)
    return path
