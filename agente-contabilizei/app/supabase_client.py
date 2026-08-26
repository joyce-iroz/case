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
    limite: int = 500,
) -> list[dict]:
    """
    Consulta a tabela base_dados com filtros opcionais.
    Usada como 'tool' pelo agente (ver app/groq_agent.py).
    """
    client = get_client()
    query = client.table("base_dados").select("*")

    if ano is not None:
        query = query.eq("ano", ano)
    if mes is not None:
        query = query.eq("mes", mes)
    if cidade is not None:
        query = query.ilike("cidade_agrupada", f"%{cidade}%")
    if segmento is not None:
        query = query.ilike("class_segmentos", f"%{segmento}%")

    resp = query.limit(limite).execute()
    return resp.data
