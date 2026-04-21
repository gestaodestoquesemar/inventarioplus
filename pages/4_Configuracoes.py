"""
pages/4_Configuracoes.py — Configurações de conta e painel admin.
"""
import streamlit as st
from auth_guard import exigir_login, topbar
from database import alterar_senha, listar_usuarios, criar_usuario, stats_gerais

st.set_page_config(page_title="Configurações — InventárioPlus", page_icon="⚙️", layout="wide")
usuario = exigir_login()
topbar(usuario)

with st.sidebar:
    st.page_link("pages/1_Dashboard.py",    label="📊 Dashboard")
    st.page_link("pages/2_Historico.py",    label="📋 Histórico")
    st.page_link("pages/3_Comparativo.py",  label="📈 Comparativo")
    st.page_link("pages/4_Configuracoes.py",label="⚙️ Configurações")

st.markdown("## ⚙️ Configurações")

# ── Dados da conta ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">👤 Minha Conta</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
col1.markdown(f"""
<div class="card">
  <b>Nome:</b> {usuario['nome']}<br>
  <b>E-mail:</b> {usuario['email']}<br>
  <b>Loja:</b> {usuario['loja']}<br>
  <b>Perfil:</b> {usuario['role']}<br>
  <b>Conta criada em:</b> {str(usuario['criado_em'])[:10]}
</div>
""", unsafe_allow_html=True)

with col2:
    with st.expander("🔑 Alterar senha"):
        with st.form("form_senha"):
            nova   = st.text_input("Nova senha", type="password")
            conf   = st.text_input("Confirmar nova senha", type="password")
            salvar = st.form_submit_button("Salvar nova senha")
        if salvar:
            if not nova or not conf:
                st.error("Preencha os dois campos.")
            elif nova != conf:
                st.error("As senhas não coincidem.")
            elif len(nova) < 6:
                st.error("Mínimo 6 caracteres.")
            else:
                if alterar_senha(usuario["id"], nova):
                    st.success("Senha alterada com sucesso!")
                else:
                    st.error("Erro ao alterar senha.")

# ── Painel Admin ───────────────────────────────────────────────────────────────
if usuario.get("role") == "admin":
    st.markdown('<div class="section-title">🛡 Painel Administrativo</div>', unsafe_allow_html=True)

    stats = stats_gerais()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Análises",    stats.get("total_analises", 0))
    c2.metric("Perda Acumulada (R$)", f"{stats.get('perda_acumulada',0):,.2f}")
    c3.metric("% Médio de Perda",     f"{(stats.get('media_pct_perda',0) or 0)*100:.2f}%" if (stats.get('media_pct_perda',0) or 0) < 1 else f"{stats.get('media_pct_perda',0):.2f}%")
    c4.metric("Usuários Ativos",      stats.get("usuarios_ativos", 0))

    st.markdown("**Usuários cadastrados:**")
    usuarios = listar_usuarios()
    import pandas as pd
    df_u = pd.DataFrame(usuarios)[["id","nome","email","loja","role","criado_em"]]
    df_u.columns = ["ID","Nome","E-mail","Loja","Perfil","Criado em"]
    st.dataframe(df_u, use_container_width=True, hide_index=True)

    with st.expander("➕ Adicionar novo usuário"):
        with st.form("form_novo_user"):
            n_nome  = st.text_input("Nome")
            n_email = st.text_input("E-mail")
            n_loja  = st.text_input("Loja")
            n_senha = st.text_input("Senha", type="password")
            n_role  = st.selectbox("Perfil", ["analista","admin"])
            n_salvar= st.form_submit_button("Criar usuário")
        if n_salvar:
            if not all([n_nome, n_email, n_senha]):
                st.error("Preencha nome, e-mail e senha.")
            else:
                res = criar_usuario(n_nome, n_email, n_senha, n_loja or "Loja Principal")
                if res["ok"]:
                    st.success(f"Usuário criado! ID #{res['id']}")
                    st.rerun()
                else:
                    st.error(res["erro"])
