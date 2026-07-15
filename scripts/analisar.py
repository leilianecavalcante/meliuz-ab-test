from pathlib import Path
import sys

from limpeza import carregar_csv, validar_schema, limpar_dados
from metricas import calcular_metricas, mostrar_metricas
from estatistica import analisar_estatisticamente
from relatorio import gerar_relatorio
from planilha import atualizar_resumo


# Raiz do projeto = pasta pai de scripts/, calculada a partir da localização
# deste arquivo (não do diretório de onde o comando é executado). Isso evita
# que reports/ e outputs/ sejam criados no lugar errado se alguém rodar o
# script de dentro de scripts/ (ex: "cd scripts && python analisar.py ...")
# em vez de a partir da raiz, como o README recomenda.
RAIZ_PROJETO = Path(__file__).resolve().parent.parent


def decidir_variante(metricas, resultado_estatistico):
    """
    Decide qual variante recomendar para escalar, combinando a métrica de
    negócio (margem de lucro) com o resultado do teste estatístico e com
    o alerta de instabilidade — em vez de só pegar o maior número.
    """

    ranking = metricas.sort_values(by="margem_lucro", ascending=False)
    candidato = ranking.index[0]

    instabilidade = resultado_estatistico.get("instabilidade_variante") or []
    teste_decisao = resultado_estatistico.get("teste_decisao")

    grupos_instaveis = {item["grupo"] for item in instabilidade}

    if candidato in grupos_instaveis:
        return {
            "variante": candidato,
            "confianca": "baixa",
            "motivo": (
                f"{candidato} tem a maior margem observada, mas a % de cashback "
                "desse grupo não foi estável durante o teste (ver alerta de "
                "instabilidade). Recomenda-se isolar sub-períodos antes de "
                "escalar."
            ),
        }

    if teste_decisao is None or not teste_decisao.get("significativo"):
        return {
            "variante": None,
            "confianca": "insuficiente",
            "motivo": (
                "Nenhuma diferença estatisticamente significativa entre as "
                "variantes foi encontrada. Não há evidência suficiente para "
                "recomendar escalar uma variante específica agora."
            ),
        }

    return {
        "variante": candidato,
        "confianca": "alta",
        "motivo": (
            f"{candidato} tem a maior margem de lucro observada e a diferença "
            f"é estatisticamente significativa ({teste_decisao['teste']}, "
            f"p={teste_decisao['p_valor']})."
        ),
    }


def main():

    if len(sys.argv) != 2:
        print("\nUso:")
        print("py scripts/analisar.py datasets/dataset_01_parceiroA.csv")
        sys.exit()

    caminho = Path(sys.argv[1])

    if not caminho.exists():
        print(f"❌ Arquivo não encontrado: {caminho}")
        sys.exit()

    # ===============================
    # 1. Ler CSV
    # ===============================
    df = carregar_csv(caminho)

    # ===============================
    # 2. Validar schema e limpar dados
    # ===============================
    validar_schema(df)
    df = limpar_dados(df)

    # ===============================
    # 3. Calcular métricas
    # ===============================
    metricas = calcular_metricas(df)
    mostrar_metricas(metricas)

    # ===============================
    # 4. Estatística (sanidade + decisão + instabilidade)
    # ===============================
    resultado_estatistico = analisar_estatisticamente(df)

    # ===============================
    # 5. Decidir variante
    # ===============================
    decisao = decidir_variante(metricas, resultado_estatistico)

    parceiro = df["Parceiro"].iloc[0]
    data_inicio = df["Data"].min().strftime("%Y-%m-%d")
    data_fim = df["Data"].max().strftime("%Y-%m-%d")

    # ===============================
    # 6. Gerar relatório
    # ===============================
    pasta_reports = RAIZ_PROJETO / "reports"
    pasta_reports.mkdir(parents=True, exist_ok=True)

    gerar_relatorio(
        parceiro=parceiro,
        decisao=decisao,
        metricas=metricas,
        estatistica=resultado_estatistico,
        data_inicio=data_inicio,
        data_fim=data_fim,
        pasta_saida=pasta_reports,
    )

    # ===============================
    # 7. Atualizar resumo (planilha/CSV)
    # ===============================
    pasta_outputs = RAIZ_PROJETO / "outputs"
    pasta_outputs.mkdir(parents=True, exist_ok=True)

    atualizar_resumo(
        parceiro=parceiro,
        decisao=decisao,
        metricas=metricas,
        estatistica=resultado_estatistico,
        data_inicio=data_inicio,
        data_fim=data_fim,
        pasta_saida=pasta_outputs,
    )

    # ===============================
    # Resultado Final
    # ===============================

    print("\n" + "=" * 60)
    print("DECISÃO FINAL")
    print("=" * 60)

    print(f"Parceiro: {parceiro}")
    print(f"Variante recomendada: {decisao['variante'] or 'nenhuma (ver motivo)'}")
    print(f"Confiança: {decisao['confianca']}")
    print(f"Motivo: {decisao['motivo']}")

    print("\nRelatório salvo em reports/")
    print("Resumo salvo em outputs/")


if __name__ == "__main__":
    main()