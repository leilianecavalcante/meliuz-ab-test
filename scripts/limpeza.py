import pandas as pd
import sys


COLUNAS_ESPERADAS = {
    "Data",
    "Grupos de usuários",
    "Parceiro",
    "compradores",
    "comissão",
    "cashback",
    "vendas totais",
}


def carregar_csv(caminho):
    """
    Lê um arquivo CSV e retorna um DataFrame.
    """

    try:
        df = pd.read_csv(caminho)

        print("✅ Arquivo carregado com sucesso!")

        return df

    except FileNotFoundError:
        print("❌ Arquivo não encontrado.")
        sys.exit()

    except Exception as erro:
        print(f"❌ Erro ao ler o arquivo: {erro}")
        sys.exit()


def validar_schema(df):
    """
    Garante que o dataset tem as colunas esperadas antes de processar.
    Falha com mensagem clara em vez de KeyError genérico mais na frente.
    """

    colunas_presentes = set(df.columns)
    faltando = COLUNAS_ESPERADAS - colunas_presentes

    if faltando:
        print(f"❌ Colunas faltando no dataset: {faltando}")
        sys.exit()

    print("✅ Schema validado com sucesso!")


def limpar_valor_monetario(valor):
    """
    Converte valores como:
    R$ 10.273 -> 10273.0
    R$ 1.234,56 -> 1234.56
    """

    if pd.isna(valor):
        return 0.0

    valor = (
        str(valor)
        .replace("R$", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )

    try:
        return float(valor)
    except ValueError:
        return 0.0


def limpar_dados(df):
    """
    Limpa e converte os dados do dataset.
    """

    linhas_antes = len(df)

    # Normalizar colunas de texto (evita quebra silenciosa em groupby
    # por causa de espaços extras, ex: "Grupo 1 " vs "Grupo 1")
    for coluna in ["Grupos de usuários", "Parceiro"]:
        df[coluna] = df[coluna].astype(str).str.strip()

    # Converter data com formato explícito; datas inválidas viram NaT
    df["Data"] = pd.to_datetime(df["Data"], format="%Y-%m-%d", errors="coerce")

    linhas_data_invalida = df["Data"].isna().sum()
    if linhas_data_invalida > 0:
        print(f"⚠️  {linhas_data_invalida} linha(s) descartada(s) por data inválida.")
        df = df.dropna(subset=["Data"])

    # compradores: numérico tolerante a lixo, nunca quebra o pipeline
    compradores_original = df["compradores"].copy()
    df["compradores"] = (
        pd.to_numeric(df["compradores"], errors="coerce").fillna(0).astype(int)
    )
    linhas_compradores_invalidos = (
        pd.to_numeric(compradores_original, errors="coerce").isna().sum()
    )
    if linhas_compradores_invalidos > 0:
        print(
            f"⚠️  {linhas_compradores_invalidos} valor(es) inválido(s) em "
            f"'compradores' foram convertidos para 0."
        )

    # Colunas monetárias
    colunas_monetarias = [
        "comissão",
        "cashback",
        "vendas totais",
    ]

    for coluna in colunas_monetarias:
        df[coluna] = df[coluna].apply(limpar_valor_monetario)

    linhas_depois = len(df)
    print(
        f"✅ Dados limpos com sucesso! ({linhas_depois}/{linhas_antes} linhas mantidas)"
    )

    return df


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python limpeza.py <caminho_do_csv>")
        sys.exit()

    caminho_csv = sys.argv[1]
    df = carregar_csv(caminho_csv)
    validar_schema(df)
    df = limpar_dados(df)
    print(df.head())