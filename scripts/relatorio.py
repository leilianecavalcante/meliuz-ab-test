from datetime import datetime
from pathlib import Path
import re


COLUNAS_RELATORIO = [
    ("compradores", "Compradores", "{:.0f}"),
    ("vendas", "Vendas Totais (R$)", "{:,.2f}"),
    ("comissao", "Comissão (R$)", "{:,.2f}"),
    ("cashback", "Cashback (R$)", "{:,.2f}"),
    ("lucro", "Lucro (R$)", "{:,.2f}"),
    ("margem_lucro", "Margem de Lucro (%)", "{:.2f}"),
    ("taxa_cashback_sobre_comissao", "Taxa Cashback/Comissão (%)", "{:.1f}"),
    ("ticket_medio", "Ticket Médio (R$)", "{:,.2f}"),
    ("roi", "ROI", "{:.2f}"),
]


def _slug(texto):
    """
    Transforma "Parceiro A" em "parceiro_a", pra usar em nome de arquivo.
    """

    texto = texto.lower().strip()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")


def _formatar_p_valor(p_valor):
    """
    Formata o p-valor de um jeito que não confunde quem não é estatístico.
    "p=0.0" parece um erro de arredondamento (nenhum p-valor é literalmente
    zero); "p<0.001" comunica a mesma ideia — a diferença dificilmente é
    coincidência — sem parecer estranho.
    """

    if p_valor is None:
        return "N/D"

    return "p<0.001" if p_valor < 0.001 else f"p={p_valor:.3f}"


def _interpretar_effect_size(effect_size):
    """
    Traduz o effect size (eta²/epsilon²) em uma palavra que um gestor
    entende sem precisar saber a fórmula por trás. Faixas usuais adaptadas
    de Cohen para eta²: <0.01 muito pequeno, <0.06 pequeno, <0.14 médio,
    caso contrário grande.
    """

    if effect_size < 0.01:
        return "muito pequeno — cuidado, mesmo com p baixo a diferença pode não valer a pena na prática"
    if effect_size < 0.06:
        return "pequeno"
    if effect_size < 0.14:
        return "médio"
    return "grande"


def _montar_tabela_markdown(metricas):
    """
    Monta a tabela de métricas por variante em Markdown, sem depender de
    bibliotecas externas (evita adicionar dependência só pra formatar tabela).
    """

    colunas_presentes = [
        (chave, titulo, fmt)
        for chave, titulo, fmt in COLUNAS_RELATORIO
        if chave in metricas.columns
    ]

    cabecalho = "| Variante | " + " | ".join(titulo for _, titulo, _ in colunas_presentes) + " |"
    separador = "|---" * (len(colunas_presentes) + 1) + "|"

    linhas = [cabecalho, separador]

    for grupo, dados in metricas.iterrows():
        valores = []
        for chave, _, fmt in colunas_presentes:
            valor = dados[chave]
            try:
                valores.append(fmt.format(valor))
            except (ValueError, TypeError):
                valores.append("N/D")

        linhas.append(f"| {grupo} | " + " | ".join(valores) + " |")

    return "\n".join(linhas)


def _montar_secao_instabilidade(instabilidade):
    if not instabilidade:
        return "Nenhuma instabilidade detectada na definição das variantes ao longo do período.\n"

    linhas = [
        "⚠️ **A % de cashback de uma ou mais variantes não se manteve constante "
        "durante o teste.** Isso pode indicar uma mudança de configuração no meio "
        "do período, contaminando a comparação entre grupos. Recomenda-se isolar "
        "sub-períodos antes de confiar totalmente no resultado.\n",
    ]

    for item in instabilidade:
        taxa_por_mes = ", ".join(
            f"{mes}: {valor}%" for mes, valor in item["taxa_por_mes"].items()
        )
        linhas.append(
            f"- **{item['grupo']}** — variação de {item['variacao_pontos_percentuais']} "
            f"pontos percentuais na taxa de cashback/comissão ({taxa_por_mes})"
        )

    return "\n".join(linhas)


def _montar_secao_estatistica(estatistica):
    sanidade = estatistica.get("teste_sanidade")
    decisao_teste = estatistica.get("teste_decisao")

    linhas = []

    if sanidade:
        status = (
            "⚠️ diferença significativa — verificar alocação de tráfego"
            if sanidade["significativo"]
            else "✅ tráfego comparável entre grupos"
        )
        linhas.append(
            f"**O tráfego foi dividido de forma parecida entre as variantes?** "
            f"{status} ({_formatar_p_valor(sanidade['p_valor'])}). Isso é só uma "
            f"checagem de sanidade — se der diferente aqui, pode ser sinal de "
            f"problema na randomização do teste, não uma informação sobre qual "
            f"variante é melhor."
        )

    if decisao_teste:
        p_texto = _formatar_p_valor(decisao_teste["p_valor"])
        interpretacao_effect = _interpretar_effect_size(decisao_teste["effect_size"])

        if decisao_teste["significativo"]:
            conclusao = (
                f"✅ **Sim** — a diferença de margem entre as variantes é real, "
                f"não é coincidência ({p_texto}). O tamanho dessa diferença é "
                f"**{interpretacao_effect}**."
            )
        else:
            conclusao = (
                f"⚠️ **Não** — não há evidência suficiente de que a diferença "
                f"observada seja real e não apenas variação do dia a dia "
                f"({p_texto}). Considere rodar o teste por mais tempo."
            )

        linhas.append(
            f"\n**A diferença de margem entre as variantes é real ou é sorte?** "
            f"{conclusao}\n\n"
            f"_Detalhe técnico: teste {decisao_teste['teste']} "
            f"(escolhido automaticamente conforme a distribuição dos dados), "
            f"estatística={decisao_teste['estatistica']}, "
            f"{decisao_teste['nome_effect_size']}={decisao_teste['effect_size']}._"
        )

        post_hoc = decisao_teste.get("post_hoc")
        if post_hoc:
            linhas.append(
                "\n**Quais variantes diferem entre si de fato "
                "(teste post-hoc Tukey HSD):**"
            )
            for grupo_a, grupo_b, p_valor in post_hoc:
                linhas.append(f"- {grupo_a} vs {grupo_b} ({_formatar_p_valor(p_valor)})")

    return "\n".join(linhas) if linhas else "Nenhum teste estatístico disponível.\n"


def gerar_relatorio(
    parceiro,
    decisao,
    metricas,
    estatistica,
    data_inicio=None,
    data_fim=None,
    pasta_saida="reports",
):
    """
    Gera um relatório em Markdown, apresentável para um gestor, com:
    - decisão final e o porquê
    - tabela de métricas por variante
    - alertas de qualidade de dados (instabilidade)
    - resultado dos testes estatísticos, em linguagem acessível a quem não
      é estatístico, com os detalhes técnicos disponíveis para quem quiser

    Retorna o caminho do arquivo gerado.
    """

    Path(pasta_saida).mkdir(parents=True, exist_ok=True)

    agora = datetime.now().strftime("%Y-%m-%d %H:%M")
    nome_arquivo = f"relatorio_{_slug(parceiro)}.md"
    caminho_arquivo = Path(pasta_saida) / nome_arquivo

    variante_texto = decisao["variante"] or "Nenhuma variante recomendada no momento"

    periodo_linha = ""
    if data_inicio and data_fim:
        periodo_linha = f"_Período analisado: {data_inicio} a {data_fim}_\n\n"

    conteudo = f"""# Relatório de Teste A/B — {parceiro}

_Gerado em {agora}_

{periodo_linha}## Decisão recomendada

**Variante: {variante_texto}**
**Confiança: {decisao['confianca']}**

{decisao['motivo']}

## Métricas por variante

{_montar_tabela_markdown(metricas)}

## Alertas de qualidade de dados

{_montar_secao_instabilidade(estatistica.get("instabilidade_variante"))}

## Essa diferença é real ou é ruído?

{_montar_secao_estatistica(estatistica)}
"""

    caminho_arquivo.write_text(conteudo, encoding="utf-8")

    print(f"✅ Relatório gerado em: {caminho_arquivo}")

    return caminho_arquivo