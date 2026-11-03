# Agente de análise do mercado de abertura de empresas

Agente conversacional que responde perguntas em português sobre dados de abertura de empresas no Brasil, consultando o banco por **tool calling** e devolvendo texto, gráfico ou relatório em PDF conforme o que foi pedido.

Feito como case técnico. O projeto está em [`agente-contabilizei/`](agente-contabilizei/).

```
você: quais segmentos mais cresceram em São Paulo desde 2022?
→ o agente escolhe a tool de agregação, consulta o Supabase e responde

você: mostra isso num gráfico
→ o agente chama gerar_grafico e devolve a imagem

você: exporta como PDF
→ o agente chama gerar_relatorio e devolve o documento
```

## Como funciona

O modelo não recebe os dados no prompt. Ele recebe **quatro tools** e decide qual chamar:

| Tool | Quando o modelo usa |
|---|---|
| `totais_aberturas` | Visão geral: totais, comparação, tendência, projeção. A soma acontece no banco |
| `consultar_aberturas` | Só quando a pergunta pede linha crua, com filtros |
| `gerar_grafico` | Quando pedem para ver, mostrar ou plotar |
| `gerar_relatorio` | Quando pedem relatório, PDF ou exportação |

**A agregação roda no PostgreSQL, não no Python.** A função `totais_aberturas` recebe filtros de ano, mês, cidade e segmento e um critério de agrupamento, e devolve os totais já somados. Uma chamada traz o total de cada um dos oito anos, em vez de trazer milhares de linhas para somar depois. O prompt instrui o modelo explicitamente a não usar a tool granular para pergunta de visão geral, porque isso é lento e estoura o limite de chamadas.

As tools de gráfico e relatório consultam os dados sozinhas. O prompt diz isso ao modelo, para ele não gastar uma chamada de consulta antes de cada uma.

## Dados

Tabela `base_dados`, uma linha por combinação de ano, mês, cidade e segmento, com o volume de aberturas.

- Período: 2018 a 2025, mensal
- Cidades: São Paulo, Rio de Janeiro, Belo Horizonte, Porto Alegre, Curitiba, Florianópolis, Grande SP e outros
- 30 categorias de CNAE agrupado: TI, advocacia, medicina, odontologia, psicologia e outras

Índices em `(ano, mes)`, `cidade_agrupada` e `class_segmentos`. Schema e função em [`schema.sql`](agente-contabilizei/schema.sql).

## Estrutura

```
agente-contabilizei/
├── app/
│   ├── gemini_agent.py     # loop do agente e declaração das tools
│   ├── groq_agent.py       # mesma ideia, com Groq
│   ├── supabase_client.py  # as duas tools de consulta
│   ├── charts.py           # gráficos em matplotlib
│   └── report.py           # PDF em reportlab
├── chat_cli.py             # teste pelo terminal
├── chat_web.py             # chat web em Streamlit
├── load_data.py            # carga do Excel para o Supabase
└── schema.sql              # tabela, índices e função de agregação
```

## Stack

Python · Google Gemini e Groq (tool calling) · Supabase (PostgreSQL) · Streamlit · matplotlib · reportlab

## Rodando

```bash
cd agente-contabilizei
pip install -r requirements.txt
cp .env.example .env        # preencha as chaves
python load_data.py         # carga inicial
streamlit run chat_web.py   # ou: python chat_cli.py
```

---

Joyce Gomes de Queiroz — [LinkedIn](https://linkedin.com/in/--joycequeiroz)
