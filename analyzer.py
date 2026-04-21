"""
analyzer.py — Motor de análise inteligente. Detecta colunas automaticamente,
calcula perdas/ganhos e gera diagnóstico com causa raiz.
"""
import pandas as pd
import numpy as np
from datetime import datetime

MAPA_COLUNAS = {
    "codigo":       ["código","codigo","cod","cod_produto","ean","id","codigoproduto"],
    "descricao":    ["descrição","descricao","produto","item","nome","description","nomeproduto"],
    "quantidade":   ["quantidade","qtd","qtd_ajuste","quantidadeajustada","ajuste_qtd","qty","quant"],
    "valor":        ["valor","vlr","vlr_ajuste","valorajuste","ajuste_vlr","value","valortotal","valorajustado"],
    "data":         ["data","dt","dt_inventario","datainventario","date","datainventário","data_inventario"],
    "departamento": ["departamento","depto","dept","seção","secao","categoria","category","secção","sessão","sessao"],
}


def _detectar(cols, candidatos):
    cl = {c.lower().strip().replace(" ","").replace("_","").replace("-",""): c for c in cols}
    for cand in candidatos:
        key = cand.lower().replace(" ","").replace("_","").replace("-","")
        if key in cl:
            return cl[key]
    return None


def _causa(row):
    qtd   = abs(row.get("quantidade", 0) or 0)
    val   = abs(row.get("valor", 0) or 0)
    depto = str(row.get("departamento", "")).upper().strip()
    preco = val / qtd if qtd > 0 else 0

    flv_deptos  = {"FLV","HORTIFRUTI","FRUTAS","LEGUMES","VERDURAS","HORTIFRUTIGRANJEIROS"}
    frio_deptos = {"FRIOS","LATICÍNIOS","LATICINIOS","RESFRIADOS","REFRIGERADOS","CONGELADOS"}
    pad_deptos  = {"PADARIA","CONFEITARIA","PANIFICAÇÃO","PANIFICACAO"}
    acou_deptos = {"AÇOUGUE","ACOUGUE","PEIXARIA","CARNES"}

    if depto in flv_deptos:
        return "Quebra operacional (FLV)" if qtd <= 50 else "Erro de contagem"
    if depto in frio_deptos:
        return "Vencimento / Armazenamento"
    if depto in pad_deptos:
        return "Quebra operacional (Padaria)"
    if depto in acou_deptos:
        return "Quebra operacional (Açougue)" if preco < 80 else "Possível desvio"
    if preco > 80:
        return "Possível desvio"
    if qtd > 100:
        return "Erro de contagem"
    if preco < 5 and qtd > 30:
        return "Erro de cadastro"
    return "Quebra operacional"


def analisar_inventario(arquivo, limite_alerta=500):
    df_raw = pd.read_excel(arquivo)

    mapa = {campo: _detectar(df_raw.columns, cands) for campo, cands in MAPA_COLUNAS.items()}

    for ob in ["descricao", "quantidade", "valor"]:
        if mapa[ob] is None:
            raise ValueError(
                f"Coluna '{ob}' não encontrada. Disponíveis: {list(df_raw.columns)}"
            )

    df = pd.DataFrame()
    df["codigo"]       = df_raw[mapa["codigo"]].astype(str) if mapa["codigo"] else "N/D"
    df["descricao"]    = df_raw[mapa["descricao"]].astype(str).str.strip()
    df["quantidade"]   = pd.to_numeric(df_raw[mapa["quantidade"]], errors="coerce").fillna(0)
    df["valor"]        = pd.to_numeric(df_raw[mapa["valor"]], errors="coerce").fillna(0)
    df["departamento"] = (df_raw[mapa["departamento"]].astype(str).str.strip()
                          if mapa["departamento"] else pd.Series(["Geral"] * len(df_raw)))
    df["data"] = (pd.to_datetime(df_raw[mapa["data"]], errors="coerce", dayfirst=True)
                  if mapa["data"] else pd.NaT)

    df["departamento"] = df["departamento"].fillna("Sem depto")
    df["tipo"] = df["valor"].apply(lambda v: "perda" if v < 0 else ("ganho" if v > 0 else "neutro"))
    df["causa_estimada"] = df.apply(_causa, axis=1)

    perdas = df[df["tipo"] == "perda"].copy()
    ganhos = df[df["tipo"] == "ganho"].copy()

    perda_total    = perdas["valor"].sum()
    ganho_total    = ganhos["valor"].sum()
    estoque_total  = df["valor"].abs().sum()
    pct_perda      = (abs(perda_total) / estoque_total * 100) if estoque_total > 0 else 0

    resumo = {
        "perda_total":   perda_total,
        "ganho_total":   ganho_total,
        "pct_perda":     pct_perda,
        "total_itens":   len(df),
        "n_perdas":      len(perdas),
        "n_ganhos":      len(ganhos),
        "n_ajustes":     len(df[df["tipo"] != "neutro"]),
        "estoque_total": estoque_total,
        "data_ref":      df["data"].dropna().max() if not df["data"].dropna().empty else datetime.today(),
    }

    top_perdas = perdas.sort_values("valor", ascending=True).head(10).reset_index(drop=True)
    top_ganhos = ganhos.sort_values("valor", ascending=False).head(10).reset_index(drop=True)

    por_depto = (
        perdas.groupby("departamento")["valor"].sum()
        .reset_index().rename(columns={"valor":"perda"})
        .sort_values("perda", ascending=True)
    )
    por_depto["pct"] = (por_depto["perda"].abs() / abs(perda_total) * 100).round(1) if perda_total != 0 else 0

    causas_raw  = perdas.groupby("causa_estimada")["valor"].sum().abs()
    dist_causas = (causas_raw / causas_raw.sum() * 100).round(1).to_dict() if len(causas_raw) > 0 else {}

    # ── Diagnósticos ──────────────────────────────────────────────────────────
    alertas_criticos  = []
    alertas_moderados = []
    recomendacoes     = []

    if not por_depto.empty:
        pior = por_depto.iloc[0]
        alertas_criticos.append({
            "titulo": f"Depto crítico: {pior['departamento']} com {pior['pct']:.1f}% das perdas",
            "descricao": (f"{pior['departamento']} registrou R$ {abs(pior['perda']):,.2f} em perdas "
                          f"({pior['pct']:.1f}% do total). Requer ação imediata.")
        })
        recomendacoes.append({"prioridade":"ALTA",
            "texto": f"Auditar processos de recebimento e armazenamento em {pior['departamento']}."})

    if pct_perda > 2:
        alertas_criticos.append({
            "titulo": f"Índice {pct_perda:.2f}% — acima da meta de 2%",
            "descricao": f"O índice está {pct_perda-2:.2f}% acima da meta, indicando problemas operacionais."
        })
        recomendacoes.append({"prioridade":"ALTA",
            "texto": "Revisar metodologia de contagem e treinamento da equipe de inventário."})

    n_desvio = len(perdas[perdas["causa_estimada"] == "Possível desvio"])
    if n_desvio > 0:
        val_dev = perdas[perdas["causa_estimada"] == "Possível desvio"]["valor"].sum()
        alertas_criticos.append({
            "titulo": f"{n_desvio} item(s) com padrão de possível desvio — R$ {abs(val_dev):,.2f}",
            "descricao": "Produtos de alto valor com perdas incompatíveis com quebra operacional. Investigar."
        })
        recomendacoes.append({"prioridade":"ALTA",
            "texto": "Acionar equipe de prevenção de perdas para análise de câmeras e registros de acesso."})

    n_contagem = len(perdas[perdas["causa_estimada"] == "Erro de contagem"])
    if n_contagem > 3:
        alertas_moderados.append({
            "titulo": f"{n_contagem} produtos com possível erro de contagem",
            "descricao": f"Ajuste incompatível com histórico esperado. Recontagem seletiva recomendada."
        })
        recomendacoes.append({"prioridade":"MÉDIA",
            "texto": f"Recontagem cega dos {min(n_contagem,20)} itens com maior desvio percentual."})

    if ganho_total > abs(perda_total) * 0.15:
        alertas_moderados.append({
            "titulo": "Ganhos representam >15% das perdas — possíveis erros em inventários anteriores",
            "descricao": f"R$ {ganho_total:,.2f} em ajustes positivos sugerem falha metodológica anterior."
        })
        recomendacoes.append({"prioridade":"MÉDIA",
            "texto": "Comparar itens com ganho recorrente para identificar falhas sistemáticas."})

    recomendacoes += [
        {"prioridade":"MÉDIA",  "texto":"Implementar inventário rotativo nos 200 itens de maior valor unitário."},
        {"prioridade":"BAIXA",  "texto":"Validar cadastros de produtos com divergência quantidade × valor unitário."},
        {"prioridade":"BAIXA",  "texto":"Documentar quebras operacionais no momento em que ocorrem (antes do inventário)."},
        {"prioridade":"BAIXA",  "texto":"Verificar calibração de balanças e coletores de dados antes de cada inventário."},
    ]

    alertas = []
    if limite_alerta > 0:
        for _, row in perdas[perdas["valor"].abs() >= limite_alerta].sort_values("valor").head(10).iterrows():
            alertas.append({"produto": row["descricao"], "departamento": row["departamento"], "valor": row["valor"]})

    return {
        "df": df,
        "resumo": resumo,
        "top_perdas": top_perdas,
        "top_ganhos": top_ganhos,
        "por_depto": por_depto,
        "diagnosticos": {
            "alertas_criticos":   alertas_criticos,
            "alertas_moderados":  alertas_moderados,
            "recomendacoes":      recomendacoes,
            "distribuicao_causas": dist_causas,
        },
        "alertas": alertas,
    }
