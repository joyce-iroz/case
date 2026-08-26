import os
from supabase import create_client, Client

# --- onde a SUPABASE_URL e a SUPABASE_SECRET_KEY são usadas --------
# secret key porque é o backend falando direto com o banco, sem
# passar por login de usuário nenhum.
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SECRET_KEY = os.environ["SUPABASE_SECRET_KEY"]
# ---------------------------------------------------------------------

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    return _client


def consultar_aberturas(
    ano: int | None = None,
    mes: int | None = None,
    cidade: str | None = None,
    segmento: str | None = None,
    limite: int = 50,
) -> list[dict]:
    """
    Consulta a tabela base_dados com filtros opcionais.
    Usada como 'tool' pelo agente (ver app/gemini_agent.py).

    OBS: o limite padrão é baixo de propósito (50 linhas) para não
    estourar o limite de tokens por minuto de contas gratuitas do
    Groq — se a consulta vier sem nenhum filtro (ano/mes/cidade/
    segmento todos nulos), o limite é reduzido ainda mais.
    """
    client = get_client()
    # não seleciona a coluna "id" (não é útil pro agente e só gasta tokens)
    query = client.table("base_dados").select(
        "ano,mes,cidade_agrupada,class_segmentos,abertura_empresas"
    )

    sem_filtro = ano is None and mes is None and cidade is None and segmento is None
    if ano is not None:
        query = query.eq("ano", ano)
    if mes is not None:
        query = query.eq("mes", mes)
    if cidade is not None:
        query = query.ilike("cidade_agrupada", f"%{cidade}%")
    if segmento is not None:
        query = query.ilike("class_segmentos", f"%{segmento}%")

    limite_efetivo = min(limite, 10) if sem_filtro else min(limite, 80)
    resp = query.limit(limite_efetivo).execute()
    return resp.data


def totais_aberturas(
    ano: int | None = None,
    mes: int | None = None,
    cidade: str | None = None,
    segmento: str | None = None,
    agrupar_por: str = "ano",
) -> list[dict]:
    """
    Retorna totais JÁ SOMADOS (agregados no banco, via função SQL
    totais_aberturas — ver schema.sql), agrupados por 'ano', 'mes',
    'cidade' ou 'segmento'. Uma chamada aqui substitui dezenas/centenas
    de linhas cruas — use isso para perguntas de visão geral, totais,
    comparações e projeções.
    """
    if agrupar_por not in {"ano", "mes", "cidade", "segmento"}:
        agrupar_por = "ano"
    client = get_client()
    resp = client.rpc(
        "totais_aberturas",
        {
            "p_ano": ano,
            "p_mes": mes,
            "p_cidade": cidade,
            "p_segmento": segmento,
            "p_agrupar_por": agrupar_por,
        },
    ).execute()
    return resp.data
