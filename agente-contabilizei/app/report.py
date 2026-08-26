import os
import uuid
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

NAVY = colors.HexColor("#1F4E78")
LIGHT_GREY = colors.HexColor("#F2F2F2")

# Mesma pasta efêmera usada para os gráficos (ver app/charts.py)
RELATORIOS_DIR = "/tmp/graficos_agente"
os.makedirs(RELATORIOS_DIR, exist_ok=True)

_styles = getSampleStyleSheet()
_styles.add(ParagraphStyle("RelTitulo", fontName="Helvetica-Bold", fontSize=16,
                            textColor=NAVY, spaceAfter=8))
_styles.add(ParagraphStyle("RelSubtitulo", fontName="Helvetica", fontSize=9.5,
                            textColor=colors.HexColor("#595959"), spaceAfter=16))


def criar_relatorio_pdf(dados: list[dict], titulo: str, caminho_grafico: str | None = None,
                         filtros_texto: str = "") -> str:
    """
    Monta um PDF de uma página com título, filtros aplicados, o gráfico
    (se fornecido) e uma tabela com os valores exatos. Retorna o caminho
    do arquivo gerado.
    """
    nome_arquivo = f"relatorio_{uuid.uuid4().hex}.pdf"
    caminho = os.path.join(RELATORIOS_DIR, nome_arquivo)

    doc = SimpleDocTemplate(caminho, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    story = []

    story.append(Paragraph(titulo, _styles["RelTitulo"]))
    gerado_em = datetime.now().strftime("%d/%m/%Y %H:%M")
    sub = f"Gerado em {gerado_em} — Mercado de Abertura de Empresas (base 2018-2025)"
    if filtros_texto:
        sub += f" · Filtros: {filtros_texto}"
    story.append(Paragraph(sub, _styles["RelSubtitulo"]))

    if caminho_grafico and os.path.exists(caminho_grafico):
        story.append(Image(caminho_grafico, width=16*cm, height=9*cm))
        story.append(Spacer(1, 14))

    header = [["Categoria", "Total de aberturas"]]
    linhas = [[str(d.get("chave", "")), f'{int(d.get("total", 0) or 0):,}'.replace(",", ".")] for d in dados]
    tabela = Table(header + linhas, colWidths=[8*cm, 6*cm])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tabela)

    doc.build(story)
    return caminho
