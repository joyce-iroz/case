# Agente — Mercado de Abertura de Empresas (Supabase + Gemini)

## ⚠️ Segurança
Qualquer chave que você já colou em algum chat deve ser tratada como
comprometida — revogue e gere uma nova antes de usar em produção.
Nunca cole valores reais de `.env` em mensagens de chat, commits do
Git, ou capturas de tela.

## Mapa de credenciais — onde cada uma entra

| Credencial | Vai para a variável (.env) | Usada em qual arquivo |
|---|---|---|
| Project URL do Supabase | `SUPABASE_URL` | `app/supabase_client.py`, `load_data.py` |
| `sb_secret_...` (Supabase) | `SUPABASE_SECRET_KEY` | `app/supabase_client.py`, `load_data.py` |
| `sb_publishable_...` (Supabase) | `SUPABASE_PUBLISHABLE_KEY` | (reservada — só necessária se algum dia você criar uma tela pública que lê o Supabase direto do navegador; o agente em si usa a secret) |
| JWKS URL (Supabase) | `SUPABASE_JWKS_URL` | (reservada — só necessária se adicionar login de usuários e validar tokens JWT; não é usada agora) |
| Chave da Gemini (aistudio.google.com/apikey) | `GEMINI_API_KEY` | `app/gemini_agent.py` |

Só **três variáveis** realmente fazem o agente funcionar:
`SUPABASE_URL`, `SUPABASE_SECRET_KEY` e `GEMINI_API_KEY`.

## Por que Gemini em vez de Groq

O projeto usava Groq (`llama-3.3-70b-versatile` → depois `gpt-oss-120b`),
mas o tier gratuito da Groq tem um limite de tokens por minuto (TPM) baixo
(8K), que estourava com facilidade em conversas com algumas perguntas
seguidas. O Gemini (`gemini-2.5-flash`) tem um tier gratuito bem mais
folgado para esse tipo de uso, com contexto de até 1M tokens.

## Passo a passo

1. Crie a tabela no Supabase: cole o conteúdo de `schema.sql` no
   SQL Editor do painel do Supabase e rode.
2. Copie o arquivo de exemplo e preencha com suas chaves:
   ```bash
   cp .env.example .env
   # edite o .env e cole os valores
   ```
3. Instale as dependências:
   ```bash
   python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Suba os dados do case para o Supabase (uma vez só):
   ```bash
   python load_data.py caminho/para/Dados_Case_2026.xlsx
   ```
5. Teste pelo terminal:
   ```bash
   python chat_cli.py
   ```
6. Ou suba o chat web local:
   ```bash
   streamlit run chat_web.py
   ```

## Deploy grátis (Streamlit Community Cloud)

1. Suba esta pasta para um repositório no GitHub — **confirme que `.env`
   está no `.gitignore`** (já está) e não foi commitado.
2. Em share.streamlit.io → "New app" → aponte para o repositório e o
   arquivo `chat_web.py`.
3. Em "Advanced settings → Secrets", cole as mesmas variáveis do seu
   `.env` (formato TOML: `CHAVE = "valor"`, uma por linha):
   ```toml
   SUPABASE_URL = "https://seu-projeto.supabase.co"
   SUPABASE_SECRET_KEY = "sb_secret_..."
   GEMINI_API_KEY = "sua-chave-gemini"
   GEMINI_MODEL = "gemini-2.5-flash"
   ```
4. Deploy. Depois de qualquer troca nos Secrets: **Save** e depois
   **Reboot app** (nem sempre reinicia sozinho).

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
    ├── charts.py             # gera as imagens dos gráficos (matplotlib)
    ├── report.py              # monta o relatório em PDF (reportlab)
    └── gemini_agent.py      # loop do agente (Gemini + tool calling)
```

## Gráficos e relatórios em PDF

O agente tem duas tools além das de consulta:

- `gerar_grafico` — acionada quando você pede para "ver", "mostrar" ou
  "plotar" algo. Busca os dados agregados e desenha um gráfico de barra
  ou linha, exibido direto no chat (`chat_web.py`) ou salvo em
  `/tmp/graficos_agente` (no terminal, `chat_cli.py` imprime o caminho).
- `gerar_relatorio` — acionada quando você pede um "relatório", "PDF" ou
  para "exportar" os dados. Monta um PDF de uma página (título + gráfico
  + tabela de valores) e oferece um botão de download no chat web; no
  terminal, imprime o caminho do arquivo salvo.

## Troubleshooting rápido

- **`KeyError` numa variável**: ela não está nos Secrets do Streamlit
  (ou não foi salva/rebootada). Confere nome exato (maiúsculas).
- **`Invalid API Key` / `AuthenticationError`**: a chave nos Secrets
  não bate com a chave ativa no console do provedor (Supabase ou
  Google AI Studio) — revoga e gera uma nova, copiando com o botão
  de copiar (não selecionando manualmente).
- **Erros de schema/tool ("expected integer but got null" etc.)**:
  já tratado no código atual — se reaparecer, é sinal de que os
  arquivos em `app/` estão desatualizados em relação a este repo.
