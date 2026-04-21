# 📦 InventárioPlus — Sistema Completo

Plataforma web completa para análise de inventário supermercadista com:
- ✅ Autenticação de usuários (login/cadastro)
- ✅ Upload de Excel e análise automática
- ✅ Diagnóstico inteligente com causa raiz
- ✅ Histórico de análises salvo em banco de dados
- ✅ Comparativo entre inventários
- ✅ Geração de PDF e Excel profissionais
- ✅ Painel administrativo

---

## 🚀 COMO PUBLICAR NA WEB — Passo a Passo Completo

### PASSO 1 — Criar conta no GitHub (gratuito)
1. Acesse **https://github.com** e clique em **"Sign up"**
2. Crie sua conta e confirme o e-mail

### PASSO 2 — Criar repositório
1. Após logar, clique no botão **"+" → "New repository"**
2. Nome: `inventarioplus`
3. Visibilidade: **Public**
4. Clique em **"Create repository"**

### PASSO 3 — Fazer upload de TODOS os arquivos
1. Na página do repositório, clique em **"uploading an existing file"**
2. Selecione ou arraste TODOS estes arquivos de uma vez:

```
app.py
analyzer.py
database.py
auth_guard.py
pdf_generator.py
excel_generator.py
requirements.txt
pages/
  1_Dashboard.py
  2_Historico.py
  3_Comparativo.py
  4_Configuracoes.py
.streamlit/
  config.toml
```

> ⚠️ **Importante:** os arquivos dentro de `pages/` devem estar numa pasta chamada `pages`.
> Os arquivos dentro de `.streamlit/` devem estar numa pasta chamada `.streamlit`.

3. Clique em **"Commit changes"**

### PASSO 4 — Criar conta no Streamlit Cloud (gratuito)
1. Acesse **https://share.streamlit.io**
2. Clique em **"Sign up"** e faça login com o GitHub

### PASSO 5 — Deploy
1. Clique em **"New app"**
2. Selecione o repositório `inventarioplus`
3. Branch: `main`
4. **Main file path:** `app.py`
5. Clique em **"Deploy!"**
6. Aguarde ~3 minutos — o sistema instala tudo automaticamente

### PASSO 6 — Acessar o sistema
1. Você receberá um link tipo: `https://inventarioplus.streamlit.app`
2. **Compartilhe esse link** com sua equipe
3. Faça login com:
   - **E-mail:** `admin@inventario.com`
   - **Senha:** `admin123`
4. Vá em **Configurações → Adicionar usuário** para criar contas para sua equipe

---

## 📁 Estrutura do projeto

```
inventarioplus/
├── app.py                  ← Página de login/cadastro
├── analyzer.py             ← Motor de análise e diagnóstico
├── database.py             ← Banco de dados SQLite (usuários + histórico)
├── auth_guard.py           ← Verificação de sessão (segurança)
├── pdf_generator.py        ← Gerador de relatório PDF
├── excel_generator.py      ← Gerador de relatório Excel
├── requirements.txt        ← Dependências
├── pages/
│   ├── 1_Dashboard.py      ← Upload + análise + exportar
│   ├── 2_Historico.py      ← Histórico de análises salvas
│   ├── 3_Comparativo.py    ← Comparar dois inventários
│   └── 4_Configuracoes.py  ← Conta + painel admin
└── .streamlit/
    └── config.toml         ← Tema e configurações
```

---

## 👥 Perfis de usuário

| Perfil | Pode fazer |
|--------|-----------|
| **analista** | Upload, análise, histórico próprio, exportar |
| **admin** | Tudo + ver histórico de todos + criar/listar usuários |

---

## 📋 Formato do Excel aceito

| Coluna | Nomes aceitos automaticamente |
|--------|-------------------------------|
| Código | Código, Cod, COD_PRODUTO, EAN |
| Descrição | Descrição, Produto, Item, Nome |
| Quantidade | Quantidade, Qtd, QTD_AJUSTE |
| Valor | Valor, Vlr, VLR_AJUSTE, ValorAjuste |
| Data | Data, DT, DT_INVENTARIO, Date |
| Departamento | Departamento, Depto, Seção, Categoria |

---

## 🗄️ Banco de dados

O sistema usa **SQLite** — um arquivo `inventarioplus.db` gerado automaticamente.
No Streamlit Cloud, esse arquivo persiste enquanto o app estiver ativo.

Para maior durabilidade (produção), é recomendado migrar para **PostgreSQL** via
[Supabase](https://supabase.com) ou [Railway](https://railway.app) (ambos gratuitos).

---

## 🧪 Testar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```
