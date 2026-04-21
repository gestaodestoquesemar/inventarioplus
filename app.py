"""
app.py — Página de entrada: login/cadastro e redirecionamento ao dashboard.
"""
import streamlit as st
from database import init_db, autenticar, criar_usuario, criar_sessao, validar_sessao

st.set_page_config(
    page_title="InventárioPlus — Login",
    page_icon="📦",
    layout="centered",
)

init_db()

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #f0f4f1; }
[data-testid="stSidebar"] { display: none; }
.login-card {
    background: white; border-radius: 16px; padding: 40px 44px;
    box-shadow: 0 2px 20px rgba(0,0,0,0.07); max-width: 420px; margin: 0 auto;
}
.login-logo { text-align: center; margin-bottom: 28px; }
.login-logo .icon { font-size: 48px; }
.login-logo h1 { font-size: 22px; font-weight: 700; color: #0f2a1e; margin: 8px 0 2px; }
.login-logo p  { font-size: 13px; color: #888; margin: 0; }
.stTextInput > div > div > input {
    border: 1.5px solid #e0e0e0 !important; border-radius: 10px !important;
    padding: 10px 14px !important; font-size: 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #1d9e75 !important; box-shadow: 0 0 0 3px rgba(29,158,117,0.12) !important;
}
div[data-testid="stForm"] button[kind="primaryFormSubmit"],
div[data-testid="stForm"] button[kind="primary"] {
    background: #0f6e56 !important; color: white !important;
    border-radius: 10px !important; width: 100% !important;
    height: 44px !important; font-size: 15px !important; font-weight: 600 !important;
    border: none !important; transition: background 0.2s !important;
}
div[data-testid="stForm"] button:hover { background: #1d9e75 !important; }
.stTabs [data-baseweb="tab"] { font-size: 14px; font-weight: 600; }
.stTabs [data-baseweb="tab-highlight"] { background-color: #1d9e75; }
</style>
""", unsafe_allow_html=True)

# ── Verificar sessão existente ─────────────────────────────────────────────────
token = st.session_state.get("token")
if token:
    usuario = validar_sessao(token)
    if usuario:
        st.switch_page("pages/1_Dashboard.py")

# ── Interface de login ─────────────────────────────────────────────────────────
st.markdown('<div class="login-card">', unsafe_allow_html=True)
st.markdown("""
<div class="login-logo">
  <div class="icon">📦</div>
  <h1>InventárioPlus</h1>
  <p>Plataforma de Análise de Perdas e Inventário</p>
</div>
""", unsafe_allow_html=True)

tab_login, tab_cadastro = st.tabs(["Entrar", "Criar conta"])

with tab_login:
    with st.form("form_login"):
        email = st.text_input("E-mail", placeholder="seu@email.com")
        senha = st.text_input("Senha", type="password", placeholder="••••••••")
        col1, col2 = st.columns([2, 1])
        submitted = col1.form_submit_button("Entrar", use_container_width=True)

    if submitted:
        if not email or not senha:
            st.error("Preencha e-mail e senha.")
        else:
            usuario = autenticar(email, senha)
            if usuario:
                token = criar_sessao(usuario["id"])
                st.session_state["token"] = token
                st.session_state["usuario"] = usuario
                st.success(f"Bem-vindo, {usuario['nome']}!")
                st.switch_page("pages/1_Dashboard.py")
            else:
                st.error("E-mail ou senha incorretos.")

    st.markdown("""
    <div style="margin-top:16px;padding:12px;background:#f0f9f5;border-radius:8px;font-size:12px;color:#555">
      <b>Acesso demo:</b><br>
      E-mail: <code>admin@inventario.com</code><br>
      Senha: <code>admin123</code>
    </div>
    """, unsafe_allow_html=True)

with tab_cadastro:
    with st.form("form_cadastro"):
        nome_novo   = st.text_input("Nome completo", placeholder="João Silva")
        email_novo  = st.text_input("E-mail", placeholder="joao@empresa.com")
        loja_nova   = st.text_input("Loja / Empresa", placeholder="Supermercado Central")
        senha_nova  = st.text_input("Senha (mín. 6 caracteres)", type="password")
        senha_conf  = st.text_input("Confirmar senha", type="password")
        cadastrar   = st.form_submit_button("Criar conta", use_container_width=True)

    if cadastrar:
        erros = []
        if not all([nome_novo, email_novo, senha_nova, senha_conf]):
            erros.append("Preencha todos os campos.")
        if senha_nova != senha_conf:
            erros.append("As senhas não coincidem.")
        if len(senha_nova) < 6:
            erros.append("A senha deve ter pelo menos 6 caracteres.")
        if erros:
            for e in erros:
                st.error(e)
        else:
            res = criar_usuario(nome_novo, email_novo, senha_nova, loja_nova or "Loja Principal")
            if res["ok"]:
                usuario = autenticar(email_novo, senha_nova)
                token = criar_sessao(usuario["id"])
                st.session_state["token"] = token
                st.session_state["usuario"] = usuario
                st.success("Conta criada! Redirecionando...")
                st.switch_page("pages/1_Dashboard.py")
            else:
                st.error(res["erro"])

st.markdown('</div>', unsafe_allow_html=True)
