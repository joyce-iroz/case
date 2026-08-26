# Agente — Mercado de Abertura de Empresas (Supabase + Groq)

## ⚠️ Antes de tudo
As chaves que você colou no chat (Supabase secret key, Groq key) devem ser
**rotacionadas** antes de usar este projeto:
- Supabase: Project Settings → API → regenerar `service_role`. Se a
  "chave do projeto" que você colou for a senha do Postgres, trocar
  também em Settings → Database → Reset Database Password.
- Groq: console.groq.com → API Keys → revogar a chave antiga → criar nova.

Só depois disso, use as chaves **novas** neste projeto.

## Mapa de credenciais — onde cada uma entra

| Credencial que você tem | Vai para a variável (.env) | Usada em qual arquivo |
|---|---|---|
| Project URL do Supabase | `SUPABASE_URL` | `app/supabase_client.py`, `load_data.py` |
| `sb_publishable_...` | `SUPABASE_PUBLISHABLE_KEY` | (reservada — só é necessária se algum dia você criar uma tela pública que lê o Supabase direto do navegador; o agente em si usa a secret) |
| `sb_secret_...` | `SUPABASE_SECRET_KEY` | `app/supabase_client.py`, `load_data.py` |
| JWKS URL | `SUPABASE_JWKS_URL` | (reservada — só necessária se você adicionar login de usuários e precisar validar tokens JWT; não é usada agora) |
| chave/senha do Postgres que você colou | não entra no `.env` deste projeto — só seria usada se você conectasse direto via `psycopg2`/connection string, o que não fazemos aqui (usamos a API REST do Supabase) | — |
| `gsk_...` | `GROQ_API_KEY` | `app/groq_agent.py` |

Ou seja: **só duas variáveis realmente fazem o agente funcionar** —
`SUPABASE_URL`, `SUPABASE_SECRET_KEY` e `GROQ_API_KEY`. As outras (`PUBLISHABLE_KEY`,
`JWKS_URL`) estão no `.env.example` só porque você já tinha elas em mãos —
guarde-as, mas não são necessárias para este agente específico.

## Passo a passo

1. **Rotacione as chaves** (seção acima).
2. Crie a tabela no Supabase: cole o conteúdo de `schema.sql` no
   SQL Editor do painel do Supabase e rode.
3. Copie o arquivo de exemplo e preencha com as chaves novas:
   ```bash
   cp .env.example .env
   # edite o .env e cole os valores novos
   ```
4. Instale as dependências:
   ```bash
   python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
5. Suba os dados do case para o Supabase (uma vez só):
   ```bash
   python load_data.py caminho/para/Dados_Case_2026.xlsx
   ```
6. Teste pelo terminal:
   ```bash
   python chat_cli.py
   ```
7. Ou suba o chat web local:
   ```bash
   streamlit run chat_web.py
   ```

## Deploy grátis (Streamlit Community Cloud)

1. Suba esta pasta para um repositório no GitHub — **confirme que `.env`
   está no `.gitignore`** (já está) e não foi commitado.
2. Em share.streamlit.io → "New app" → aponte para o repositório e o
   arquivo `chat_web.py`.
3. Em "Advanced settings → Secrets", cole as mesmas variáveis do seu
   `.env` (formato `CHAVE = "valor"`).
4. Deploy. Pronto — chat público (ou com senha, se configurar) rodando
   de graça.

## Estrutura

```
.
├── .env.example        # nomes das variáveis (sem valores)
├── .gitignore           # garante que .env nunca vai pro Git
├── requirements.txt
├── schema.sql            # cria a tabela base_dados no Supabase
├── load_data.py          # sobe o Excel do case para o Supabase
├── chat_cli.py           # teste rápido via terminal
├── chat_web.py           # chat web (Streamlit)
└── app/
    ├── supabase_client.py  # consulta a tabela (tool do agente)
    └── groq_agent.py        # loop do agente (Groq + tool calling)
```
