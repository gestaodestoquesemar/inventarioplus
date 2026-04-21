"""
database.py — Gerencia SQLite: usuários, sessões e histórico de análises.
"""
import sqlite3
import hashlib
import secrets
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path("inventarioplus.db")


def _conn():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    """Cria tabelas se não existirem. Chamado na inicialização do app."""
    con = _conn()
    cur = con.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        nome       TEXT    NOT NULL,
        email      TEXT    NOT NULL UNIQUE,
        senha_hash TEXT    NOT NULL,
        loja       TEXT    DEFAULT 'Loja Principal',
        role       TEXT    DEFAULT 'analista',
        criado_em  TEXT    DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS analises (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id      INTEGER NOT NULL,
        nome_arquivo    TEXT    NOT NULL,
        loja            TEXT,
        periodo         TEXT,
        perda_total     REAL,
        ganho_total     REAL,
        pct_perda       REAL,
        total_itens     INTEGER,
        n_ajustes       INTEGER,
        resumo_json     TEXT,
        top_perdas_json TEXT,
        por_depto_json  TEXT,
        diagnostico_txt TEXT,
        observacoes     TEXT,
        criado_em       TEXT    DEFAULT (datetime('now')),
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    );

    CREATE TABLE IF NOT EXISTS sessoes (
        token      TEXT PRIMARY KEY,
        usuario_id INTEGER NOT NULL,
        expira_em  TEXT    NOT NULL,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    );
    """)

    # Criar usuário admin padrão se nenhum existir
    cur.execute("SELECT COUNT(*) as n FROM usuarios")
    if cur.fetchone()["n"] == 0:
        _criar_usuario_interno(cur, "Administrador", "admin@inventario.com", "admin123", "Matriz", "admin")

    con.commit()
    con.close()


# ── Usuários ───────────────────────────────────────────────────────────────────
def _hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def _criar_usuario_interno(cur, nome, email, senha, loja, role):
    cur.execute(
        "INSERT OR IGNORE INTO usuarios (nome, email, senha_hash, loja, role) VALUES (?,?,?,?,?)",
        (nome, email, _hash_senha(senha), loja, role)
    )


def criar_usuario(nome: str, email: str, senha: str, loja: str = "Loja Principal") -> dict:
    con = _conn()
    cur = con.cursor()
    try:
        cur.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, loja) VALUES (?,?,?,?)",
            (nome, email.lower().strip(), _hash_senha(senha), loja)
        )
        con.commit()
        return {"ok": True, "id": cur.lastrowid}
    except sqlite3.IntegrityError:
        return {"ok": False, "erro": "E-mail já cadastrado."}
    finally:
        con.close()


def autenticar(email: str, senha: str) -> dict | None:
    """Retorna dict do usuário se credenciais corretas, None caso contrário."""
    con = _conn()
    cur = con.cursor()
    cur.execute(
        "SELECT * FROM usuarios WHERE email=? AND senha_hash=?",
        (email.lower().strip(), _hash_senha(senha))
    )
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None


def get_usuario(user_id: int) -> dict | None:
    con = _conn()
    cur = con.cursor()
    cur.execute("SELECT * FROM usuarios WHERE id=?", (user_id,))
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None


def listar_usuarios() -> list:
    con = _conn()
    cur = con.cursor()
    cur.execute("SELECT id, nome, email, loja, role, criado_em FROM usuarios ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def alterar_senha(user_id: int, nova_senha: str) -> bool:
    con = _conn()
    cur = con.cursor()
    cur.execute("UPDATE usuarios SET senha_hash=? WHERE id=?", (_hash_senha(nova_senha), user_id))
    con.commit()
    ok = cur.rowcount > 0
    con.close()
    return ok


# ── Sessões ────────────────────────────────────────────────────────────────────
def criar_sessao(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expira = datetime.now().replace(hour=23, minute=59, second=59).isoformat()
    con = _conn()
    con.execute("INSERT OR REPLACE INTO sessoes VALUES (?,?,?)", (token, user_id, expira))
    con.commit()
    con.close()
    return token


def validar_sessao(token: str) -> dict | None:
    if not token:
        return None
    con = _conn()
    cur = con.cursor()
    cur.execute("""
        SELECT u.* FROM sessoes s
        JOIN usuarios u ON u.id = s.usuario_id
        WHERE s.token=? AND s.expira_em > datetime('now')
    """, (token,))
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None


def encerrar_sessao(token: str):
    con = _conn()
    con.execute("DELETE FROM sessoes WHERE token=?", (token,))
    con.commit()
    con.close()


# ── Histórico de Análises ──────────────────────────────────────────────────────
def salvar_analise(usuario_id: int, nome_arquivo: str, resultado: dict, observacoes: str = "") -> int:
    resumo      = resultado["resumo"]
    top_perdas  = resultado["top_perdas"]
    por_depto   = resultado["por_depto"]
    diagnosticos= resultado["diagnosticos"]

    con = _conn()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO analises
        (usuario_id, nome_arquivo, loja, periodo, perda_total, ganho_total,
         pct_perda, total_itens, n_ajustes, resumo_json, top_perdas_json,
         por_depto_json, diagnostico_txt, observacoes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        usuario_id,
        nome_arquivo,
        resumo.get("loja", ""),
        str(resumo.get("data_ref", "")),
        round(resumo["perda_total"], 2),
        round(resumo["ganho_total"], 2),
        round(resumo["pct_perda"], 4),
        resumo["total_itens"],
        resumo["n_ajustes"],
        json.dumps(resumo, default=str),
        json.dumps(top_perdas.to_dict("records"), default=str),
        json.dumps(por_depto.to_dict("records"), default=str),
        json.dumps(diagnosticos, default=str),
        observacoes,
    ))
    analise_id = cur.lastrowid
    con.commit()
    con.close()
    return analise_id


def listar_analises(usuario_id: int | None = None, limit: int = 50) -> list:
    con = _conn()
    cur = con.cursor()
    if usuario_id:
        cur.execute("""
            SELECT a.*, u.nome as usuario_nome FROM analises a
            JOIN usuarios u ON u.id = a.usuario_id
            WHERE a.usuario_id=?
            ORDER BY a.criado_em DESC LIMIT ?
        """, (usuario_id, limit))
    else:
        cur.execute("""
            SELECT a.*, u.nome as usuario_nome FROM analises a
            JOIN usuarios u ON u.id = a.usuario_id
            ORDER BY a.criado_em DESC LIMIT ?
        """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def get_analise(analise_id: int) -> dict | None:
    con = _conn()
    cur = con.cursor()
    cur.execute("SELECT * FROM analises WHERE id=?", (analise_id,))
    row = cur.fetchone()
    con.close()
    return dict(row) if row else None


def deletar_analise(analise_id: int, usuario_id: int) -> bool:
    con = _conn()
    cur = con.cursor()
    cur.execute("DELETE FROM analises WHERE id=? AND usuario_id=?", (analise_id, usuario_id))
    con.commit()
    ok = cur.rowcount > 0
    con.close()
    return ok


def stats_gerais() -> dict:
    con = _conn()
    cur = con.cursor()
    cur.execute("""
        SELECT
          COUNT(*) as total_analises,
          SUM(ABS(perda_total)) as perda_acumulada,
          AVG(pct_perda) as media_pct_perda,
          COUNT(DISTINCT usuario_id) as usuarios_ativos
        FROM analises
    """)
    row = cur.fetchone()
    con.close()
    return dict(row) if row else {}
