# Agente — Mercado de Abertura de Empresas (Supabase + Gemini)



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


