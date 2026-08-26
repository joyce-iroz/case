import os
import uuid

import matplotlib
matplotlib.use("Agg")  
import matplotlib.pyplot as plt

# Pasta temporária onde os gráficos gerados na sessão ficam salvos.
GRAFICOS_DIR = "/tmp/graficos_agente"
os.makedirs(GRAFICOS_DIR, exist_ok=True)

CORES = ["#1F4E78", "#C00000", "#548235", "#BF8F00", "#7030A0", "#2E75B6"]


def criar_grafico(dados: list[dict], tipo: str, titulo: str, rotulo_eixo_y: str = "Aberturas de empresas") -> str:
    """
    Recebe dados no formato [{"chave": "2024", "total": 288281}, ...]
    (mesmo formato retornado por totais_aberturas), monta um gráfico de
    barra ou linha, salva como PNG e retorna o caminho do arquivo.
    """
    if not dados:
        raise ValueError("Sem dados para plotar.")

    chaves = [str(d.get("chave", "")) for d in dados]
    valores = [d.get("total", 0) or 0 for d in dados]

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=130)

    if tipo == "linha":
        ax.plot(chaves, valores, color=CORES[0], linewidth=2.2, marker="o", markersize=4)
        ax.fill_between(range(len(chaves)), valores, color=CORES[0], alpha=0.08)
    else:  # barra (padrão)
        ax.bar(chaves, valores, color=CORES[0])

    ax.set_title(titulo, fontsize=12, fontweight="bold", color="#1F4E78", pad=12)
    ax.set_ylabel(rotulo_eixo_y, fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", labelrotation=45 if len(chaves) > 8 else 0, labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(axis="y", color="#E0E0E0", linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()

    nome_arquivo = f"{uuid.uuid4().hex}.png"
    caminho = os.path.join(GRAFICOS_DIR, nome_arquivo)
    fig.savefig(caminho, facecolor="white")
    plt.close(fig)
    return caminho
