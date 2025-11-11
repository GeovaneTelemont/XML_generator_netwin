import pandas as pd
import os, zipfile, shutil
from datetime import datetime
import xml.etree.ElementTree as ET
from constants import CODIGOS_COMPLEMENTO
from settings import Config

def extrair_numero_argumento(texto):
    """
    Extrai TODO o conteúdo depois das duas primeiras letras
    """
    if pd.isna(texto) or texto == '':
        return '1'
    
    texto_str = str(texto).strip()
    
    if len(texto_str) < 2:
        return '1'
    
    argumento = texto_str[2:].strip()
    
    if argumento == '':
        return '1'
    
    return argumento



def formatar_coordenada(coord):
    """Converte coordenada de formato brasileiro para internacional"""
    if pd.isna(coord):
        return None
    try:
        return float(str(coord).replace(',', '.'))
    except ValueError:
        return None

def obter_codigo_complemento(texto):
    """
    Obtém o código do complemento baseado nas duas primeiras letras do texto
    """
    if pd.isna(texto) or texto == '':
        return '60'  # Default para LT (LOTE)
    
    texto_str = str(texto).strip().upper()
    
    # Pegar as duas primeiras letras
    if len(texto_str) >= 2:
        codigo = texto_str[:2]
        return str(CODIGOS_COMPLEMENTO.get(codigo, 60))  # Default 60 se não encontrar
    else:
        return '60'  # Default para LT (LOTE)


def criar_xml_edificio_ccomplementos(dados_csv, numero_pasta, complemento_vazio):
    edificio = ET.Element('edificio')
    edificio.set('tipo', 'M')
    edificio.set('versao', '7.9.2')
    ET.SubElement(edificio, 'gravado').text = 'false'
    ET.SubElement(edificio, 'nEdificio').text = dados_csv['COD_SURVEY']
    latitude = formatar_coordenada(dados_csv['LATITUDE'])
    longitude = formatar_coordenada(dados_csv['LONGITUDE'])
    ET.SubElement(edificio, 'coordX').text = str(longitude)
    ET.SubElement(edificio, 'coordY').text = str(latitude)
    codigo_zona = str(dados_csv['COD_ZONA']) if 'COD_ZONA' in dados_csv and not pd.isna(dados_csv['COD_ZONA']) else 'DF-GURX-ETGR-CEOS-68'
    ET.SubElement(edificio, 'codigoZona').text = codigo_zona
    ET.SubElement(edificio, 'nomeZona').text = codigo_zona
    localidade = str(dados_csv['LOCALIDADE']) if 'LOCALIDADE' in dados_csv and not pd.isna(dados_csv['LOCALIDADE']) else 'GUARA'
    ET.SubElement(edificio, 'localidade').text = localidade
    endereco = ET.SubElement(edificio, 'enderecoEdificio')
    ET.SubElement(endereco, 'id').text = str(dados_csv['ID_ENDERECO']) if 'ID_ENDERECO' in dados_csv and not pd.isna(dados_csv['ID_ENDERECO']) else '93128133'
    logradouro = str(dados_csv['LOGRADOURO'] +", "+ dados_csv['BAIRRO']+", "+dados_csv['MUNICIPIO']+", "+dados_csv['LOCALIDADE']+" - "+ dados_csv["UF"]+ f" ({dados_csv['COD_LOGRADOURO']})" )
    ET.SubElement(endereco, 'logradouro').text = logradouro
    num_fachada = str(dados_csv['NUM_FACHADA']) if 'NUM_FACHADA' in dados_csv and not pd.isna(dados_csv['NUM_FACHADA']) else 'SN'
    ET.SubElement(endereco, 'numero_fachada').text = num_fachada
    complemento1 = dados_csv['COMPLEMENTO'] if 'COMPLEMENTO' in dados_csv else ''
    codigo_complemento1 = obter_codigo_complemento(complemento1)
    argumento1 = extrair_numero_argumento(complemento1)
    ET.SubElement(endereco, 'id_complemento1').text = codigo_complemento1
    ET.SubElement(endereco, 'argumento1').text = argumento1
    complemento2 = dados_csv['COMPLEMENTO2'] if 'COMPLEMENTO2' in dados_csv else ''
    codigo_complemento2 = obter_codigo_complemento(complemento2)
    argumento2 = extrair_numero_argumento(complemento2)
    ET.SubElement(endereco, 'id_complemento2').text = codigo_complemento2
    ET.SubElement(endereco, 'argumento2').text = argumento2

    # Só adiciona complemento3 se não estiver vazio
    if complemento_vazio == False:
        complemento3 = dados_csv['RESULTADO'] if 'RESULTADO' in dados_csv else ''
        if not pd.isna(complemento3) and str(complemento3).strip() != '':
            codigo_complemento3 = obter_codigo_complemento(complemento3)
            argumento3 = extrair_numero_argumento(complemento3)
            ET.SubElement(endereco, 'id_complemento3').text = codigo_complemento3
            ET.SubElement(endereco, 'argumento3').text = argumento3

    cep = str(dados_csv['CEP']) if 'CEP' in dados_csv and not pd.isna(dados_csv['CEP']) else '71065071'
    ET.SubElement(endereco, 'cep').text = cep
    bairro = str(dados_csv['BAIRRO']) if 'BAIRRO' in dados_csv and not pd.isna(dados_csv['BAIRRO']) else localidade
    ET.SubElement(endereco, 'bairro').text = bairro
    ET.SubElement(endereco, 'id_roteiro').text = str(dados_csv['ID_ROTEIRO']) if 'ID_ROTEIRO' in dados_csv and not pd.isna(dados_csv['ID_ROTEIRO']) else '57149008'
    ET.SubElement(endereco, 'id_localidade').text = str(dados_csv['ID_LOCALIDADE']) if 'ID_LOCALIDADE' in dados_csv and not pd.isna(dados_csv['ID_LOCALIDADE']) else '1894644'
    cod_lograd = str(dados_csv['COD_LOGRADOURO']) if 'COD_LOGRADOURO' in dados_csv and not pd.isna(dados_csv['COD_LOGRADOURO']) else '2700035341'
    ET.SubElement(endereco, 'cod_lograd').text = cod_lograd
    tecnico = ET.SubElement(edificio, 'tecnico')
    ET.SubElement(tecnico, 'id').text = '1828772688'
    ET.SubElement(tecnico, 'nome').text = 'NADIA CAROLINE'
    empresa = ET.SubElement(edificio, 'empresa')
    ET.SubElement(empresa, 'id').text = '42541126'
    ET.SubElement(empresa, 'nome').text = 'TELEMONT'
    data_atual = datetime.now().strftime('%Y%m%d%H%M%S')
    ET.SubElement(edificio, 'data').text = data_atual
    total_ucs = int(dados_csv['QUANTIDADE_UMS']) if 'QUANTIDADE_UMS' in dados_csv and not pd.isna(dados_csv['QUANTIDADE_UMS']) else 1
    ET.SubElement(edificio, 'totalUCs').text = str(total_ucs)
    ET.SubElement(edificio, 'ocupacao').text = "EDIFICACAOCOMPLETA"
    ET.SubElement(edificio, 'numPisos').text = '1'
    ET.SubElement(edificio, 'destinacao').text = 'COMERCIO'
    xml_str = ET.tostring(edificio, encoding='UTF-8', method='xml')
    xml_completo = b'<?xml version="1.0" encoding="UTF-8"?>' + xml_str
    return xml_completo 

def processar_csv(arquivo_path):
    global LOG_COMPLEMENTOS
    global ERRO_COMPLEMENTO2
    global ERRO_COMPLEMENTO3
    ERRO_COMPLEMENTO2 = False
    ERRO_COMPLEMENTO3 = False


    try:
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        for encoding in encodings:
            try:
                df = pd.read_csv(arquivo_path, sep=';', encoding=encoding)
                # print(f"Arquivo lido com encoding: {encoding}")
                break 
            except UnicodeDecodeError:
                continue
        else:
            df = pd.read_csv(arquivo_path, sep=';')
    except Exception as e:
        raise Exception(f"Erro ao ler o arquivo CSV: {e}")

    if len(df) == 0:
        raise Exception("O arquivo CSV está vazio")

    estacao = df['ESTACAO_ABASTECEDORA'].iloc[0] if 'ESTACAO_ABASTECEDORA' in df.columns else 'DESCONHECIDA'
    diretorio_principal = f'moradias_xml_{estacao}_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    os.makedirs(diretorio_principal, exist_ok=True)

    pastas_criadas = []
    log_processamento = []

    for i, (index, linha) in enumerate(df.iterrows(), 1):
         # Verifica se a coluna COMPLEMENTO3 e COMPLEMENTO2 estão totalmente vazias
        coluna_complemento_2_vazia = df['COMPLEMENTO3'].isna().all() or (df['COMPLEMENTO3'].astype(str).str.strip() == '').all()
        
        nome_pasta = f'moradia{i}'
        caminho_pasta = os.path.join(diretorio_principal, nome_pasta)
        os.makedirs(caminho_pasta, exist_ok=True)
        pastas_criadas.append(caminho_pasta)

        comp1 = linha['COMPLEMENTO'] if 'COMPLEMENTO' in linha else ''
        comp2 = linha['COMPLEMENTO2'] if 'COMPLEMENTO2' in linha else ''
        resultado = linha['RESULTADO'] if 'RESULTADO' in linha else ''

        xml_content = criar_xml_edificio_ccomplementos(linha, i, coluna_complemento_2_vazia)

        # validação dos complementos
        if comp1 == '' or pd.isna(comp1):
            ERRO_COMPLEMENTO2 = True
            LOG_COMPLEMENTOS = "⚠️(ERRO) no CSV na coluna do [COMPLEMENTO1], existem células que estão vazias. Todas as celulas da coluna COMPLEMENTO2 teve ser preenchidas para gerar o xml com 2 complementos."
        
        elif comp2 == '' or pd.isna(comp2):
            ERRO_COMPLEMENTO2 = True
            LOG_COMPLEMENTOS = "⚠️(ERRO) no CSV na coluna do [COMPLEMENTO2], existem células que estão vazias. Todas as celulas da coluna COMPLEMENTO2 teve ser preenchidas para gerar o xml com 2 complementos."

        elif resultado == '' or pd.isna(resultado):
            ERRO_COMPLEMENTO3 = True
            LOG_COMPLEMENTOS = "⚠️(ERRO) no CSV na coluna do [COMPLEMENTO3], existem células que estão vazias. Todas as celulas da coluna COMPLEMENTO3 teve ser preenchidas para gerar o xml com 3 complementos."
        
        elif coluna_complemento_2_vazia:
            ERRO_COMPLEMENTO3 = False
            ERRO_COMPLEMENTO2 = False
            LOG_COMPLEMENTOS = "✅(XML) com dois complementos gerado com sucesso! Agora é só fazer o download do zip!"
        else:
            ERRO_COMPLEMENTO3 = False
            ERRO_COMPLEMENTO2 = False
            LOG_COMPLEMENTOS = "✅(XML) com três complementos gerado com sucesso! Agora é só fazer o download do zip!"


        caminho_xml = os.path.join(caminho_pasta, f'{nome_pasta}.xml')
        with open(caminho_xml, 'wb') as f:
            f.write(xml_content)

        if i % 10 == 0 or i == 1:
            codigo1 = obter_codigo_complemento(comp1)
            codigo2 = obter_codigo_complemento(comp2)
            arg1 = extrair_numero_argumento(comp1)
            arg2 = extrair_numero_argumento(comp2)
            log_processamento.append(f'Registro {i}:')

            if coluna_complemento_2_vazia:
                log_processamento.append(f'  COMP1("{comp1}" → código:{codigo1} argumento:"{arg1}")')
                log_processamento.append(f'  COMP2("{comp2}" → código:{codigo2} argumento:"{arg2}")')
                log_processamento.append('-' * 50)
                
            else:
                codigo3 = obter_codigo_complemento(resultado)
                arg3 = extrair_numero_argumento(resultado)
                log_processamento.append(f'  COMP1("{comp1}" → código:{codigo1} argumento:"{arg1}")')
                log_processamento.append(f'  COMP2("{comp2}" → código:{codigo2} argumento:"{arg2}")')
                log_processamento.append(f'  COMP3("{resultado}" → código:{codigo3} argumento:"{arg3}")')
                log_processamento.append('-' * 50)
          
    config = Config()
    zip_filename = os.path.join(config.download_folder, f'{diretorio_principal}.zip')
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for pasta in pastas_criadas:
            for root, dirs, files in os.walk(pasta):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, diretorio_principal)
                    zipf.write(file_path, arcname)

    shutil.rmtree(diretorio_principal)
    return os.path.basename(zip_filename), len(df), '\n'.join(log_processamento) 
