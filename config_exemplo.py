# Configuração da integração com Google Sheets (opcional)
#
# Como usar:
# 1. Copie este arquivo e renomeie a cópia para "config.py" (na mesma pasta)
# 2. Cole o ID da sua planilha entre as aspas abaixo
#    (o ID é o trecho da URL entre "/d/" e "/edit", ex:
#     https://docs.google.com/spreadsheets/d/AQUI_ESTA_O_ID/edit)
# 3. Salve o arquivo
#
# Se você não preencher isso, a solução funciona normalmente e registra
# os testes só no CSV local (outputs/acompanhamento_testes.csv).

GOOGLE_SHEETS_ID = ""

# Caminho do arquivo de credenciais da service account (só mexa nisso se
# tiver colocado o arquivo de credenciais em outro lugar/nome).
GOOGLE_SHEETS_CREDENTIALS = "credentials.json"