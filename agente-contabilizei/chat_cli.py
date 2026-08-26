"""
Teste rápido do agente pelo terminal.

Uso:
    python chat_cli.py
"""
from dotenv import load_dotenv

load_dotenv()

from app.gemini_agent import perguntar  # noqa: E402  (import depois do load_dotenv)


def main():
    print("Agente Contabilizei — digite sua pergunta (ou 'sair' para encerrar)\n")
    historico = []
    while True:
        pergunta = input("Você: ").strip()
        if pergunta.lower() in {"sair", "exit", "quit"}:
            break
        resposta, historico, graficos, relatorios = perguntar(pergunta, historico)
        print(f"\nAgente: {resposta}\n")
        for caminho in graficos:
            print(f"[gráfico salvo em: {caminho}]\n")
        for caminho in relatorios:
            print(f"[relatório PDF salvo em: {caminho}]\n")


if __name__ == "__main__":
    main()
