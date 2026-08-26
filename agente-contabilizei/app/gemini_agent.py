import os
import json

from google import genai
from google.genai import types

from app.supabase_client import consultar_aberturas, totais_aberturas
from app.charts import criar_grafico
from app.report import criar_relatorio_pdf


client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

SYSTEM_PROMPT = """Você é um analista de dados especializado no mercado
brasileiro de abertura de empresas. Você tem acesso a uma tabela chamada
base_dados no Supabase, com uma linha por combinação de
(ano, mes, cidade_agrupada, class_segmentos), contendo a coluna
abertura_empresas (volume de aberturas naquele corte).

Período disponível: 2018 a 2025, mensal.
Cidades: SAO PAULO, RIO DE JANEIRO, BELO HORIZONTE, PORTO ALEGRE,
CURITIBA, FLORIANOPOLIS, grande_sp, outros.
Segmentos: 30 categorias de CNAE agrupado (ex.: Psicologia, TI/DEV,
Odontologia, Advocacia, Medicina, etc.).

Você tem QUATRO tools disponíveis:

1. `totais_aberturas` — retorna totais JÁ SOMADOS pelo banco, agrupados
   por ano, mês, cidade ou segmento. USE ESTA para qualquer pergunta de
   visão geral: totais, comparações, tendência, projeção, crescimento.
   Uma chamada só já traz, por exemplo, o total de cada um dos 8 anos.

2. `consultar_aberturas` — retorna linhas cruas (não agregadas), com
   filtros. Use APENAS quando a pergunta pedir detalhe granular real
   (ex.: "me mostra alguns registros de Psicologia em SP em 2024").

3. `gerar_grafico` — quando o usuário pedir para "ver", "mostrar",
   "plotar" ou "visualizar" algo (ex.: "mostra num gráfico a evolução
   por ano", "plota um comparativo entre as cidades"), use esta tool.
   Ela busca os dados agregados e já desenha o gráfico — você não
   precisa (e não deve) chamar `totais_aberturas` antes dela para a
   mesma informação; ela já faz a consulta internamente. Depois de
   chamá-la, apenas comente o que o gráfico mostra em 1-2 frases —
   não descreva número por número.

4. `gerar_relatorio` — quando o usuário pedir um "relatório", "PDF",
   "documento" ou "exportar" os dados, use esta tool. Ela busca os
   dados agregados, monta um gráfico e gera um PDF de uma página com
   título, gráfico e tabela de valores — pronto para o usuário baixar.
   Assim como `gerar_grafico`, ela já consulta os dados sozinha; não
   chame `totais_aberturas` antes dela para a mesma informação.

Para projeções e tendências sem pedido explícito de gráfico ou relatório:
chame `totais_aberturas` agrupando por 'ano' (ou 'mes', se for
sazonalidade) e faça você mesmo a extrapolação simples sobre esses
totais já agregados — nunca tente somar linha por linha com
`consultar_aberturas` para perguntas desse tipo, é lento e não cabe no
limite de chamadas.
"""

_TOOL_DECLARATION = types.FunctionDeclaration(
    name="consultar_aberturas",
    description=(
        "Consulta a tabela base_dados no Supabase, com filtros opcionais "
        "por ano, mês, cidade e segmento. Retorna as linhas granulares "
        "(não agregadas)."
    ),
    parameters={
        "type": "object",
        "properties": {
            "ano": {"type": "integer", "description": "Ex.: 2025"},
            "mes": {"type": "integer", "description": "1 a 12"},
            "cidade": {
                "type": "string",
                "description": "Busca parcial, ex.: 'SAO PAULO'",
            },
            "segmento": {
                "type": "string",
                "description": "Busca parcial, ex.: 'Psicologia'",
            },
        },
    },
)
_TOOL_TOTAIS = types.FunctionDeclaration(
    name="totais_aberturas",
    description=(
        "Retorna totais JÁ SOMADOS (agregados no banco), agrupados por "
        "'ano', 'mes', 'cidade' ou 'segmento', com filtros opcionais. "
        "Prefira esta tool para qualquer pergunta de totais, comparação, "
        "tendência, crescimento ou projeção."
    ),
    parameters={
        "type": "object",
        "properties": {
            "ano": {"type": "integer", "description": "Filtra por um ano específico, ex.: 2025"},
            "mes": {"type": "integer", "description": "Filtra por um mês específico, 1 a 12"},
            "cidade": {"type": "string", "description": "Busca parcial, ex.: 'SAO PAULO'"},
            "segmento": {"type": "string", "description": "Busca parcial, ex.: 'Psicologia'"},
            "agrupar_por": {
                "type": "string",
                "enum": ["ano", "mes", "cidade", "segmento"],
                "description": "Como agrupar a soma. Use 'ano' para tendência/projeção.",
            },
        },
    },
)
_TOOL_GRAFICO = types.FunctionDeclaration(
    name="gerar_grafico",
    description=(
        "Busca totais agregados e gera um gráfico (barra ou linha) para "
        "visualização. Use quando o usuário pedir explicitamente para "
        "ver/mostrar/plotar/visualizar algo."
    ),
    parameters={
        "type": "object",
        "properties": {
            "agrupar_por": {
                "type": "string",
                "enum": ["ano", "mes", "cidade", "segmento"],
                "description": "Dimensão do eixo X do gráfico.",
            },
            "tipo_grafico": {
                "type": "string",
                "enum": ["barra", "linha"],
                "description": "'linha' para evolução ao longo do tempo (ano/mês); 'barra' para comparação entre categorias (cidade/segmento).",
            },
            "titulo": {"type": "string", "description": "Título curto e descritivo do gráfico."},
            "ano": {"type": "integer", "description": "Filtro opcional de ano"},
            "mes": {"type": "integer", "description": "Filtro opcional de mês"},
            "cidade": {"type": "string", "description": "Filtro opcional de cidade (busca parcial)"},
            "segmento": {"type": "string", "description": "Filtro opcional de segmento (busca parcial)"},
        },
        "required": ["agrupar_por", "tipo_grafico", "titulo"],
    },
)
_TOOL_RELATORIO = types.FunctionDeclaration(
    name="gerar_relatorio",
    description=(
        "Busca totais agregados, monta um gráfico e gera um relatório em "
        "PDF (título + gráfico + tabela de valores) pronto para download. "
        "Use quando o usuário pedir um relatório, PDF, documento ou para "
        "exportar os dados."
    ),
    parameters={
        "type": "object",
        "properties": {
            "agrupar_por": {
                "type": "string",
                "enum": ["ano", "mes", "cidade", "segmento"],
                "description": "Dimensão principal do relatório.",
            },
            "tipo_grafico": {
                "type": "string",
                "enum": ["barra", "linha"],
                "description": "'linha' para evolução ao longo do tempo (ano/mês); 'barra' para comparação entre categorias (cidade/segmento).",
            },
            "titulo": {"type": "string", "description": "Título curto e descritivo do relatório."},
            "ano": {"type": "integer", "description": "Filtro opcional de ano"},
            "mes": {"type": "integer", "description": "Filtro opcional de mês"},
            "cidade": {"type": "string", "description": "Filtro opcional de cidade (busca parcial)"},
            "segmento": {"type": "string", "description": "Filtro opcional de segmento (busca parcial)"},
        },
        "required": ["agrupar_por", "tipo_grafico", "titulo"],
    },
)
_TOOLS = [types.Tool(function_declarations=[_TOOL_DECLARATION, _TOOL_TOTAIS, _TOOL_GRAFICO, _TOOL_RELATORIO])]

_CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    tools=_TOOLS,
    # desliga a execução automática: queremos controlar o loop nós
    # mesmos (mesmo padrão usado na versão Groq deste projeto)
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)


def _executar_tool(nome: str, argumentos: dict, graficos_gerados: list, relatorios_gerados: list):
    if nome == "consultar_aberturas":
        return consultar_aberturas(**argumentos)
    if nome == "totais_aberturas":
        return totais_aberturas(**argumentos)
    if nome == "gerar_grafico":
        args = dict(argumentos)
        agrupar_por = args.pop("agrupar_por")
        tipo_grafico = args.pop("tipo_grafico")
        titulo = args.pop("titulo")
        dados = totais_aberturas(agrupar_por=agrupar_por, **args)
        caminho = criar_grafico(dados, tipo=tipo_grafico, titulo=titulo)
        graficos_gerados.append(caminho)
        # devolve só um resumo pro modelo (não os dados completos de novo)
        return {"grafico_gerado": True, "pontos_plotados": len(dados)}
    if nome == "gerar_relatorio":
        args = dict(argumentos)
        agrupar_por = args.pop("agrupar_por")
        tipo_grafico = args.pop("tipo_grafico")
        titulo = args.pop("titulo")
        dados = totais_aberturas(agrupar_por=agrupar_por, **args)
        caminho_grafico = criar_grafico(dados, tipo=tipo_grafico, titulo=titulo)
        filtros_texto = ", ".join(f"{k}={v}" for k, v in args.items() if v is not None) or "nenhum"
        caminho_pdf = criar_relatorio_pdf(dados, titulo=titulo, caminho_grafico=caminho_grafico,
                                           filtros_texto=filtros_texto)
        relatorios_gerados.append(caminho_pdf)
        return {"relatorio_gerado": True, "linhas_incluidas": len(dados)}
    raise ValueError(f"Tool desconhecida: {nome}")


def perguntar(pergunta: str, historico: list | None = None) -> tuple[str, list, list, list]:
    """
    Manda uma pergunta pro agente. `historico` é uma lista de
    `types.Content` (não dicts) com o texto final de perguntas/respostas
    anteriores — os dados brutos de tools passadas NÃO ficam salvos aqui,
    só são usados dentro do turno atual (evita estourar limite de tokens
    em conversas longas).
    Retorna (resposta_texto, novo_historico, caminhos_dos_graficos, caminhos_dos_relatorios_pdf).
    """
    historico = historico or []
    graficos_gerados: list[str] = []
    relatorios_gerados: list[str] = []
    # mantém só as últimas 3 trocas de pergunta/resposta como contexto
    contents = list(historico[-6:])
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=pergunta)]))

    for _ in range(8):
        resp = client.models.generate_content(model=MODEL, contents=contents, config=_CONFIG)
        candidate = resp.candidates[0]
        function_calls = [p.function_call for p in candidate.content.parts if p.function_call]

        if not function_calls:
            texto = resp.text or ""
            novo_historico = historico + [
                types.Content(role="user", parts=[types.Part.from_text(text=pergunta)]),
                types.Content(role="model", parts=[types.Part.from_text(text=texto)]),
            ]
            return texto, novo_historico, graficos_gerados, relatorios_gerados

        contents.append(candidate.content)
        response_parts = []
        for fc in function_calls:
            resultado = _executar_tool(fc.name, dict(fc.args or {}), graficos_gerados, relatorios_gerados)
            response_parts.append(
                types.Part.from_function_response(
                    name=fc.name,
                    response={"result": json.loads(json.dumps(resultado, default=str))},
                )
            )
        contents.append(types.Content(role="user", parts=response_parts))

    texto = "Não consegui concluir — muitas chamadas de ferramenta."
    novo_historico = historico + [
        types.Content(role="user", parts=[types.Part.from_text(text=pergunta)]),
        types.Content(role="model", parts=[types.Part.from_text(text=texto)]),
    ]
    return texto, novo_historico, graficos_gerados, relatorios_gerados
