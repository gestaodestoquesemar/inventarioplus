"""
pages/2_Historico.py — Histórico de análises salvas.
"""
import streamlit as st
import json
import pandas as pd
from auth_guard import exigir_login, topbar
from database import listar_analises, get_analise, deletar_analise

st.set_page_config(page_title="Histórico — InventárioPlus", page_icon="📋", layout="wide")
usuario = exigir_login()
topbar(usuario)

with st.sidebar:
    st.page_link("pages/1_Dashboard.py",    label="📊 Dashboard")
    st.page_link("pages/2_Historico.py",    label="📋 Histórico")
    st.page_link("pages/3_Comparativo.py",  label="📈 Comparativo")
    st.page_link("pages/4_Configuracoes.py",label="⚙️ Configurações")

st.markdown("## 📋 Histórico de Análises")

is_admin = usuario.get("role") == "admin"
analises = listar_analises(None if is_admin else usuario["id"], limit=100)

if not analises:
    st.info("Nenhuma análise salva ainda. Vá ao Dashboard, faça um upload e clique em 'Salvar análise'.")
    st.stop()

# ── Filtros ────────────────────────────────────────────────────────────────────
col_f1, col_f2 = st.columns(2)
busca = col_f1.text_input("🔍 Buscar por arquivo ou loja", placeholder="nome do arquivo...")
ordem = col_f2.selectbox("Ordenar por", ["Mais recente", "Maior perda", "Maior %"])

analises_f = [a for a in analises if not busca or busca.lower() in a["nome_arquivo"].lower()]
if ordem == "Maior perda":
    analises_f.sort(key=lambda x: abs(x["perda_total"]), reverse=True)
elif ordem == "Maior %":
    analises_f.sort(key=lambda x: x["pct_perda"], reverse=True)

st.markdown(f"**{len(analises_f)} análise(s) encontrada(s)**")
st.markdown("---")

for a in analises_f:
    cor_pct = "#e24b4a" if a["pct_perda"] > 0.02 else "#1d9e75"

    with st.expander(f"📄 {a['nome_arquivo']}  —  {a['criado_em'][:16]}  |  R$ {abs(a['perda_total']):,.2f}"):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Perda Total",    f"R$ {abs(a['perda_total']):,.2f}")
        col2.metric("% Estoque",      f"{a['pct_perda']*100:.2f}%" if a['pct_perda'] < 1 else f"{a['pct_perda']:.2f}%")
        col3.metric("Ganhos",         f"R$ {a['ganho_total']:,.2f}")
        col4.metric("Itens",          str(a["total_itens"]))

        if is_admin:
            st.caption(f"👤 Analista: {a.get('usuario_nome','?')} | Loja: {a.get('loja','?')}")

        # Top perdas
        try:
            tp = json.loads(a["top_perdas_json"])
            if tp:
                st.markdown("**Top perdas:**")
                df_tp = pd.DataFrame(tp)[["descricao","departamento","valor"]].head(5)
                df_tp["valor"] = df_tp["valor"].apply(lambda x: f"R$ {abs(x):,.2f}")
                df_tp.columns = ["Produto","Depto","Perda"]
                st.dataframe(df_tp, use_container_width=True, hide_index=True)
        except Exception:
            pass

        # Diagnóstico resumido
        try:
            diag = json.loads(a["diagnostico_txt"])
            alertas_c = diag.get("alertas_criticos",[])
            if alertas_c:
                st.markdown("**Diagnóstico:**")
                for d in alertas_c[:2]:
                    st.markdown(f'<div class="alert-box"><b>⚠ {d["titulo"]}</b></div>',
                                unsafe_allow_html=True)
        except Exception:
            pass

        # Observações
        if a.get("observacoes"):
            st.markdown(f"**Observações:** {a['observacoes']}")

        # Exportar a partir do histórico
        colx, cold = st.columns([4,1])
        with colx:
            if st.button(f"📤 Reexportar PDF desta análise", key=f"pdf_{a['id']}"):
                try:
                    resumo = json.loads(a["resumo_json"])
                    top_p  = pd.DataFrame(json.loads(a["top_perdas_json"]))
                    top_g  = pd.DataFrame()
                    por_d  = pd.DataFrame(json.loads(a["por_depto_json"]))
                    diag   = json.loads(a["diagnostico_txt"])
                    resultado_fake = {
                        "resumo": resumo, "top_perdas": top_p, "top_ganhos": top_g,
                        "por_depto": por_d, "diagnosticos": diag, "alertas": []
                    }
                    from pdf_generator import gerar_pdf_relatorio
                    pdf = gerar_pdf_relatorio(resultado_fake, a.get("observacoes",""), 0)
                    st.download_button("⬇️ Baixar PDF", pdf,
                        a["nome_arquivo"].replace(".xlsx","")+"_historico.pdf",
                        "application/pdf", key=f"dl_pdf_{a['id']}")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")

        with cold:
            if st.button("🗑 Deletar", key=f"del_{a['id']}", type="secondary"):
                if deletar_analise(a["id"], usuario["id"]):
                    st.success("Análise removida.")
                    st.rerun()
                else:
                    st.error("Não foi possível deletar.")
