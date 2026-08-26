"""
Sobe os dados do case (Dados_Case_2026.xlsx) para a tabela `base_dados`
no Supabase. Rode uma vez só, depois que a tabela existir (schema.sql).

Uso:
    python load_data.py caminho/para/Dados_Case_2026.xlsx
"""
import sys
import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# --- onde a SUPABASE_SECRET_KEY é usada -----------------------------
# Precisa da secret key (não a publishable) porque é uma escrita em massa.
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SECRET_KEY = os.environ["SUPABASE_SECRET_KEY"]
# ---------------------------------------------------------------------

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


def main(path: str):
    df = pd.read_excel(path, sheet_name="Extração 1")
    df = df[["ano", "mes", "cidade_agrupada", "class_segmentos", "abertura_empresas"]]

    registros = df.to_dict(orient="records")
    print(f"Enviando {len(registros)} linhas para o Supabase...")

    # envia em lotes de 1000 (limite prático da API REST do Supabase)
    tamanho_lote = 1000
    for i in range(0, len(registros), tamanho_lote):
        lote = registros[i : i + tamanho_lote]
        supabase.table("base_dados").insert(lote).execute()
        print(f"  {i + len(lote)}/{len(registros)} enviadas")

    print("Concluído.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python load_data.py caminho/para/Dados_Case_2026.xlsx")
        sys.exit(1)
    main(sys.argv[1])
