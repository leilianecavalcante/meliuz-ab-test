# Relatório de Teste A/B — Parceiro C

_Gerado em 2026-07-15 00:43_

_Período analisado: 2011-07-01 a 2011-08-14_

## Decisão recomendada

**Variante: Grupo 1**
**Confiança: alta**

Grupo 1 tem a maior margem de lucro observada e a diferença é estatisticamente significativa (Kruskal-Wallis, p=0.0).

## Métricas por variante

| Variante | Compradores | Vendas Totais (R$) | Comissão (R$) | Cashback (R$) | Lucro (R$) | Margem de Lucro (%) | Taxa Cashback/Comissão (%) | Ticket Médio (R$) | ROI |
|---|---|---|---|---|---|---|---|---|---|
| Grupo 1 | 4549 | 1,738,460.00 | 121,693.00 | 86,924.00 | 34,769.00 | 2.00 | 71.4 | 382.16 | 0.40 |
| Grupo 2 | 4522 | 1,685,235.00 | 117,967.00 | 117,967.00 | 0.00 | 0.00 | 100.0 | 372.67 | 0.00 |

## Alertas de qualidade de dados

Nenhuma instabilidade detectada na definição das variantes ao longo do período.


## Essa diferença é real ou é ruído?

**O tráfego foi dividido de forma parecida entre as variantes?** ✅ tráfego comparável entre grupos (p=0.922). Isso é só uma checagem de sanidade — se der diferente aqui, pode ser sinal de problema na randomização do teste, não uma informação sobre qual variante é melhor.

**A diferença de margem entre as variantes é real ou é sorte?** ✅ **Sim** — a diferença de margem entre as variantes é real, não é coincidência (p<0.001). O tamanho dessa diferença é **grande**.

_Detalhe técnico: teste Kruskal-Wallis (escolhido automaticamente conforme a distribuição dos dados), estatística=76.2911, epsilon²=0.8556._
