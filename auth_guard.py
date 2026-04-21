"""
auth_guard.py — Helper para verificar sessão em todas as páginas protegidas.
Importe e chame `exigir_login()` no topo de cada página.
"""
import streamlit as st
from database import validar_sessao


def _css_base():
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #f7f8fa; }
    .topbar {
        background: #0f2a1e; color: white; padding: 14px 24px;
        border-radius: 10px; margin-bottom: 20px;
        display: flex; align-items: center; justify-content: space-between;
    }
    .topbar-left { display: flex; align-items: center; gap: 12px; }
    .topbar-logo { font-size: 20px; font-weight: 700; color: white; }
    .topbar-sub  { font-size: 12px; color: rgba(255,255,255,0.55); }
    .topbar-user { font-size: 12px; color: #5dcaa5; font-weight: 600; }
    .kpi-box {
        background: white; border-radius: 12px; padding: 18px 20px;
        border: 1px solid #e8e8e8; text-align: center;
    }
    .kpi-label { font-size: 11px; color: #888; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
    .kpi-value { font-size: 24px; font-weight: 700; margin: 4px 0; }
    .kpi-delta { font-size: 11px; color: #888; }
    .section-title {
        font-size: 14px; font-weight: 700; color: #1a1a1a;
        border-left: 4px solid #1d9e75; padding-left: 10px; margin: 22px 0 12px;
    }
    .alert-box {
        background: #fff5f5; border: 1px solid #f0c0c0; border-radius: 8px;
        padding: 12px 16px; margin-bottom: 10px; font-size: 13px;
    }
    .warn-box {
        background: #fffbf0; border: 1px solid #f0d890; border-radius: 8px;
        padding: 12px 16px; margin-bottom: 10px; font-size: 13px;
    }
    .card {
        background: white; border-radius: 12px; padding: 20px;
        border: 1px solid #e8e8e8; margin-bottom: 14px;
    }
    .rec-item {
        padding: 7px 0; font-size: 13px; color: #444;
        border-bottom: 1px solid #f0f0f0; line-height: 1.5;
    }
    .hist-row {
        background: white; border-radius: 10px; padding: 14px 18px;
        border: 1px solid #e8e8e8; margin-bottom: 8px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .badge {
        display: inline-block; padding: 2px 10px; border-radius: 20px;
        font-size: 11px; font-weight: 600;
    }
    .badge-red   { background: #fcebeb; color: #a32d2d; }
    .badge-green { background: #e1f5ee; color: #0f6e56; }
    .badge-amber { background: #faeeda; color: #854f0b; }
    .badge-blue  { background: #e6f1fb; color: #0c447c; }
    </style>
    """, unsafe_allow_html=True)


def exigir_login() -> dict:
    """
    Verifica se há sessão ativa. Redireciona para login se não houver.
    Retorna dict do usuário logado.
    """
    _css_base()
    token = st.session_state.get("token")
    usuario = None
    if token:
        usuario = validar_sessao(token)
        if usuario:
            st.session_state["usuario"] = dict(usuario)

    if not usuario:
        st.warning("Sessão expirada ou não autenticado. Faça login novamente.")
        st.page_link("app.py", label="← Ir para o login", icon="🔐")
        st.stop()

    return dict(usuario)


def topbar(usuario: dict):
    """Renderiza a barra superior com nome do usuário e botão de logout."""
    col_logo, col_user = st.columns([3, 1])
    with col_logo:
        st.markdown(f"""
        <div class="topbar">
          <div class="topbar-left">
            <span style="font-size:26px">📦</span>
            <div>
              <div class="topbar-logo">InventárioPlus</div>
              <div class="topbar-sub">Prevenção de Perdas e Análise de Inventário</div>
            </div>
          </div>
          <div class="topbar-user">👤 {usuario['nome']} &nbsp;|&nbsp; {usuario['loja']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_user:
        if st.button("Sair", use_container_width=True):
            from database import encerrar_sessao
            encerrar_sessao(st.session_state.get("token", ""))
            st.session_state.clear()
            st.switch_page("app.py")
