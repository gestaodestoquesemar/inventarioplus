"""
pages/1_Dashboard.py — Painel principal: upload, análise automática e diagnóstico.
"""
import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json
from auth_guard import exigir_login, topbar
from analyzer import analisar_inventario
from database import salvar_analise
from pdf_generator import gerar_pdf_relatorio
from excel_generator import gerar_excel_relatorio

st.set_page_config(page_title="Dashboard — InventárioPlus", page_icon="📊", layout="wide")

usuario = exigir_login()
topbar(usuario)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Importar Inventário")
    arquivo = st.file_uploader("Arquivo Excel (.xlsx)", type=["xlsx"],
        help="O sistema detecta automaticamente as colunas.")
    st.markdown("---")
    limite_alerta = st.number_input("Alerta: perdas acima de (R$)", min_value=0, value=500, step=100)
    st.markdown("---")
    st.markdown("### 🔗 Navegação")
    st.page_link("pages/1_Dashboard.py", label="📊 Dashboard", icon="📊")
    st.page_link("pages/2_Historico.py", label="📋 Histórico", icon="📋")
    st.page_link("pages/3_Comparativo.py", label="📈 Comparativo", icon="📈")
    st.page_link("pages/4_Configuracoes.py", label="⚙️ Configurações", icon="⚙️")
    st.markdown("---")
    st.markdown("### 📋 Formato esperado")
    st.markdown("""
    | Coluna | Exemplo |
    |--------|---------|
    | Código | 7891234 |
    | Descrição | Banana kg |
    | Quantidade | -18 |
    | Valor | -54.00 |
    | Data | 10/05/2025 |
    | Departamento | FLV |
    """)

# ── Sem arquivo ────────────────────────────────────────────────────────────────
if arquivo is None:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;background:white;border-radius:16px;border:2px dashed #d0d0d0">
      <div style="font-size:52px;margin-bottom:16px">📂</div>
      <div style="font-size:18px;font-weight:700;color:#1a1a1a;margin-bottom:8px">Faça upload do arquivo de inventário</div>
      <div style="font-size:14px;color:#888">Selecione o arquivo <b>.xlsx</b> na barra lateral para iniciar a análise automática</div>
    </div>
    """, unsafe_allow_html=True)

    # Histórico recente resumido
    from database import listar_analises
    analises = listar_analises(usuario["id"], limit=3)
    if analises:
        st.markdown('<div class="section-title">📋 Suas análises recentes</div>', unsafe_allow_html=True)
        for a in analises:
            cor  = "#e24b4a" if a["pct_perda"] > 2 else "#1d9e75"
            st.markdown(f"""
            <div class="hist-row">
              <div>
                <b>{a['nome_arquivo']}</b><br>
                <span style="font-size:12px;color:#888">{a['criado_em'][:16]}</span>
              </div>
              <div style="text-align:right">
                <div style="color:{cor};font-weight:700;font-size:16px">R$ {abs(a['perda_total']):,.2f}</div>
                <div style="font-size:11px;color:#888">{a['pct_perda']*100:.2f}% do estoque</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
    st.stop()

# ── Processar ──────────────────────────────────────────────────────────────────
with st.spinner("Analisando inventário..."):
    try:
        resultado = analisar_inventario(arquivo, limite_alerta)
    except Exception as e:
        st.error(f"❌ Erro ao processar: {e}")
        st.markdown("Verifique se o arquivo possui as colunas de Descrição, Quantidade e Valor.")
        st.stop()

df          = resultado["df"]
resumo      = resultado["resumo"]
top_perdas  = resultado["top_perdas"]
top_ganhos  = resultado["top_ganhos"]
por_depto   = resultado["por_depto"]
diagnosticos= resultado["diagnosticos"]
alertas     = resultado["alertas"]

# ── Abas ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊 Painel", "📉 Perdas", "🧠 Diagnóstico", "📤 Exportar"])

# ════════════════════════════════════════════
# ABA 1 — PAINEL
# ════════════════════════════════════════════
with tab1:
    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="kpi-box">
            <div class="kpi-label">Perda Total</div>
            <div class="kpi-value" style="color:#e24b4a">R$ {abs(resumo['perda_total']):,.2f}</div>
            <div class="kpi-delta">{resumo['n_perdas']} itens negativos</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        cor = "#e24b4a" if resumo['pct_perda'] > 2 else "#1d9e75"
        st.markdown(f"""<div class="kpi-box">
            <div class="kpi-label">% Perda / Estoque</div>
            <div class="kpi-value" style="color:{cor}">{resumo['pct_perda']:.2f}%</div>
            <div class="kpi-delta">Meta: abaixo de 2%</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="kpi-box">
            <div class="kpi-label">Ganhos (ajustes +)</div>
            <div class="kpi-value" style="color:#1d9e75">R$ {resumo['ganho_total']:,.2f}</div>
            <div class="kpi-delta">{resumo['n_ganhos']} itens positivos</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="kpi-box">
            <div class="kpi-label">Itens Auditados</div>
            <div class="kpi-value" style="color:#378add">{resumo['total_itens']:,}</div>
            <div class="kpi-delta">{resumo['n_ajustes']} com ajuste</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="section-title">Perdas por Departamento</div>', unsafe_allow_html=True)
        if not por_depto.empty:
            fig, ax = plt.subplots(figsize=(6, max(2.5, len(por_depto) * 0.55)))
            bars = ax.barh(por_depto["departamento"], por_depto["perda"].abs(),
                           color="#e24b4a", height=0.6)
            for bar, val in zip(bars, por_depto["perda"]):
                ax.text(bar.get_width() + por_depto["perda"].abs().max() * 0.02,
                        bar.get_y() + bar.get_height() / 2,
                        f"R$ {abs(val):,.0f}", va="center", fontsize=8, color="#444")
            ax.set_xlim(0, por_depto["perda"].abs().max() * 1.35)
            ax.tick_params(labelsize=9)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    with col_b:
        st.markdown('<div class="section-title">Distribuição por Causa Raiz</div>', unsafe_allow_html=True)
        causas = diagnosticos.get("distribuicao_causas", {})
        if causas:
            fig2, ax2 = plt.subplots(figsize=(5, 4))
            cores = ["#e24b4a","#ba7517","#378add","#7f77dd","#888780","#1d9e75"]
            ax2.pie(list(causas.values()), labels=list(causas.keys()),
                    autopct="%1.0f%%", colors=cores[:len(causas)],
                    textprops={"fontsize": 8}, startangle=90,
                    wedgeprops={"edgecolor":"white","linewidth":1.5})
            fig2.tight_layout()
            st.pyplot(fig2)
            plt.close(fig2)

    if alertas:
        st.markdown('<div class="section-title">⚑ Alertas Automáticos</div>', unsafe_allow_html=True)
        for a in alertas:
            st.markdown(f"""<div class="alert-box">
                <b>⚠ {a['produto']}</b> — {a['departamento']} &nbsp;
                <span style="color:#e24b4a;font-weight:700">R$ {abs(a['valor']):,.2f}</span>
                <span style="font-size:11px;color:#888"> — acima do limite de R$ {limite_alerta:,.0f}</span>
            </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════
# ABA 2 — PERDAS
# ════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-title">🔴 Top 10 — Maiores Perdas Financeiras</div>', unsafe_allow_html=True)
    if not top_perdas.empty:
        dp = top_perdas.copy()
        dp["Valor Perda"] = dp["valor"].apply(lambda x: f"R$ {abs(x):,.2f}")
        st.dataframe(
            dp[["codigo","descricao","departamento","quantidade","Valor Perda","causa_estimada"]].rename(columns={
                "codigo":"Código","descricao":"Produto","departamento":"Depto",
                "quantidade":"Qtd","Valor Perda":"Perda (R$)","causa_estimada":"Causa"}),
            use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">🟢 Top 10 — Maiores Ganhos (possíveis erros anteriores)</div>', unsafe_allow_html=True)
    if not top_ganhos.empty:
        dg = top_ganhos.copy()
        dg["Valor Ganho"] = dg["valor"].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(
            dg[["codigo","descricao","departamento","quantidade","Valor Ganho"]].rename(columns={
                "codigo":"Código","descricao":"Produto","departamento":"Depto",
                "quantidade":"Qtd","Valor Ganho":"Ganho (R$)"}),
            use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">📋 Dados Completos</div>', unsafe_allow_html=True)
    dep_opts = ["Todos"] + sorted(df["departamento"].dropna().unique().tolist())
    tipo_opts = ["Todos","perda","ganho","neutro"]
    c_dep, c_tipo = st.columns(2)
    filtro_dep  = c_dep.selectbox("Departamento", dep_opts)
    filtro_tipo = c_tipo.selectbox("Tipo", tipo_opts)
    df_f = df.copy()
    if filtro_dep  != "Todos": df_f = df_f[df_f["departamento"] == filtro_dep]
    if filtro_tipo != "Todos": df_f = df_f[df_f["tipo"] == filtro_tipo]
    st.dataframe(df_f, use_container_width=True, hide_index=True)

# ════════════════════════════════════════════
# ABA 3 — DIAGNÓSTICO
# ════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-title">🧠 Diagnóstico Automático</div>', unsafe_allow_html=True)

    for d in diagnosticos.get("alertas_criticos", []):
        st.markdown(f"""<div class="alert-box">
            <b>⚠ {d['titulo']}</b><br>
            <span style="font-size:12px;color:#555">{d['descricao']}</span>
        </div>""", unsafe_allow_html=True)

    for d in diagnosticos.get("alertas_moderados", []):
        st.markdown(f"""<div class="warn-box">
            <b>► {d['titulo']}</b><br>
            <span style="font-size:12px;color:#555">{d['descricao']}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">✅ Recomendações Práticas</div>', unsafe_allow_html=True)
    cores_prior = {"ALTA":"🔴","MÉDIA":"🟡","BAIXA":"🟢"}
    for rec in diagnosticos.get("recomendacoes", []):
        st.markdown(f"""<div class="rec-item">
            {cores_prior.get(rec['prioridade'],'⚪')} <b>[{rec['prioridade']}]</b> {rec['texto']}
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">📝 Observações do Analista</div>', unsafe_allow_html=True)
    obs = st.text_area("", height=120, placeholder="Registre aqui observações sobre este inventário...",
                       key="obs_diag")

# ════════════════════════════════════════════
# ABA 4 — EXPORTAR
# ════════════════════════════════════════════
with tab4:
    obs_val = st.session_state.get("obs_diag", "")

    st.markdown('<div class="section-title">💾 Salvar no Histórico</div>', unsafe_allow_html=True)
    col_sv, col_info = st.columns([2, 3])
    with col_sv:
        if st.button("💾 Salvar esta análise no histórico", use_container_width=True, type="primary"):
            aid = salvar_analise(usuario["id"], arquivo.name, resultado, obs_val)
            st.success(f"✅ Análise salva! ID #{aid} — acesse em Histórico.")

    st.markdown('<div class="section-title">📤 Gerar Relatórios</div>', unsafe_allow_html=True)
    col_pdf, col_excel = st.columns(2)

    with col_pdf:
        st.markdown("#### 📄 Relatório PDF")
        st.caption("Capa profissional, gráficos, tabelas e diagnóstico completo.")
        if st.button("🔄 Gerar PDF", use_container_width=True):
            with st.spinner("Gerando PDF..."):
                from pdf_generator import gerar_pdf_relatorio
                pdf = gerar_pdf_relatorio(resultado, obs_val, limite_alerta)
            nome_pdf = arquivo.name.replace(".xlsx","") + "_relatorio.pdf"
            st.download_button("⬇️ Baixar PDF", pdf, nome_pdf, "application/pdf", use_container_width=True)

    with col_excel:
        st.markdown("#### 📊 Relatório Excel")
        st.caption("4 abas formatadas: Resumo, Top Perdas, Deptos, Dados completos.")
        if st.button("🔄 Gerar Excel", use_container_width=True):
            with st.spinner("Gerando Excel..."):
                from excel_generator import gerar_excel_relatorio
                xl = gerar_excel_relatorio(resultado, obs_val)
            nome_xl = arquivo.name.replace(".xlsx","") + "_relatorio.xlsx"
            st.download_button("⬇️ Baixar Excel", xl, nome_xl,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
