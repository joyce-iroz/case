import os
import json

from google import genai
from google.genai import types

from app.supabase_client import consultar_aberturas

# --- onde a GEMINI_API_KEY é usada -------------------------------
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
# -------------------------------------------------------------------

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

Sempre que precisar de números, use a tool `consultar_aberturas` —
nunca invente valores. A tool retorna no máximo algumas dezenas de
linhas por chamada, então:
- Prefira várias chamadas específicas (ex.: uma por ano, ou uma por
  cidade) a uma chamada ampla sem filtro nenhum.
- Se a pergunta pedir uma agregação (soma, média, crescimento) que
  exija muitos meses/cidades/segmentos, faça isso em várias chamadas
  pequenas e some os resultados você mesmo, explicando o raciocínio
  de forma breve.
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
_TOOLS = [types.Tool(function_declarations=[_TOOL_DECLARATION])]

_CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    tools=_TOOLS,
    # desliga a execução automática: queremos controlar o loop nós
    # mesmos (mesmo padrão usado na versão Groq deste projeto)
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)


def _executar_tool(nome: str, argumentos: dict):
    if nome == "consultar_aberturas":
        return consultar_aberturas(**argumentos)
    raise ValueError(f"Tool desconhecida: {nome}")


def perguntar(pergunta: str, historico: list | None = None) -> tuple[str, list]:
    """
    Manda uma pergunta pro agente. `historico` é uma lista de
    `types.Content` (não dicts) com o texto final de perguntas/respostas
    anteriores — os dados brutos de tools passadas NÃO ficam salvos aqui,
    só são usados dentro do turno atual (evita estourar limite de tokens
    em conversas longas).
    Retorna (resposta_texto, novo_historico).
    """
    historico = historico or []
    # mantém só as últimas 3 trocas de pergunta/resposta como contexto
    contents = list(historico[-6:])
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=pergunta)]))

    for _ in range(5):
        resp = client.models.generate_content(model=MODEL, contents=contents, config=_CONFIG)
        candidate = resp.candidates[0]
        function_calls = [p.function_call for p in candidate.content.parts if p.function_call]

        if not function_calls:
            texto = resp.text or ""
            novo_historico = historico + [
                types.Content(role="user", parts=[types.Part.from_text(text=pergunta)]),
                types.Content(role="model", parts=[types.Part.from_text(text=texto)]),
            ]
            return texto, novo_historico

        contents.append(candidate.content)
        response_parts = []
        for fc in function_calls:
            resultado = _executar_tool(fc.name, dict(fc.args or {}))
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
    return texto, novo_historico
