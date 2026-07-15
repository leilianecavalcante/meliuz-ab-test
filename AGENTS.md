# AGENTS.md

Contexto para agentes de IA (Claude Code, Cursor, Codex, Gemini CLI, etc.)
trabalhando neste repositório.

## Projeto

Análise de testes A/B de % de cashback para o Méliuz. Recebe um CSV de teste
(qualquer parceiro, qualquer número de variantes) e responde: qual variante
escalar para 100% do tráfego.

## Comando principal

```bash
python scripts/analisar.py <caminho_do_dataset.csv>
```

Rode sempre a partir da raiz do repositório. Esse comando sozinho executa o
pipeline inteiro (limpeza → métricas → estatística → relatório → resumo) e
não precisa de argumentos além do caminho do CSV.

## Quando alguém pedir para "analisar um teste" em linguagem natural

1. Identifique o caminho do CSV (pergunte ou procure em `datasets/` se não
   estiver claro — nunca escolha um arquivo arbitrariamente).
2. Rode `python scripts/analisar.py <caminho>`.
3. Leia a saída e responda em linguagem natural, sempre incluindo o nível de
   confiança da recomendação (`alta`, `baixa` ou `insuficiente`) e o motivo —
   nunca simplifique para "a variante X venceu" quando a confiança não for
   `alta`. Ver `prompts/instrucoes_agente.md` para o roteiro completo de como
   interpretar e responder.

## Estrutura

- `scripts/` — pipeline (`limpeza.py`, `metricas.py`, `estatistica.py`,
  `relatorio.py`, `planilha.py`, orquestrado por `analisar.py`)
- `datasets/` — CSVs de entrada (schema fixo, número de variantes varia)
- `reports/` — relatórios gerados (um `.md` por parceiro)
- `outputs/acompanhamento_testes.csv` — resumo de todos os testes já rodados

## Regras

- Nunca hardcode nomes ou número de variantes (`Grupo 1`, `Grupo 2`...) — a
  solução precisa aceitar qualquer quantidade sem alteração de código.
- Não edite os scripts do pipeline a menos que explicitamente pedido — eles
  já foram revisados e testados nos 3 datasets fornecidos.
- `config.py` (credenciais do Google Sheets) nunca deve ser commitado — está
  no `.gitignore`; use `config_exemplo.py` como referência.
- Ao gerar novo código para este projeto, siga o estilo dos scripts
  existentes: nomes de função/variável em português, docstrings curtas
  explicando o "porquê", mensagens de print com ✅/⚠️/❌ para status.