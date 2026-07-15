import csv
import importlib.util
import os
import re
from datetime import datetime
from pathlib import Path


COLUNAS_RESUMO = [
    "nome_teste",
    "parceiro",
    "status",
    "melhor_grupo",
    "margem",
    "decisao",
    "confianca",
    "significancia",
    "variantes",
    "data_inicio",
    "data_fim",
    "teste_estatistico",
    "p_valor",
    "relatorio",
    "data_registro",
]

# Raiz do projeto (pasta pai de scripts/), calculada a partir da localização
# deste arquivo — não do diretório de onde o comando é executado. Assim o
# config.py é encontrado independente de onde/como a pessoa roda o script.
_RAIZ_PROJETO = Path(__file__).resolve().parent.parent


def _carregar_config():
    """
    Carrega config.py a partir do caminho absoluto na raiz do projeto, em vez
    de usar "import config" (que só encontraria o arquivo se ele estivesse na
    mesma pasta do script chamado, ou no diretório atual — o que não é
    garantido dependendo de como a pessoa roda o comando). Retorna None se o
    arquivo não existir.
    """

    caminho_config = _RAIZ_PROJETO / "config.py"

    if not caminho_config.exists():
        return None

    spec = importlib.util.spec_from_file_location("config", caminho_config)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config


def _ler_configuracao():
    """
    Lê a configuração do Google Sheets a partir de config.py (arquivo simples,
    sem terminal/variável de ambiente — pensado para quem não programa).
    Se config.py não existir ou os campos estiverem vazios, cai para
    variáveis de ambiente como alternativa avançada, e por fim para None.
    """

    config = _carregar_config()

    if config is not None:
        planilha_id = getattr(config, "GOOGLE_SHEETS_ID", "").strip()
        credenciais = getattr(config, "GOOGLE_SHEETS_CREDENTIALS", "credentials.json").strip()
    else:
        planilha_id = ""
        credenciais = "credentials.json"

    # Variável de ambiente sobrescreve o config.py, para quem preferir usar assim
    planilha_id = os.environ.get("GOOGLE_SHEETS_ID", planilha_id)
    credenciais = os.environ.get("GOOGLE_SHEETS_CREDENTIALS", credenciais)

    return planilha_id or None, credenciais


def _slug(texto):
    """Transforma 'Parceiro A' em 'parceiro_a' (mesma lógica do relatorio.py)."""
    texto = texto.lower().strip()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")


def _status_e_decisao(decisao, variante_recomendada):
    """
    Traduz a confiança calculada em analisar.py (decidir_variante) para uma
    decisão operacional legível e um status em formato semáforo — pensado
    para alguém do time de growth escanear a planilha rapidamente.
    """

    confianca = decisao["confianca"]

    if confianca == "alta":
        return (
            "✅ Escalar",
            f"Escalar {variante_recomendada} para 100% do tráfego",
        )

    if confianca == "baixa":
        return (
            "⚠️ Revisar",
            f"Não escalar ainda — {variante_recomendada} lidera, mas com "
            "instabilidade detectada na % de cashback; isolar sub-períodos "
            "antes de decidir",
        )

    return (
        "❌ Não escalar",
        "Não escalar nenhuma variante — sem significância estatística suficiente",
    )


def _construir_linha_resumo(parceiro, decisao, metricas, estatistica, data_inicio, data_fim):
    """
    Monta a linha que vai para a planilha de acompanhamento. Colunas curtas e
    estruturadas (uma métrica por célula) em vez de texto corrido — assim dá
    para filtrar, ordenar e montar gráfico a partir da própria planilha. O
    detalhe completo por trás de cada número já está no relatório em reports/.
    """

    ranking = metricas.sort_values(by="margem_lucro", ascending=False)
    melhor_grupo = ranking.index[0]
    melhor_margem = ranking.iloc[0]["margem_lucro"]

    teste_decisao = estatistica.get("teste_decisao") or {}
    nome_teste_stat = teste_decisao.get("teste", "N/D")
    p_valor = teste_decisao.get("p_valor")
    significativo = teste_decisao.get("significativo")

    if p_valor is not None:
        p_texto = "p<0.001" if p_valor < 0.001 else f"p={p_valor:.3f}"
    else:
        p_texto = "N/D"

    significancia_texto = (
        "Significativo" if significativo else "Não significativo"
    )

    variante_recomendada = decisao["variante"] or melhor_grupo
    status, decisao_texto = _status_e_decisao(decisao, variante_recomendada)

    sinal = "+" if melhor_margem >= 0 else ""

    return {
        "nome_teste": f"Teste A/B Cashback — {parceiro}",
        "parceiro": parceiro,
        "variantes": len(metricas),
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "melhor_grupo": melhor_grupo,
        "margem": f"{sinal}{melhor_margem:.1f}%",
        "teste_estatistico": nome_teste_stat,
        "p_valor": p_texto,
        "significancia": significancia_texto,
        "confianca": decisao["confianca"],
        "decisao": decisao_texto,
        "status": status,
        "relatorio": f"reports/relatorio_{_slug(parceiro)}.md",
        "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def _atualizar_csv(linha, caminho_csv):
    """
    Grava a linha no CSV de acompanhamento. Se já existir uma linha para o
    mesmo teste (mesmo "nome_teste"), ela é substituída em vez de duplicada —
    rodar o mesmo dataset de novo atualiza o registro existente, não empilha
    uma cópia nova a cada execução.
    """

    caminho_csv = Path(caminho_csv)
    caminho_csv.parent.mkdir(parents=True, exist_ok=True)

    linhas_existentes = []
    if caminho_csv.exists() and caminho_csv.stat().st_size > 0:
        with open(caminho_csv, mode="r", newline="", encoding="utf-8") as f:
            leitor = csv.DictReader(f)
            for row in leitor:
                if row.get("nome_teste") == linha["nome_teste"]:
                    continue
                # Normaliza linhas de execuções antigas para o schema atual:
                # descarta colunas que não existem mais e preenche com vazio
                # as colunas novas que essa linha antiga não tinha. Sem isso,
                # o DictWriter quebra ao encontrar uma coluna desconhecida
                # (ex: "descricao"/"resultado" de uma versão anterior deste
                # script, antes de virar colunas estruturadas).
                linhas_existentes.append(
                    {coluna: row.get(coluna, "") for coluna in COLUNAS_RESUMO}
                )

    linhas_existentes.append(linha)

    with open(caminho_csv, mode="w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS_RESUMO)
        escritor.writeheader()
        escritor.writerows(linhas_existentes)

    print(f"✅ Resumo registrado em: {caminho_csv}")


def _atualizar_google_sheets(linha, planilha_id, caminho_credenciais, aba="Testes"):
    """
    Escreve/atualiza a linha diretamente no Google Sheets (cenário ideal,
    diferencial do teste). Requer:
      pip install gspread google-auth
    e o arquivo de credenciais indicado em config.py (GOOGLE_SHEETS_CREDENTIALS).

    Se já existir uma linha para o mesmo teste, ela é atualizada em vez de
    duplicada. Se qualquer coisa faltar (biblioteca, credencial, planilha),
    levanta exceção — quem chama decide se isso é fatal ou só um aviso.
    """

    import gspread
    from google.oauth2.service_account import Credentials

    if not Path(caminho_credenciais).exists():
        raise FileNotFoundError(
            f"Arquivo de credenciais não encontrado em '{caminho_credenciais}'. "
            "Veja config_exemplo.py para instruções de como configurar."
        )

    escopos = ["https://www.googleapis.com/auth/spreadsheets"]
    credenciais = Credentials.from_service_account_file(caminho_credenciais, scopes=escopos)
    cliente = gspread.authorize(credenciais)

    planilha = cliente.open_by_key(planilha_id)

    try:
        pagina = planilha.worksheet(aba)
    except gspread.exceptions.WorksheetNotFound:
        pagina = planilha.add_worksheet(title=aba, rows=1000, cols=len(COLUNAS_RESUMO))
        pagina.append_row(COLUNAS_RESUMO)

    valores = pagina.get_all_values()
    linha_existente = None

    for indice, row in enumerate(valores[1:], start=2):  # pula cabeçalho
        if row and row[0] == linha["nome_teste"]:
            linha_existente = indice
            break

    nova_linha = [str(linha[coluna]) for coluna in COLUNAS_RESUMO]

    if linha_existente:
        pagina.update(f"A{linha_existente}", [nova_linha])
    else:
        pagina.append_row(nova_linha)

    print(f"✅ Resumo também registrado no Google Sheets (aba '{aba}').")


def atualizar_resumo(
    parceiro,
    decisao,
    metricas,
    estatistica,
    data_inicio,
    data_fim,
    pasta_saida="outputs",
):
    """
    Registra o teste analisado no resumo de acompanhamento.
    Sempre grava em CSV (mínimo exigido). Se config.py tiver o
    GOOGLE_SHEETS_ID preenchido (ver config_exemplo.py), também tenta
    escrever direto no Google Sheets (diferencial) — sem quebrar o
    pipeline se falhar. Reruns do mesmo teste atualizam a linha existente
    em vez de duplicar.
    """

    linha = _construir_linha_resumo(
        parceiro, decisao, metricas, estatistica, data_inicio, data_fim
    )

    caminho_csv = Path(pasta_saida) / "acompanhamento_testes.csv"
    _atualizar_csv(linha, caminho_csv)

    planilha_id, caminho_credenciais = _ler_configuracao()

    if not planilha_id:
        print(
            "ℹ️  Google Sheets não configurado (veja config_exemplo.py) — "
            "o CSV acima já cobre o mínimo exigido."
        )
        return

    try:
        _atualizar_google_sheets(linha, planilha_id, caminho_credenciais)
    except ModuleNotFoundError:
        print(
            "⚠️  Biblioteca 'gspread' não instalada — pulando Google Sheets. "
            "Rode: pip install gspread google-auth"
        )
    except Exception as erro:
        print(f"⚠️  Não foi possível escrever no Google Sheets: {erro}")