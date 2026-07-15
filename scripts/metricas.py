import pandas as pd


def calcular_metricas(df):
    """
    Calcula as principais métricas do teste A/B por grupo.
    """

    metricas = (
        df.groupby("Grupos de usuários")
        .agg(
            compradores=("compradores", "sum"),
            comissao=("comissão", "sum"),
            cashback=("cashback", "sum"),
            vendas=("vendas totais", "sum"),
            dias=("Data", "count"),
        )
    )

    # Denominadores "seguros" — evita divisão por zero virar erro ou inf silencioso
    compradores_seguro = metricas["compradores"].replace(0, pd.NA)
    cashback_seguro = metricas["cashback"].replace(0, pd.NA)
    vendas_seguro = metricas["vendas"].replace(0, pd.NA)
    comissao_seguro = metricas["comissao"].replace(0, pd.NA)

    # Lucro
    metricas["lucro"] = (
        metricas["comissao"] - metricas["cashback"]
    )

    # ROI
    metricas["roi"] = metricas["lucro"] / cashback_seguro

    # Ticket médio
    metricas["ticket_medio"] = metricas["vendas"] / compradores_seguro

    # Comissão média por comprador
    metricas["comissao_por_comprador"] = metricas["comissao"] / compradores_seguro

    # Cashback médio por comprador
    metricas["cashback_por_comprador"] = metricas["cashback"] / compradores_seguro

    # Lucro médio por comprador
    metricas["lucro_por_comprador"] = metricas["lucro"] / compradores_seguro

    # Percentual de cashback sobre vendas
    metricas["cashback_percentual"] = (metricas["cashback"] / vendas_seguro) * 100

    # Comissão sobre vendas
    metricas["comissao_percentual"] = (metricas["comissao"] / vendas_seguro) * 100

    # Lucro sobre vendas — métrica normalizada, não depende do volume do grupo
    metricas["margem_lucro"] = (metricas["lucro"] / vendas_seguro) * 100

    # Taxa de cashback sobre comissão — é isso que de fato define a variante
    # (ex: 82% significa que o grupo devolveu 82% da comissão como cashback)
    metricas["taxa_cashback_sobre_comissao"] = (
        metricas["cashback"] / comissao_seguro
    ) * 100

    return metricas


def mostrar_metricas(metricas):
    """
    Exibe todas as métricas calculadas.
    """

    print("\n")
    print("=" * 80)
    print("MÉTRICAS DO TESTE A/B")
    print("=" * 80)

    print(metricas.round(2))

    print("\n")
    print("=" * 80)
    print("RANKING (por margem de lucro sobre vendas)")
    print("=" * 80)

    # Ranqueia por margem_lucro (%), não por lucro total — assim o grupo
    # com mais tráfego no período não vence só por volume.
    ranking = metricas.sort_values(
        by="margem_lucro",
        ascending=False
    )

    for posicao, (grupo, dados) in enumerate(ranking.iterrows(), start=1):

        print(
            f"{posicao}º - {grupo}"
            f" | Margem: {dados['margem_lucro']:.2f}%"
            f" | Lucro total: R$ {dados['lucro']:,.2f}"
            f" | ROI: {dados['roi']:.2f}"
            f" | Taxa cashback/comissão: {dados['taxa_cashback_sobre_comissao']:.1f}%"
        )

    candidato = ranking.index[0]

    print("\n")
    print("=" * 80)
    print("MAIOR MARGEM OBSERVADA (ainda sem teste de significância)")
    print("=" * 80)

    print(
        f"📊 {candidato} — decisão final depende da validação estatística "
        f"(ver estatistica.py)"
    )

    return candidato