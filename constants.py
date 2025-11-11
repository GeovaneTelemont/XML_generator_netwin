import os, tempfile, queue, threading


SECRET_KEY='d7b81e4aabb0131e68f8914a6f5f08a94be1b6d0b908e7e8e03c06d6b492b46d'
MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1025 # 2GB max file size
UPLOAD_FOLDER = tempfile.mkdtemp()
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')

CODIGOS_COMPLEMENTO = {
    "AC": 1, "AA": 2, "AF": 3, "AL": 4, "AS": 5, "AB": 6, "AN": 7, "AX": 8,
    "AP": 9, "AZ": 10, "AT": 11, "BS": 12, "BA": 13, "BR": 14, "BC": 15,
    "BL": 16, "BX": 17, "CS": 18, "CM": 20, "CP": 21, "CA": 22, "CE": 23,
    "CT": 24, "CB": 25, "CL": 26, "CD": 27, "CJ": 28, "CR": 29, "CO": 30,
    "DP": 31, "DT": 32, "DV": 34, "ED": 35, "EN": 36, "ES": 37, "EC": 38,
    "ET": 39, "EP": 40, "FO": 42, "FR": 43, "FU": 44, "GL": 45, "GP": 46,
    "GA": 47, "GB": 48, "GJ": 49, "GR": 50, "GH": 52, "HG": 53, "LD": 55,
    "LM": 56, 'LH': 57, "LE": 58, "LJ": 59, "LT": 60, "LO": 61, "M": 62,
    "MT": 63, "MC": 64, "MZ": 65, "MD": 66, "NC": 67, "OM": 68, "OG": 69,
    "PC": 70, "PR": 71, "PP": 72, "PV": 73, "PM": 74, "PS": 75, "PA": 76,
    "PL": 77, "P": 78, "PO": 80, "PT": 81, "PD": 82, "PE": 83, "QU": 85,
    "QT": 86, "KM": 87, "QN": 88, "QQ": 89, "RM": 90, "RP": 91, "RF": 92,
    "RT": 93, "RL": 95, "SL": 96, "SC": 97, "SR": 98, "SB": 100, "SJ": 101,
    "SD": 102, "SU": 103, "SS": 104, "SQ": 105, "TN": 106, "TO": 107,
    "TE": 109, "TV": 110, "TR": 111, "VL": 112, "VZ": 113, "AD": 114,
    "BI": 115, "SA": 116, "NA": 117, "SK": 118, "ND": 119, "SE": 120,
    "AM": 121, "NR": 122, "CH": 124
}

# Colunas obrigatórias para validação
COLUNAS_OBRIGATORIAS = [
    'CELULA', 'ESTACAO_ABASTECEDORA', 'UF', 'MUNICIPIO', 'LOCALIDADE', 
    'COD_LOCALIDADE', 'LOCALIDADE_ABREV', 'LOGRADOURO', 'COD_LOGRADOURO', 
    'NUM_FACHADA', 'COMPLEMENTO', 'COMPLEMENTO2', 'COMPLEMENTO3', 'CEP', 
    'BAIRRO', 'COD_SURVEY', 'QUANTIDADE_UMS', 'COD_VIABILIDADE', 
    'TIPO_VIABILIDADE', 'TIPO_REDE', 'UCS_RESIDENCIAIS', 'UCS_COMERCIAIS', 
    'NOME_CDO', 'ID_ENDERECO', 'LATITUDE', 'LONGITUDE', 'TIPO_SURVEY', 
    'REDE_INTERNA', 'UMS_CERTIFICADAS', 'REDE_EDIF_CERT', 'DISP_COMERCIAL', 
    'ESTADO_CONTROLE', 'DATA_ESTADO_CONTROLE', 'ID_CELULA', 'QUANTIDADE_HCS'
]


LOG_COMPLEMENTOS = ""
ERRO_COMPLEMENTO3 = False
ERRO_COMPLEMENTO2 = False


# Sistema de mensagens para SSE
MENSSAGE_QUEUE = queue.Queue()

# Dicionário global para armazenar resultados (em vez de session)
PROCESSING_RESULTS = {}
RESULTS_LOCK = threading.Lock()
PROGRESS_DATA = {
    'message': '',
    'progress': 0,
    'current': 0,
    'total': 0,
    'filename': '',
    'status': 'waiting'
}
PROGRESS_LOCK = threading.Lock()
