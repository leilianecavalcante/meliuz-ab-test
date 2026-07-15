# Relatório de Teste A/B — Parceiro A

_Gerado em 2026-07-15 00:42_

_Período analisado: 2011-01-01 a 2011-04-02_

## Decisão recomendada

**Variante: Grupo 1**
**Confiança: baixa**

Grupo 1 tem a maior margem observada, mas a % de cashback desse grupo não foi estável durante o teste (ver alerta de instabilidade). Recomenda-se isolar sub-períodos antes de escalar.

## Métricas por variante

| Variante | Compradores | Vendas Totais (R$) | Comissão (R$) | Cashback (R$) | Lucro (R$) | Margem de Lucro (%) | Taxa Cashback/Comissão (%) | Ticket Médio (R$) | ROI |
|---|---|---|---|---|---|---|---|---|---|
| Grupo 1 | 9633 | 5,605,173.00 | 638,135.00 | 233,424.00 | 404,711.00 | 7.22 | 36.6 | 581.87 | 1.73 |
| Grupo 2 | 10814 | 6,423,096.00 | 728,178.00 | 370,659.00 | 357,519.00 | 5.57 | 50.9 | 593.96 | 0.96 |
| Grupo 3 | 11410 | 6,785,856.00 | 767,887.00 | 503,600.00 | 264,287.00 | 3.89 | 65.6 | 594.73 | 0.52 |

## Alertas de qualidade de dados

⚠️ **A % de cashback de uma ou mais variantes não se manteve constante durante o teste.** Isso pode indicar uma mudança de configuração no meio do período, contaminando a comparação entre grupos. Recomenda-se isolar sub-períodos antes de confiar totalmente no resultado.

- **Grupo 1** — variação de 20.3 pontos percentuais na taxa de cashback/comissão (2011-01: 27.7%, 2011-02: 31.3%, 2011-03: 48.0%, 2011-04: 45.5%)
- **Grupo 3** — variação de 27.3 pontos percentuais na taxa de cashback/comissão (2011-01: 72.4%, 2011-02: 65.8%, 2011-03: 45.1%, 2011-04: 45.4%)

## Essa diferença é real ou é ruído?

**O tráfego foi dividido de forma parecida entre as variantes?** ✅ tráfego comparável entre grupos (p=0.096). Isso é só uma checagem de sanidade — se der diferente aqui, pode ser sinal de problema na randomização do teste, não uma informação sobre qual variante é melhor.

**A diferença de margem entre as variantes é real ou é sorte?** ✅ **Sim** — a diferença de margem entre as variantes é real, não é coincidência (p<0.001). O tamanho dessa diferença é **grande**.

_Detalhe técnico: teste Kruskal-Wallis (escolhido automaticamente conforme a distribuição dos dados), estatística=128.0427, epsilon²=0.4617._

**Quais variantes diferem entre si de fato (teste post-hoc Tukey HSD):**
- Grupo 1 vs Grupo 2 (p<0.001)
- Grupo 1 vs Grupo 3 (p<0.001)
- Grupo 2 vs Grupo 3 (p<0.001)
