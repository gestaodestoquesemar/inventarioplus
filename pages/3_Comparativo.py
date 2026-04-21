"""
pages/3_Comparativo.py — Compara dois inventários do histórico.
"""
import streamlit as st
import json
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from auth_guard import exigir_login, topbar
from database import listar_analises

st.set_page_config(page_title="Comparativo — InventárioPlus", page_icon="📈", layout="wide")
usuario = exigir_login()
topbar(usuario)

with st.sidebar:
    st.page_link("pages/1_Dashboard.py",    label="📊 Dashboard")
    st.page_link("pages/2_Historico.py",    label="📋 Histórico")
    st.page_link("pages/3_Comparativo.py",  label="📈 Comparativo")
    st.page_link("pages/4_Configuracoes.py",label="⚙️ Configurações")

st.markdown("## 📈 Comparativo entre Inventários")
st.caption("Selecione dois inventários salvos para comparar indicadores lado a lado.")

analises = listar_analises(usuario["id"] if usuario.get("role") != "admin" else None, limit=50)

if len(analises) < 2:
    st.info("Você precisa ter pelo menos 2 análises salvas para usar o comparativo.")
    st.page_link("pages/1_Dashboard.py", label="→ Ir ao Dashboard para importar e salvar análises")
    st.stop()

opcoes = {f"#{a['id']} — {a['nome_arquivo']} ({a['criado_em'][:10]})": a for a in analises}
nomes  = list(opcoes.keys())

col_a, col_b = st.columns(2)
sel_a = col_a.selectbox("Inventário A (base)", nomes, index=0)
sel_b = col_b.selectbox("Inventário B (comparação)", nomes, index=min(1, len(nomes)-1))

if sel_a == sel_b:
    st.warning("Selecione dois inventários diferentes.")
    st.stop()

inv_a = opcoes[sel_a]
inv_b = opcoes[sel_b]

# ── KPIs comparativos ──────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">Comparação de Indicadores</div>', unsafe_allow_html=True)

def _delta_badge(val_a, val_b, menor_melhor=True):
    if val_a == 0:
        return ""
    diff = val_b - val_a
    pct  = diff / abs(val_a) * 100
    if menor_melhor:
        cor  = "#e24b4a" if diff > 0 else "#1d9e75"
        icon = "▲" if diff > 0 else "▼"
    else:
        cor  = "#1d9e75" if diff > 0 else "#e24b4a"
        icon = "▲" if diff > 0 else "▼"
    return f'<span style="color:{cor};font-weight:700">{icon} {abs(pct):.1f}%</span>'

metricas = [
    ("Perda Total (R$)", abs(inv_a["perda_total"]), abs(inv_b["perda_total"]), True),
    ("% Perda / Estoque", inv_a["pct_perda"]*100 if inv_a["pct_perda"]<1 else inv_a["pct_perda"],
                          inv_b["pct_perda"]*100 if inv_b["pct_perda"]<1 else inv_b["pct_perda"], True),
    ("Ganhos (R$)",       inv_a["ganho_total"],     inv_b["ganho_total"],     False),
    ("Itens auditados",   inv_a["total_itens"],      inv_b["total_itens"],     False),
    ("Ajustes realizados",inv_a["n_ajustes"],        inv_b["n_ajustes"],       True),
]

header_cols = st.columns([2,1,1,1])
header_cols[0].markdown("**Indicador**")
header_cols[1].markdown(f"**A:** {inv_a['nome_arquivo'][:20]}")
header_cols[2].markdown(f"**B:** {inv_b['nome_arquivo'][:20]}")
header_cols[3].markdown("**Variação A→B**")

for nome, va, vb, menor_melhor in metricas:
    cs = st.columns([2,1,1,1])
    cs[0].markdown(nome)
    fmt = ".2f" if isinstance(va, float) else ",.0f"
    cs[1].markdown(f"**{va:{fmt}}**")
    cs[2].markdown(f"**{vb:{fmt}}**")
    cs[3].markdown(_delta_badge(va, vb, menor_melhor), unsafe_allow_html=True)

# ── Gráfico comparativo por departamento ───────────────────────────────────────
st.markdown('<div class="section-title">Perdas por Departamento — A vs B</div>', unsafe_allow_html=True)
try:
    dep_a = pd.DataFrame(json.loads(inv_a["por_depto_json"])).rename(columns={"perda":"perda_a"})
    dep_b = pd.DataFrame(json.loads(inv_b["por_depto_json"])).rename(columns={"perda":"perda_b"})
    merged = dep_a.merge(dep_b, on="departamento", how="outer").fillna(0)

    fig, ax = plt.subplots(figsize=(10, max(3, len(merged)*0.6)))
    x = range(len(merged))
    w = 0.35
    bars_a = ax.barh([i - w/2 for i in x], merged["perda_a"].abs(), w, label="Inventário A", color="#e24b4a", alpha=0.85)
    bars_b = ax.barh([i + w/2 for i in x], merged["perda_b"].abs(), w, label="Inventário B", color="#378add", alpha=0.85)
    ax.set_yticks(list(x))
    ax.set_yticklabels(merged["departamento"], fontsize=9)
    ax.set_xlabel("R$", fontsize=9)
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
except Exception as e:
    st.warning(f"Não foi possível gerar o gráfico: {e}")

# ── Evolução temporal (todos os inventários) ───────────────────────────────────
st.markdown('<div class="section-title">Evolução de Perdas — Todos os Inventários</div>', unsafe_allow_html=True)
if len(analises) >= 2:
    try:
        datas  = [a["criado_em"][:10] for a in reversed(analises)]
        perdas = [abs(a["perda_total"]) for a in reversed(analises)]
        fig3, ax3 = plt.subplots(figsize=(10, 3.5))
        ax3.plot(datas, perdas, marker="o", color="#e24b4a", linewidth=2)
        ax3.fill_between(datas, perdas, alpha=0.08, color="#e24b4a")
        ax3.set_ylabel("Perda Total (R$)", fontsize=9)
        ax3.tick_params(axis="x", rotation=30, labelsize=8)
        ax3.tick_params(axis="y", labelsize=8)
        ax3.spines["top"].set_visible(False)
        ax3.spines["right"].set_visible(False)
        ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,p: f"R${x:,.0f}"))
        fig3.tight_layout()
        st.pyplot(fig3)
        plt.close(fig3)
    except Exception:
        pass
