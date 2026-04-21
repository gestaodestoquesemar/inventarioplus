"""
pdf_generator.py — Gera relatório PDF profissional usando ReportLab.
"""
import io
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Image
)
from reportlab.lib.colors import HexColor


# ── Paleta de cores ────────────────────────────────────────────────────────────
VERDE_ESCURO  = HexColor("#0f2a1e")
VERDE_MED     = HexColor("#1d9e75")
VERDE_CLARO   = HexColor("#e1f5ee")
VERMELHO      = HexColor("#e24b4a")
VERMELHO_CLARO= HexColor("#fcebeb")
AMBAR         = HexColor("#ba7517")
AMBAR_CLARO   = HexColor("#faeeda")
AZUL          = HexColor("#378add")
CINZA_ESCURO  = HexColor("#444441")
CINZA_MEDIO   = HexColor("#888780")
CINZA_CLARO   = HexColor("#f1efe8")
BRANCO        = colors.white


def _criar_estilos():
    estilos = getSampleStyleSheet()
    base = {"fontName": "Helvetica", "textColor": CINZA_ESCURO}

    e = {}
    e["titulo_capa"] = ParagraphStyle("titulo_capa", fontName="Helvetica-Bold",
        fontSize=28, textColor=BRANCO, alignment=TA_CENTER, leading=34)
    e["sub_capa"] = ParagraphStyle("sub_capa", fontName="Helvetica",
        fontSize=13, textColor=HexColor("#9FE1CB"), alignment=TA_CENTER, leading=18)
    e["h1"] = ParagraphStyle("h1", fontName="Helvetica-Bold",
        fontSize=14, textColor=VERDE_ESCURO, spaceBefore=14, spaceAfter=6, leading=18)
    e["h2"] = ParagraphStyle("h2", fontName="Helvetica-Bold",
        fontSize=11, textColor=VERDE_MED, spaceBefore=8, spaceAfter=4)
    e["body"] = ParagraphStyle("body", fontName="Helvetica",
        fontSize=9, textColor=CINZA_ESCURO, leading=14, spaceAfter=4)
    e["body_bold"] = ParagraphStyle("body_bold", fontName="Helvetica-Bold",
        fontSize=9, textColor=CINZA_ESCURO, leading=14)
    e["small"] = ParagraphStyle("small", fontName="Helvetica",
        fontSize=8, textColor=CINZA_MEDIO, leading=12)
    e["alerta"] = ParagraphStyle("alerta", fontName="Helvetica-Bold",
        fontSize=9, textColor=VERMELHO, leading=12)
    e["alerta_mod"] = ParagraphStyle("alerta_mod", fontName="Helvetica-Bold",
        fontSize=9, textColor=AMBAR, leading=12)
    e["rec"] = ParagraphStyle("rec", fontName="Helvetica",
        fontSize=9, textColor=CINZA_ESCURO, leading=13)
    return e


def _grafico_barras(por_depto):
    """Gera gráfico de barras horizontais e retorna bytes PNG."""
    fig, ax = plt.subplots(figsize=(6, max(2.5, len(por_depto) * 0.5)))
    cores = ["#e24b4a"] * len(por_depto)
    bars = ax.barh(por_depto["departamento"], por_depto["perda"].abs(), color=cores, height=0.55)
    for bar, val in zip(bars, por_depto["perda"]):
        ax.text(bar.get_width() + por_depto["perda"].abs().max() * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"R$ {abs(val):,.0f}", va='center', fontsize=8, color="#444")
    ax.set_xlim(0, por_depto["perda"].abs().max() * 1.35)
    ax.tick_params(axis='both', labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlabel("Valor (R$)", fontsize=8)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _grafico_pizza(causas):
    """Gera pizza de causas raiz."""
    labels = list(causas.keys())
    vals   = list(causas.values())
    cores  = ["#e24b4a", "#ba7517", "#378add", "#7f77dd", "#888780", "#1d9e75"]
    fig, ax = plt.subplots(figsize=(4.5, 3.5))
    wedges, texts, autotexts = ax.pie(
        vals, labels=None, autopct="%1.0f%%",
        colors=cores[:len(labels)], startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
        textprops={"fontsize": 8}
    )
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(0.85, 0.5),
              fontsize=7, frameon=False)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _tabela_kpi(resumo, estilos):
    """Cria tabela de KPIs em 4 colunas."""
    pct_cor = VERMELHO if resumo["pct_perda"] > 2 else VERDE_MED
    dados = [
        [
            Paragraph("<b>Perda Total</b>", estilos["small"]),
            Paragraph("<b>% Perda/Estoque</b>", estilos["small"]),
            Paragraph("<b>Ganhos (ajustes +)</b>", estilos["small"]),
            Paragraph("<b>Itens Auditados</b>", estilos["small"]),
        ],
        [
            Paragraph(f"<b>R$ {abs(resumo['perda_total']):,.2f}</b>", ParagraphStyle(
                "kv", fontName="Helvetica-Bold", fontSize=14, textColor=VERMELHO, alignment=TA_CENTER)),
            Paragraph(f"<b>{resumo['pct_perda']:.2f}%</b>", ParagraphStyle(
                "kv2", fontName="Helvetica-Bold", fontSize=14, textColor=pct_cor, alignment=TA_CENTER)),
            Paragraph(f"<b>R$ {resumo['ganho_total']:,.2f}</b>", ParagraphStyle(
                "kv3", fontName="Helvetica-Bold", fontSize=14, textColor=VERDE_MED, alignment=TA_CENTER)),
            Paragraph(f"<b>{resumo['total_itens']:,}</b>", ParagraphStyle(
                "kv4", fontName="Helvetica-Bold", fontSize=14, textColor=AZUL, alignment=TA_CENTER)),
        ],
        [
            Paragraph(f"{resumo['n_perdas']} itens negativos", estilos["small"]),
            Paragraph("Meta: abaixo de 2%", estilos["small"]),
            Paragraph(f"{resumo['n_ganhos']} itens positivos", estilos["small"]),
            Paragraph(f"{resumo['n_ajustes']} com ajuste", estilos["small"]),
        ],
    ]
    t = Table(dados, colWidths=[4.2 * cm] * 4)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), CINZA_CLARO),
        ("BACKGROUND", (0, 1), (-1, 2), BRANCO),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, 2), [BRANCO, CINZA_CLARO]),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#d0d0d0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor("#e0e0e0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return t


def _tabela_perdas(top_perdas, estilos):
    cabecalho = ["#", "Produto", "Depto", "Qtd", "Valor Perda", "Causa Estimada"]
    linhas = [cabecalho]
    for i, row in top_perdas.iterrows():
        linhas.append([
            str(i + 1),
            str(row["descricao"])[:35],
            str(row["departamento"])[:12],
            str(int(row["quantidade"])),
            f"R$ {abs(row['valor']):,.2f}",
            str(row["causa_estimada"])[:20],
        ])
    t = Table(linhas, colWidths=[0.7*cm, 5.5*cm, 2.2*cm, 1.2*cm, 2.5*cm, 4.5*cm])
    estilo = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE_ESCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), BRANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BRANCO, VERMELHO_CLARO]),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ALIGN", (3, 0), (4, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#d0d0d0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor("#e8e8e8")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ])
    # Destacar valores em vermelho
    for i in range(1, len(linhas)):
        estilo.add("TEXTCOLOR", (4, i), (4, i), VERMELHO)
        estilo.add("FONTNAME", (4, i), (4, i), "Helvetica-Bold")
    t.setStyle(estilo)
    return t


def _tabela_deptos(por_depto, estilos):
    cabecalho = ["Departamento", "Perda (R$)", "% do Total"]
    linhas = [cabecalho]
    for _, row in por_depto.iterrows():
        linhas.append([
            str(row["departamento"]),
            f"R$ {abs(row['perda']):,.2f}",
            f"{row['pct']:.1f}%",
        ])
    t = Table(linhas, colWidths=[6*cm, 5*cm, 5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE_ESCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), BRANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BRANCO, CINZA_CLARO]),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#d0d0d0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor("#e8e8e8")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    for i in range(1, len(linhas)):
        t.setStyle(TableStyle([("TEXTCOLOR", (1, i), (1, i), VERMELHO),
                                ("FONTNAME", (1, i), (1, i), "Helvetica-Bold")]))
    return t


def _pagina_capa(canvas_obj, doc):
    """Desenha a capa verde escura."""
    canvas_obj.saveState()
    w, h = A4
    canvas_obj.setFillColor(VERDE_ESCURO)
    canvas_obj.rect(0, 0, w, h, fill=1, stroke=0)
    canvas_obj.setFillColor(VERDE_MED)
    canvas_obj.rect(0, h * 0.35, w, 4, fill=1, stroke=0)
    canvas_obj.setFillColor(HexColor("#0d2419"))
    canvas_obj.rect(0, 0, w, h * 0.12, fill=1, stroke=0)
    canvas_obj.restoreState()


def _rodape(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.setFillColor(CINZA_MEDIO)
    canvas_obj.drawString(2*cm, 1*cm, f"InventárioPlus — Gerado em {datetime.today().strftime('%d/%m/%Y %H:%M')}")
    canvas_obj.drawRightString(A4[0] - 2*cm, 1*cm, f"Página {doc.page}")
    canvas_obj.restoreState()


def gerar_pdf_relatorio(resultado, observacoes="", limite_alerta=500):
    """
    Gera o relatório PDF completo e retorna bytes.
    """
    resumo      = resultado["resumo"]
    top_perdas  = resultado["top_perdas"]
    top_ganhos  = resultado["top_ganhos"]
    por_depto   = resultado["por_depto"]
    diagnosticos= resultado["diagnosticos"]

    estilos = _criar_estilos()
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="Relatório de Inventário — InventárioPlus"
    )

    story = []

    # ── CAPA ──────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 5*cm))
    story.append(Paragraph("📦 InventárioPlus", estilos["titulo_capa"]))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Relatório de Análise de Inventário", estilos["sub_capa"]))
    story.append(Paragraph("Diagnóstico Automático de Perdas e Prevenção", estilos["sub_capa"]))
    story.append(Spacer(1, 2*cm))

    data_ref = resumo["data_ref"]
    data_str = data_ref.strftime("%d/%m/%Y") if hasattr(data_ref, "strftime") else str(data_ref)
    story.append(Paragraph(f"Data de referência: {data_str}", estilos["sub_capa"]))
    story.append(Paragraph(f"Gerado em: {datetime.today().strftime('%d/%m/%Y às %H:%M')}", estilos["sub_capa"]))
    story.append(PageBreak())

    # ── RESUMO EXECUTIVO ──────────────────────────────────────────────────────
    story.append(Paragraph("1. Resumo Executivo", estilos["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_MED, spaceAfter=10))

    story.append(_tabela_kpi(resumo, estilos))
    story.append(Spacer(1, 0.5*cm))

    pct_str = f"{resumo['pct_perda']:.2f}%"
    meta_str = "ACIMA da meta de 2%" if resumo["pct_perda"] > 2 else "dentro da meta de 2%"
    story.append(Paragraph(
        f"O inventário analisou <b>{resumo['total_itens']:,} produtos</b>, "
        f"sendo <b>{resumo['n_ajustes']} com algum ajuste</b> identificado. "
        f"A perda total foi de <b>R$ {abs(resumo['perda_total']):,.2f}</b>, "
        f"representando <b>{pct_str} do estoque total</b> — {meta_str}. "
        f"Foram identificados <b>{resumo['n_ganhos']} itens com ajuste positivo</b> "
        f"(R$ {resumo['ganho_total']:,.2f}), sugerindo possíveis erros em inventários anteriores.",
        estilos["body"]
    ))
    story.append(Spacer(1, 0.3*cm))

    # ── GRÁFICO DE DEPTOS ─────────────────────────────────────────────────────
    if not por_depto.empty:
        story.append(Paragraph("2. Perdas por Departamento", estilos["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=VERDE_MED, spaceAfter=10))
        story.append(_tabela_deptos(por_depto, estilos))
        story.append(Spacer(1, 0.4*cm))
        try:
            img_buf = _grafico_barras(por_depto)
            img = Image(img_buf, width=14*cm, height=max(4*cm, len(por_depto)*1.2*cm))
            story.append(img)
        except Exception:
            pass

    story.append(PageBreak())

    # ── TOP 10 PERDAS ─────────────────────────────────────────────────────────
    story.append(Paragraph("3. Top 10 — Maiores Perdas Financeiras", estilos["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=VERMELHO, spaceAfter=10))
    if not top_perdas.empty:
        story.append(_tabela_perdas(top_perdas, estilos))
    story.append(Spacer(1, 0.5*cm))

    # ── TOP GANHOS ────────────────────────────────────────────────────────────
    story.append(Paragraph("4. Top Ganhos — Possíveis Erros de Inventário Anterior", estilos["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_MED, spaceAfter=10))
    if not top_ganhos.empty:
        cab = ["#", "Produto", "Departamento", "Qtd", "Valor Ganho"]
        linhas_g = [cab] + [
            [str(i+1), str(r["descricao"])[:38], str(r["departamento"])[:15],
             str(int(r["quantidade"])), f"R$ {r['valor']:,.2f}"]
            for i, r in top_ganhos.iterrows()
        ]
        tg = Table(linhas_g, colWidths=[0.7*cm, 6.5*cm, 3*cm, 1.3*cm, 3*cm])
        tg.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), VERDE_ESCURO),
            ("TEXTCOLOR", (0, 0), (-1, 0), BRANCO),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BRANCO, VERDE_CLARO]),
            ("ALIGN", (3, 0), (4, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.5, HexColor("#d0d0d0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor("#e8e8e8")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        for i in range(1, len(linhas_g)):
            tg.setStyle(TableStyle([("TEXTCOLOR", (4, i), (4, i), VERDE_MED),
                                     ("FONTNAME", (4, i), (4, i), "Helvetica-Bold")]))
        story.append(tg)

    story.append(PageBreak())

    # ── DIAGNÓSTICO ───────────────────────────────────────────────────────────
    story.append(Paragraph("5. Diagnóstico Automático", estilos["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=VERMELHO, spaceAfter=10))

    for d in diagnosticos.get("alertas_criticos", []):
        story.append(Paragraph(f"⚠ {d['titulo']}", estilos["alerta"]))
        story.append(Paragraph(d["descricao"], estilos["body"]))
        story.append(Spacer(1, 0.2*cm))

    for d in diagnosticos.get("alertas_moderados", []):
        story.append(Paragraph(f"► {d['titulo']}", estilos["alerta_mod"]))
        story.append(Paragraph(d["descricao"], estilos["body"]))
        story.append(Spacer(1, 0.2*cm))

    # Gráfico pizza causas
    causas = diagnosticos.get("distribuicao_causas", {})
    if causas:
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("Distribuição de Causas Raiz (estimativa):", estilos["h2"]))
        try:
            pizza_buf = _grafico_pizza(causas)
            story.append(Image(pizza_buf, width=10*cm, height=7*cm))
        except Exception:
            pass

    # ── RECOMENDAÇÕES ─────────────────────────────────────────────────────────
    story.append(Paragraph("6. Recomendações Práticas", estilos["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=VERDE_MED, spaceAfter=10))

    prioridade_cor = {"ALTA": VERMELHO, "MÉDIA": AMBAR, "BAIXA": VERDE_MED}
    for rec in diagnosticos.get("recomendacoes", []):
        cor = prioridade_cor.get(rec["prioridade"], CINZA_ESCURO)
        story.append(Paragraph(
            f'<font color="#{cor.hexval()[2:]}"><b>[{rec["prioridade"]}]</b></font> {rec["texto"]}',
            estilos["rec"]
        ))
        story.append(Spacer(1, 0.1*cm))

    # ── OBSERVAÇÕES ───────────────────────────────────────────────────────────
    if observacoes and observacoes.strip():
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("7. Observações do Analista", estilos["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=CINZA_MEDIO, spaceAfter=8))
        story.append(Paragraph(observacoes, estilos["body"]))

    # ── BUILD ─────────────────────────────────────────────────────────────────
    def primeira_pagina(canvas_obj, doc_obj):
        _pagina_capa(canvas_obj, doc_obj)

    def paginas_seguintes(canvas_obj, doc_obj):
        _rodape(canvas_obj, doc_obj)

    doc.build(story, onFirstPage=primeira_pagina, onLaterPages=paginas_seguintes)
    buf.seek(0)
    return buf.read()
