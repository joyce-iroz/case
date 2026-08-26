import os
import json
from groq import Groq

from app.supabase_client import consultar_aberturas

# --- onde a GROQ_API_KEY é usada --------------------------------
# O client já lê GROQ_API_KEY do ambiente automaticamente, mas
# deixamos explícito aqui pra ficar claro de onde vem.
client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
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
nunca invente valores. Se a pergunta pedir uma agregação (soma, média,
crescimento), busque os dados granulares com a tool e calcule você mesmo
na resposta, explicando o raciocínio de forma breve.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_aberturas",
            "description": (
                "Consulta a tabela base_dados no Supabase, com filtros "
                "opcionais por ano, mês, cidade e segmento. Retorna as "
                "linhas granulares (não agregadas). Para um filtro que "
                "não deve ser aplicado, passe null."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ano": {
                        "type": ["integer", "null"],
                        "description": "Ex.: 2025. Use null para não filtrar por ano.",
                    },
                    "mes": {
                        "type": ["integer", "null"],
                        "description": "1 a 12. Use null para não filtrar por mês.",
                    },
                    "cidade": {
                        "type": ["string", "null"],
                        "description": "Busca parcial, ex.: 'SAO PAULO'. Use null para não filtrar.",
                    },
                    "segmento": {
                        "type": ["string", "null"],
                        "description": "Busca parcial, ex.: 'Psicologia'. Use null para não filtrar.",
                    },
                },
                "required": ["ano", "mes", "cidade", "segmento"],
                "additionalProperties": False,
            },
        },
    }
]


def _executar_tool(nome: str, argumentos: dict):
    if nome == "consultar_aberturas":
        return consultar_aberturas(**argumentos)
    raise ValueError(f"Tool desconhecida: {nome}")


def perguntar(pergunta: str, historico: list[dict] | None = None) -> tuple[str, list[dict]]:
    """
    Manda uma pergunta pro agente. `historico` é a lista de mensagens
    anteriores (sem o system prompt), para manter contexto entre turnos.
    Retorna (resposta_texto, novo_historico).
    """
    mensagens = [{"role": "system", "content": SYSTEM_PROMPT}]
    mensagens += historico or []
    mensagens.append({"role": "user", "content": pergunta})

    # loop simples de tool-calling (até 5 idas e voltas)
    for _ in range(5):
        resp = client.chat.completions.create(
            model=MODEL,
            messages=mensagens,
            tools=TOOLS,
            tool_choice="auto",
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            novo_historico = mensagens[1:] + [{"role": "assistant", "content": msg.content}]
            return msg.content, novo_historico

        mensagens.append(msg)
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            resultado = _executar_tool(call.function.name, args)
            mensagens.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(resultado, ensure_ascii=False, default=str),
                }
            )

    return "Não consegui concluir — muitas chamadas de ferramenta.", mensagens[1:]
