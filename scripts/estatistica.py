import numpy as np
import pandas as pd
from scipy.stats import f_oneway, kruskal, levene, tukey_hsd


ALPHA = 0.05


def _obter_grupos(df, coluna, coluna_grupo="Grupos de usuários"):
    """
    Quebra a coluna numérica em uma lista de séries, uma por grupo.
    Descarta grupos sem dados válidos.
    """

    nomes = []
    grupos = []

    for nome_grupo in df[coluna_grupo].unique():
        valores = df.loc[df[coluna_grupo] == nome_grupo, coluna].dropna()

        if len(valores) >= 2:
            nomes.append(nome_grupo)
            grupos.append(valores)

    return nomes, grupos


def calcular_margem_diaria(df):
    """
    Calcula a margem de lucro diária (%) por linha: (comissão - cashback) / vendas * 100.
    Essa é a métrica de negócio usada no teste de decisão — não o volume de compradores.
    """

    df = df.copy()
    vendas_seguro = df["vendas totais"].replace(0, pd.NA)

    df["margem_lucro_dia"] = (
        (df["comissão"] - df["cashback"]) / vendas_seguro
    ) * 100

    return df


def detectar_instabilidade_variante(df, coluna_grupo="Grupos de usuários", limite_variacao=10.0):
    """
    Verifica se a % de cashback sobre comissão se mantém estável dentro de cada
    grupo ao longo do tempo. Se a variante "vaza" (a % muda no meio do teste),
    misturar o período inteiro na análise pode mascarar ou inflar o resultado.
    Retorna a lista de grupos instáveis para o relatório sinalizar.
    """

    df = df.copy()
    df["mes"] = df["Data"].dt.to_period("M")
    comissao_segura = df["comissão"].replace(0, pd.NA)
    df["taxa_cashback_comissao"] = (df["cashback"] / comissao_segura) * 100

    grupos_instaveis = []

    for nome_grupo, dados_grupo in df.groupby(coluna_grupo):
        taxa_por_mes = dados_grupo.groupby("mes")["taxa_cashback_comissao"].mean()

        if len(taxa_por_mes) < 2:
            continue

        variacao = taxa_por_mes.max() - taxa_por_mes.min()

        if variacao > limite_variacao:
            grupos_instaveis.append(
                {
                    "grupo": nome_grupo,
                    "variacao_pontos_percentuais": round(variacao, 1),
                    "taxa_por_mes": taxa_por_mes.round(1).to_dict(),
                }
            )

    if grupos_instaveis:
        print("\n" + "=" * 60)
        print("⚠️  ALERTA: INSTABILIDADE NA DEFINIÇÃO DA VARIANTE")
        print("=" * 60)
        for item in grupos_instaveis:
            print(
                f"{item['grupo']}: taxa de cashback/comissão variou "
                f"{item['variacao_pontos_percentuais']} p.p. ao longo do período "
                f"{item['taxa_por_mes']}"
            )
        print(
            "A % de cashback desse(s) grupo(s) não é constante durante o teste. "
            "Isso pode indicar uma mudança de configuração no meio do período, "
            "contaminando a comparação entre variantes. Considere isolar "
            "sub-períodos antes de decidir."
        )

    return grupos_instaveis


def verificar_pressupostos(grupos):
    """
    Testa homogeneidade de variância entre os grupos (Levene).
    Usado para decidir entre ANOVA (paramétrico) e Kruskal-Wallis (não-paramétrico).
    """

    if len(grupos) < 2:
        return True

    _, p_levene = levene(*grupos)
    variancias_homogeneas = p_levene >= ALPHA

    print(f"Teste de Levene (variâncias) — p-valor: {round(p_levene, 6)}")

    if variancias_homogeneas:
        print("✅ Variâncias homogêneas entre grupos — ANOVA é apropriada.")
    else:
        print("⚠️  Variâncias diferentes entre grupos — usando Kruskal-Wallis (não-paramétrico).")

    return variancias_homogeneas


def _eta_quadrado_anova(grupos, estatistica_f):
    """
    Effect size da ANOVA (eta²): qual fração da variação total é explicada
    pela variante. Complementa o p-valor, que sozinho não diz se a diferença
    tem relevância prática.
    """

    todos_valores = np.concatenate([np.asarray(g) for g in grupos])
    media_geral = todos_valores.mean()

    ss_entre = sum(
        len(g) * (np.asarray(g).mean() - media_geral) ** 2 for g in grupos
    )
    ss_total = sum((todos_valores - media_geral) ** 2)

    return ss_entre / ss_total if ss_total > 0 else 0.0


def realizar_teste_sanidade(df, coluna_grupo="Grupos de usuários"):
    """
    ANOVA sobre 'compradores' — não decide a variante vencedora, serve para
    checar se a alocação de tráfego entre os grupos foi comparável. Se der
    significativo aqui, é sinal de problema na randomização do teste, não
    uma informação sobre qual variante é melhor.
    """

    nomes, grupos = _obter_grupos(df, "compradores", coluna_grupo)

    print("\n" + "=" * 60)
    print("TESTE DE SANIDADE (volume de compradores por grupo)")
    print("=" * 60)

    if len(grupos) < 2:
        print("⚠️  Grupos insuficientes para comparar — pulando teste de sanidade.")
        return None

    estatistica, p_valor = f_oneway(*grupos)
    significativo = p_valor < ALPHA

    print(f"Estatística F : {round(estatistica, 4)}")
    print(f"P-valor       : {round(p_valor, 6)}")

    if significativo:
        print(
            "⚠️  Volume de compradores difere significativamente entre grupos — "
            "verifique se a randomização/alocação de tráfego foi feita corretamente "
            "antes de confiar na comparação de lucro."
        )
    else:
        print("✅ Grupos com volume de tráfego comparável.")

    return {
        "teste": "ANOVA (sanidade - compradores)",
        "estatistica_f": round(estatistica, 4),
        "p_valor": round(p_valor, 6),
        "significativo": significativo,
    }


def realizar_teste_decisao(df, coluna="margem_lucro_dia", coluna_grupo="Grupos de usuários"):
    """
    Teste que efetivamente embasa a decisão de qual variante escalar:
    compara a margem de lucro diária entre grupos. Escolhe ANOVA ou
    Kruskal-Wallis conforme o resultado do teste de Levene, e reporta
    effect size junto do p-valor.
    """

    nomes, grupos = _obter_grupos(df, coluna, coluna_grupo)

    print("\n" + "=" * 60)
    print(f"TESTE DE DECISÃO (comparando '{coluna}' entre grupos)")
    print("=" * 60)

    if len(grupos) < 2:
        print("❌ Grupos insuficientes para decidir estatisticamente entre variantes.")
        return None

    variancias_homogeneas = verificar_pressupostos(grupos)

    if variancias_homogeneas:
        estatistica, p_valor = f_oneway(*grupos)
        nome_teste = "ANOVA"
        effect_size = _eta_quadrado_anova(grupos, estatistica)
        nome_effect_size = "eta²"
    else:
        estatistica, p_valor = kruskal(*grupos)
        nome_teste = "Kruskal-Wallis"
        # epsilon² como aproximação de effect size não-paramétrico
        n_total = sum(len(g) for g in grupos)
        effect_size = (estatistica - len(grupos) + 1) / (n_total - len(grupos))
        effect_size = max(effect_size, 0.0)
        nome_effect_size = "epsilon²"

    significativo = p_valor < ALPHA

    print(f"\nTeste usado  : {nome_teste}")
    print(f"Estatística  : {round(estatistica, 4)}")
    print(f"P-valor      : {round(p_valor, 6)}")
    print(f"{nome_effect_size} (effect size) : {round(effect_size, 4)}")

    if significativo:
        print(f"\n✅ Diferença estatisticamente significativa entre as variantes ({nome_teste}).")
        if effect_size < 0.01:
            print(
                "⚠️  Atenção: mesmo significativo, o effect size é muito pequeno — "
                "a diferença pode não ter relevância prática de negócio."
            )
    else:
        print(f"\n⚠️  Nenhuma diferença estatisticamente significativa encontrada ({nome_teste}).")
        print(
            "Não há evidência estatística suficiente para escalar uma variante "
            "específica com confiança — considere rodar o teste por mais tempo."
        )

    resultado = {
        "teste": nome_teste,
        "estatistica": round(estatistica, 4),
        "p_valor": round(p_valor, 6),
        "effect_size": round(effect_size, 4),
        "nome_effect_size": nome_effect_size,
        "significativo": significativo,
    }

    if significativo and len(grupos) >= 3:
        resultado["post_hoc"] = realizar_tukey(nomes, grupos)

    return resultado


def realizar_tukey(nomes, grupos):
    """
    Post-hoc Tukey HSD — necessário quando há 3+ grupos e a ANOVA/Kruskal deu
    significativa, pois esses testes só dizem que existe diferença em algum
    lugar, não qual par de grupos difere.
    """

    print("\n" + "-" * 60)
    print("POST-HOC (Tukey HSD) — qual par de grupos difere")
    print("-" * 60)

    resultado_tukey = tukey_hsd(*grupos)
    pares_significativos = []

    for i in range(len(nomes)):
        for j in range(i + 1, len(nomes)):
            p_par = resultado_tukey.pvalue[i, j]
            diferente = p_par < ALPHA

            print(
                f"{nomes[i]} vs {nomes[j]} — p-valor: {round(p_par, 6)}"
                f" {'✅ diferem' if diferente else '⚠️ sem diferença clara'}"
            )

            if diferente:
                pares_significativos.append((nomes[i], nomes[j], round(p_par, 6)))

    return pares_significativos


def analisar_estatisticamente(df, coluna_grupo="Grupos de usuários"):
    """
    Orquestra a análise estatística completa de um teste A/B:
    1) checa estabilidade da definição da variante ao longo do tempo
    2) roda teste de sanidade (tráfego comparável entre grupos)
    3) roda o teste que decide a variante (margem de lucro diária)
    4) roda post-hoc se necessário
    """

    df = calcular_margem_diaria(df)

    instabilidade = detectar_instabilidade_variante(df, coluna_grupo)
    sanidade = realizar_teste_sanidade(df, coluna_grupo)
    decisao = realizar_teste_decisao(df, "margem_lucro_dia", coluna_grupo)

    return {
        "instabilidade_variante": instabilidade,
        "teste_sanidade": sanidade,
        "teste_decisao": decisao,
    }