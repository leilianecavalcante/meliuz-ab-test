# Relatório de Teste A/B — Parceiro B

_Gerado em 2026-07-15 00:42_

_Período analisado: 2011-05-01 a 2011-06-30_

## Decisão recomendada

**Variante: Grupo 1**
**Confiança: alta**

Grupo 1 tem a maior margem de lucro observada e a diferença é estatisticamente significativa (Kruskal-Wallis, p=0.0).

## Métricas por variante

| Variante | Compradores | Vendas Totais (R$) | Comissão (R$) | Cashback (R$) | Lucro (R$) | Margem de Lucro (%) | Taxa Cashback/Comissão (%) | Ticket Médio (R$) | ROI |
|---|---|---|---|---|---|---|---|---|---|
| Grupo 1 | 7990 | 4,093,818.00 | 450,321.00 | 163,751.00 | 286,570.00 | 7.00 | 36.4 | 512.37 | 1.75 |
| Grupo 2 | 5452 | 2,863,019.00 | 314,935.00 | 171,778.00 | 143,157.00 | 5.00 | 54.5 | 525.13 | 0.83 |
| Grupo 3 | 5029 | 2,629,963.00 | 289,290.00 | 236,697.00 | 52,593.00 | 2.00 | 81.8 | 522.96 | 0.22 |

## Alertas de qualidade de dados

Nenhuma instabilidade detectada na definição das variantes ao longo do período.


## Essa diferença é real ou é ruído?

**O tráfego foi dividido de forma parecida entre as variantes?** ⚠️ diferença significativa — verificar alocação de tráfego (p<0.001). Isso é só uma checagem de sanidade — se der diferente aqui, pode ser sinal de problema na randomização do teste, não uma informação sobre qual variante é melhor.

**A diferença de margem entre as variantes é real ou é sorte?** ✅ **Sim** — a diferença de margem entre as variantes é real, não é coincidência (p<0.001). O tamanho dessa diferença é **grande**.

_Detalhe técnico: teste Kruskal-Wallis (escolhido automaticamente conforme a distribuição dos dados), estatística=161.7829, epsilon²=0.8877._

**Quais variantes diferem entre si de fato (teste post-hoc Tukey HSD):**
- Grupo 1 vs Grupo 2 (p<0.001)
- Grupo 1 vs Grupo 3 (p<0.001)
- Grupo 2 vs Grupo 3 (p<0.001)
