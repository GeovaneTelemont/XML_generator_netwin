from constants import COLUNAS_OBRIGATORIAS, PROGRESS_LOCK, MENSSAGE_QUEUE, PROGRESS_DATA
import pandas as pd
import numpy as np
import os
from datetime import datetime
from settings import Config

def processar_enderecos_otimizado(df_enderecos, df_roteiro_aparecida, df_roteiro_goiania):
    """
    Processa os dados de endereços de forma otimizada mantendo TODOS os dados originais
    """
    
    # Fazer uma cópia do dataframe
    df = df_enderecos.copy()
    
    print(f"🔍 Colunas iniciais: {list(df.columns)}")
    print(f"📊 Total de linhas inicial: {len(df)}")
    
    # ========== CORREÇÕES DE FORMATAÇÃO OTIMIZADAS ==========
    
    print("🔧 Aplicando correções de formatação...")
    
    # 1. Corrigir CEP - operações vetorizadas
    if 'CEP' in df.columns:
        df['CEP'] = (df['CEP'].astype(str)
                      .str.strip()
                      .str.replace(r'\D', '', regex=True)
                      .str[:8]
                      .apply(lambda x: x.zfill(8) if x != '' else ''))
        print("✅ CEP formatado")
    
    # 2. Corrigir COD_LOGRADOURO - operações vetorizadas
    if 'COD_LOGRADOURO' in df.columns:
        df['COD_LOGRADOURO'] = (df['COD_LOGRADOURO'].astype(str)
                                 .str.strip()
                                 .str.replace(r'\D', '', regex=True)
                                 .str[:10])
        print("✅ COD_LOGRADOURO formatado")
    
    # ========== CRIAÇÃO DE COLUNAS OTIMIZADAS ==========
    
    print("Criando CHAVE LOG...")
    # CHAVE LOG otimizada - evita apply
    colunas_chave = ['ESTACAO_ABASTECEDORA', 'LOCALIDADE', 'LOGRADOURO', 'COMPLEMENTO', 'COMPLEMENTO2']
    for coluna in colunas_chave:
        if coluna in df.columns:
            df[coluna] = df[coluna].fillna('').astype(str).str.strip()
    
    # Cria CHAVE LOG de forma vetorizada
    df['CHAVE_LOG'] = (df['ESTACAO_ABASTECEDORA'] + "-" + 
                      df['LOCALIDADE'] + "-" + 
                      df['LOGRADOURO'] + "-" + 
                      df['COMPLEMENTO'] + "-" + 
                      df['COMPLEMENTO2'])
    
    # Remove hífens extras
    df['CHAVE_LOG'] = df['CHAVE_LOG'].str.replace(r'-+', '-', regex=True).str.strip('-')
    
    print("Processando COMPLEMENTO3...")
    # COMPLEMENTO3 otimizado - MANTÉM OS DADOS ORIGINAIS
    if 'COMPLEMENTO3' in df.columns:
        # Salva o original
        df['COMPLEMENTO3_ORIGINAL'] = df['COMPLEMENTO3']
        # Cria versão tratada para processamento
        df['COMPLEMENTO3_TRATADO'] = df['COMPLEMENTO3'].fillna('').astype(str).str.strip().str.upper()
    else:
        df['COMPLEMENTO3_ORIGINAL'] = ''
        df['COMPLEMENTO3_TRATADO'] = ''
    
    # Extrai prefixo de forma vetorizada (usa o tratado)
    df['Prefixo'] = df['COMPLEMENTO3_TRATADO'].str[:2]
    
    print("Agrupando e numerando...")
    # Filtra e agrupa de forma mais eficiente - MAS MANTÉM TODAS AS LINHAS
    mask_prefixo_valido = (df['Prefixo'].notna()) & (df['Prefixo'] != "")
    df_com_prefixo = df[mask_prefixo_valido].copy()
    df_sem_prefixo = df[~mask_prefixo_valido].copy()
    
    # Aplica agrupamento apenas se houver dados
    if len(df_com_prefixo) > 0:
        df_com_prefixo['ORDEM'] = df_com_prefixo.groupby(['CHAVE_LOG', 'Prefixo']).cumcount() + 1
        df_com_prefixo['Resultado'] = df_com_prefixo['Prefixo'] + " " + df_com_prefixo['ORDEM'].astype(str)
        df_com_prefixo = df_com_prefixo.drop('Prefixo', axis=1)
    else:
        df_com_prefixo['ORDEM'] = 0
        df_com_prefixo['Resultado'] = ""
    
    # Prepara dados sem prefixo - MANTÉM TODOS OS DADOS ORIGINAIS
    df_sem_prefixo['ORDEM'] = 0
    df_sem_prefixo['Resultado'] = ""
    if 'Prefixo' in df_sem_prefixo.columns:
        df_sem_prefixo = df_sem_prefixo.drop('Prefixo', axis=1)
    
    # Combina os dataframes - AGORA COM TODAS AS LINHAS
    df = pd.concat([df_com_prefixo, df_sem_prefixo], ignore_index=True)
    
    print(f"📊 Linhas com prefixo válido: {len(df_com_prefixo)}")
    print(f"📊 Linhas sem prefixo válido: {len(df_sem_prefixo)}")
    print(f"📊 Total após concatenação: {len(df)}")
    
    # ========== TRANSFORMAÇÕES RÁPIDAS ==========
    
    print("Aplicando transformações rápidas...")
    
    # COD_ZONA otimizado
    if 'CELULA' in df.columns:
        df['Nº CELULA'] = df['CELULA'].str.split(' ').str[0].fillna('')
    else:
        df['Nº CELULA'] = ''
    
    df['COD_ZONA'] = (df['UF'] + "-" + df['LOCALIDADE_ABREV'] + "-" + 
                     df['ESTACAO_ABASTECEDORA'] + "-CEOS-" + df['Nº CELULA'])
    
    # RESULTADO e COMPARATIVO otimizados
    df['RESULTADO'] = df['Resultado'].str.replace(' ', '')
    
    # COMPARATIVO usa o COMPLEMENTO3 original
    df['COMPARATIVO'] = np.where(df['RESULTADO'] == df['COMPLEMENTO3_TRATADO'], "VERDADEIRO", "FALSO")
    
    # Remove coluna temporária
    if 'Nº CELULA' in df.columns:
        df = df.drop('Nº CELULA', axis=1)
    
    # ========== MERGE OTIMIZADO E CORRIGIDO ==========
    
    print("Fazendo merge com roteiros...")
    df_roteiros = pd.concat([df_roteiro_aparecida, df_roteiro_goiania], ignore_index=True)
    
    # Prepara colunas para merge - CORREÇÃO DO ERRO
    if 'id' in df_roteiros.columns:
        df_roteiros['id'] = df_roteiros['id'].astype(str).str.replace(r'\.0$', '', regex=True)
    if 'id_localidade' in df_roteiros.columns:
        df_roteiros['id_localidade'] = df_roteiros['id_localidade'].astype(str).str.replace(r'\.0$', '', regex=True)
    
    # CORREÇÃO: Converter cod_lograd para string para compatibilidade com COD_LOGRADOURO
    if 'cod_lograd' in df_roteiros.columns:
        df_roteiros['cod_lograd'] = df_roteiros['cod_lograd'].astype(str).str.strip()
        df_roteiros['cod_lograd'] = df_roteiros['cod_lograd'].str.replace(r'\D', '', regex=True)
        df_roteiros['cod_lograd'] = df_roteiros['cod_lograd'].str[:10]  # Garante 10 dígitos
    
    # Faz merge apenas se as colunas existem
    if 'COD_LOGRADOURO' in df.columns and 'cod_lograd' in df_roteiros.columns:
        # Garantir que ambas as colunas são strings
        df['COD_LOGRADOURO'] = df['COD_LOGRADOURO'].astype(str)
        df_roteiros['cod_lograd'] = df_roteiros['cod_lograd'].astype(str)
        
        df = df.merge(
            df_roteiros[['cod_lograd', 'id', 'id_localidade']],
            left_on='COD_LOGRADOURO',
            right_on='cod_lograd',
            how='left'
        )
        df = df.rename(columns={'id': 'ID_ROTEIRO', 'id_localidade': 'ID_LOCALIDADE'})
        if 'cod_lograd' in df.columns:
            df = df.drop('cod_lograd', axis=1)
        print("✅ Merge com roteiros concluído")
    else:
        df['ID_ROTEIRO'] = ''
        df['ID_LOCALIDADE'] = ''
        print("⚠️  Merge não realizado - colunas de junção não encontradas")
    
    # ========== REMOVE DUPLICATAS ==========
    
    if 'COD_SURVEY' in df.columns:
        antes = len(df)
        df = df.drop_duplicates(subset=['COD_SURVEY'])
        depois = len(df)
        print(f"📊 Duplicatas removidas: {antes - depois}")
    
    # ========== COLUNAS NUMÉRICAS ==========
    
    print("Processando colunas numéricas...")
    # Extrai números do COMPLEMENTO3 tratado
    df['NUM_ARGUMENTO3_COMPLEMENTO3'] = (df['COMPLEMENTO3_TRATADO']
                                       .str.extract(r'(\d+)')[0]
                                       .fillna(0)
                                       .astype(int))
    
    df['ORDEM'] = df['ORDEM'].astype(int)
    
    # ========== VALIDAÇÃO SIMPLIFICADA ==========
    
    print("Criando validação...")
    conditions = [
        df['ORDEM'] == 0,
        df['NUM_ARGUMENTO3_COMPLEMENTO3'] == 0,
        df['NUM_ARGUMENTO3_COMPLEMENTO3'] > 10,
        df['ORDEM'] > 10
    ]
    
    choices = [
        "SEM PREFIXO VÁLIDO",
        "VERIFICAR COMPLEMENTO3-VAZIO",
        "VERIFICAR COMPLEMENTO3 >10", 
        "VERIFICAR RESULTADO >10"
    ]
    
    df['VALIDACAO'] = np.select(conditions, choices, default="OK")
    
    # ========== GARANTIR ESTRUTURA FINAL ==========
    
    print("Finalizando estrutura...")
    
    # RESTAURA O COMPLEMENTO3 ORIGINAL
    df['COMPLEMENTO3'] = df['COMPLEMENTO3_ORIGINAL']
    
    colunas_finais = [
        'CHAVE_LOG', 'CELULA', 'ESTACAO_ABASTECEDORA', 'UF', 'MUNICIPIO', 'LOCALIDADE', 
        'COD_LOCALIDADE', 'LOCALIDADE_ABREV', 'LOGRADOURO', 'COD_LOGRADOURO', 'NUM_FACHADA', 
        'COMPLEMENTO', 'COMPLEMENTO2', 'COMPLEMENTO3', 'CEP', 'BAIRRO', 'COD_SURVEY', 
        'QUANTIDADE_UMS', 'COD_VIABILIDADE', 'TIPO_VIABILIDADE', 'TIPO_REDE', 'UCS_RESIDENCIAIS', 
        'UCS_COMERCIAIS', 'NOME_CDO', 'ID_ENDERECO', 'LATITUDE', 'LONGITUDE', 'TIPO_SURVEY', 
        'REDE_INTERNA', 'UMS_CERTIFICADAS', 'REDE_EDIF_CERT', 'DISP_COMERCIAL', 'ESTADO_CONTROLE', 
        'DATA_ESTADO_CONTROLE', 'ID_CELULA', 'QUANTIDADE_HCS', 'ID_ROTEIRO', 'ID_LOCALIDADE', 
        'COD_ZONA', 'ORDEM', 'RESULTADO', 'COMPARATIVO', 'NUM_ARGUMENTO3_COMPLEMENTO3', 'VALIDACAO'
    ]
    
    # Adiciona colunas faltantes
    for coluna in colunas_finais:
        if coluna not in df.columns:
            df[coluna] = ''
    
    # Reordena colunas
    df = df[colunas_finais]
    
    # Remove colunas auxiliares
    colunas_para_remover = ['COMPLEMENTO3_ORIGINAL', 'COMPLEMENTO3_TRATADO', 'Resultado']
    for coluna in colunas_para_remover:
        if coluna in df.columns:
            df = df.drop(coluna, axis=1)
    
    # ========== PREPARAÇÃO PARA POWER QUERY (RÁPIDA) ==========
    
    print("Preparando para Power Query...")
    
    # Apenas as correções essenciais para Power Query
    df = df.replace({
        'NaN': '',
        'nan': '',
        'None': '',
        'null': '',
        'True': 'VERDADEIRO',
        'False': 'FALSO'
    })
    
    # Remove valores nulos
    df = df.fillna('')
    
    print(f"✅ Processamento concluído. Linhas: {len(df):,}")
    
    # Verificar estatísticas dos dados
    print(f"\n📈 ESTATÍSTICAS DOS DADOS:")
    print(f"   - Total de linhas: {len(df):,}")
    print(f"   - COMPLEMENTO3 vazios: {(df['COMPLEMENTO3'] == '').sum():,}")
    print(f"   - COMPLEMENTO2 vazios: {(df['COMPLEMENTO2'] == '').sum():,}")
    print(f"   - Linhas com validação OK: {(df['VALIDACAO'] == 'OK').sum():,}")
    print(f"   - Linhas sem prefixo válido: {(df['VALIDACAO'] == 'SEM PREFIXO VÁLIDO').sum():,}")
    
    return df


def validar_colunas_csv(arquivo_path):
    """Valida se o arquivo CSV contém todas as colunas obrigatórias"""
    try:
        # Tenta ler apenas o cabeçalho do CSV
        with open(arquivo_path, 'r', encoding='latin-1') as f:
            primeira_linha = f.readline().strip()
        
        # Verifica o separador (| ou ;)
        if '|' in primeira_linha:
            separador = '|'
        elif ';' in primeira_linha:
            separador = ';'
        else:
            separador = ','  # fallback
        
        # Lê apenas o cabeçalho
        df_header = pd.read_csv(arquivo_path, encoding='latin-1', sep=separador, nrows=0)
        colunas_encontradas = set(df_header.columns.str.strip().str.upper())
        colunas_obrigatorias_set = set([coluna.upper() for coluna in COLUNAS_OBRIGATORIAS])
        
        # Verifica colunas faltantes
        colunas_faltantes = colunas_obrigatorias_set - colunas_encontradas
        
        # Verifica se há colunas extras (opcional, apenas para informação)
        colunas_extras = colunas_encontradas - colunas_obrigatorias_set
        
        return {
            'valido': len(colunas_faltantes) == 0,
            'colunas_faltantes': list(colunas_faltantes),
            'colunas_extras': list(colunas_extras),
            'total_colunas': len(df_header.columns),
            'colunas_encontradas': list(colunas_encontradas)
        }
        
    except Exception as e:
        return {
            'valido': False,
            'erro': str(e),
            'colunas_faltantes': COLUNAS_OBRIGATORIAS,
            'colunas_extras': [],
            'total_colunas': 0,
            'colunas_encontradas': []
        }
    

def update_progress(message, progress=None, current=None, total=None, status=None):
    """Atualiza os dados de progresso e envia para a fila"""
    global progress_data
    with PROGRESS_LOCK:
        if message:
            PROGRESS_DATA['message'] = message
        if progress is not None:
            PROGRESS_DATA['progress'] = progress
        if current is not None:
            PROGRESS_DATA['current'] = current
        if total is not None:
            PROGRESS_DATA['total'] = total
        if status:
            PROGRESS_DATA['status'] = status
        
        # Envia cópia dos dados para a fila
        MENSSAGE_QUEUE.put(PROGRESS_DATA.copy())


def processar_csv_conversor(arquivo_path):
    """Processa o arquivo CSV para conversão"""
    config = Config()

    try:
        print(f"📂 Carregando {arquivo_path}...")
        
        # Carrega o CSV
        df_enderecos = pd.read_csv(
            arquivo_path,
            encoding='latin-1',
            sep='|',
            engine='c',
            low_memory=False
        )
        
        print(f"✅ CSV carregado: {len(df_enderecos):,} linhas")
        
        # Carrega os roteiros
        df_roteiro_aparecida, df_roteiro_goiania = carregar_roteiros()
        if df_roteiro_aparecida is None or df_roteiro_goiania is None:
            raise Exception("Erro ao carregar arquivos de roteiro. Verifique se os arquivos estão na pasta 'roteiros'.")
        
        # Processa os dados
        df_final = processar_enderecos_otimizado(df_enderecos, df_roteiro_aparecida, df_roteiro_goiania)
        
        # Gera nome do arquivo
        nome_arquivo = f"Enderecos_Totais_CO_Convertido_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        caminho_arquivo = os.path.join(config.download_folder, nome_arquivo)
        
        # Salva o arquivo
        df_final.to_csv(
            caminho_arquivo,
            index=False,
            encoding='utf-8-sig',
            sep=';',
            quoting=1,
            quotechar='"',
            na_rep=''
        )
        
        print(f"✅ Arquivo convertido salvo: {nome_arquivo}")
        return nome_arquivo, len(df_final)
        
    except Exception as e:
        print(f"❌ Erro no processamento: {e}")
        raise Exception(f"Erro ao processar arquivo: {str(e)}")
    

def processar_csv_conversor_grande(arquivo_path):
    """Processa o arquivo CSV para conversão - OTIMIZADO PARA ARQUIVOS GRANDES"""
    config = Config()
    try:
        update_progress("📂 Iniciando carregamento do arquivo...", progress=5, status='processing')
        
        # Verificar tamanho do arquivo
        file_size = os.path.getsize(arquivo_path) / (1024 * 1024)  # Tamanho em MB
        update_progress(f"📊 Tamanho do arquivo: {file_size:.2f} MB", progress=10)
        
        # Carrega os roteiros primeiro (uma vez só)
        update_progress("📁 Carregando arquivos de roteiro...", progress=15)
        df_roteiro_aparecida, df_roteiro_goiania = carregar_roteiros()
        if df_roteiro_aparecida is None or df_roteiro_goiania is None:
            raise Exception("Erro ao carregar arquivos de roteiro. Verifique se os arquivos estão na pasta 'roteiros'.")
        
        update_progress("✅ Roteiros carregados com sucesso", progress=20)

        # Processamento em chunks para arquivos grandes
        chunk_size = 50000  # Ajuste conforme a memória disponível
        chunks_processed = 0
        total_rows = 0
        
        # Primeiro passagem: contar linhas totais
        update_progress("🔢 Contando linhas totais...", progress=25)
        with open(arquivo_path, 'r', encoding='latin-1') as f:
            total_rows = sum(1 for line in f) - 1  # -1 para o cabeçalho
        
        update_progress(f"📊 Total de linhas encontradas: {total_rows:,}", progress=30, total=total_rows)
        
        # Lista para armazenar chunks processados
        chunks_processados = []
        
        # Processar em chunks
        update_progress("🔄 Iniciando processamento em chunks...", progress=35)
        
        for chunk_number, chunk in enumerate(pd.read_csv(arquivo_path, 
                                encoding='latin-1',
                                sep='|',
                                chunksize=chunk_size,
                                low_memory=False), 1):
            
            chunks_processed += 1
            current_row = chunk_number * chunk_size
            if current_row > total_rows:
                current_row = total_rows
                
            progress_percent = 35 + (chunk_number * 55 / (total_rows / chunk_size))
            progress_percent = min(progress_percent, 90)
            
            update_progress(
                f"📦 Processando chunk {chunk_number} ({len(chunk):,} linhas)...", 
                progress=progress_percent,
                current=current_row
            )
            
            # Processa o chunk
            chunk_processado = processar_enderecos_otimizado(chunk, df_roteiro_aparecida, df_roteiro_goiania)
            chunks_processados.append(chunk_processado)
            
            # Limpar memória
            del chunk
            del chunk_processado
            
            update_progress(f"✅ Chunk {chunk_number} processado", progress=progress_percent)
        
        # Combinar todos os chunks
        update_progress("🔗 Combinando chunks processados...", progress=92)
        df_final = pd.concat(chunks_processados, ignore_index=True)
        
        # Gera nome do arquivo
        nome_arquivo = f"Enderecos_Totais_CO_Convertido_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        caminho_arquivo = os.path.join(config.download_folder, nome_arquivo)
        
        # Salva o arquivo em chunks também (para evitar problemas de memória)
        update_progress("💾 Salvando arquivo final...", progress=95)
        df_final.to_csv(
            caminho_arquivo,
            index=False,
            encoding='utf-8-sig',
            sep=';',
            quoting=1,
            quotechar='"',
            na_rep='',
            chunksize=10000  # Salva em chunks também
        )
        
        update_progress(
            f"✅ Conversão concluída! Arquivo salvo: {nome_arquivo}", 
            progress=100, 
            current=total_rows,
            status='completed'
        )
        
        print(f"✅ Arquivo convertido salvo: {nome_arquivo}")
        print(f"📊 Total processado: {len(df_final):,} linhas")
        
        return nome_arquivo, len(df_final)
        
    except Exception as e:
        error_msg = f"❌ Erro no processamento: {str(e)}"
        update_progress(error_msg, status='error')
        print(error_msg)
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        raise Exception(f"Erro ao processar arquivo: {str(e)}")
    
def carregar_roteiros():
    """Carrega os arquivos de roteiro necessários para a conversão"""
    try:
        # Caminho absoluto para a pasta de roteiros
        base_dir = os.path.dirname(os.path.abspath(__file__))
        roteiros_dir = os.path.join(base_dir, 'roteiros')
        
        caminho_aparecida = os.path.join(roteiros_dir, 'roteiro_aparecida.xlsx')
        caminho_goiania = os.path.join(roteiros_dir, 'roteiro_goiania.xlsx')
        
        print(f"📂 Tentando carregar roteiros de:")
        print(f"   - {caminho_aparecida}")
        print(f"   - {caminho_goiania}")
        
        # Verificar se os arquivos existem
        if not os.path.exists(caminho_aparecida):
            print(f"❌ Arquivo não encontrado: {caminho_aparecida}")
            return None, None
        if not os.path.exists(caminho_goiania):
            print(f"❌ Arquivo não encontrado: {caminho_goiania}")
            return None, None
            
        df_roteiro_aparecida = pd.read_excel(caminho_aparecida)
        df_roteiro_goiania = pd.read_excel(caminho_goiania)
        
        print("✅ Roteiros carregados com sucesso")
        print(f"   - Aparecida: {len(df_roteiro_aparecida)} registros")
        print(f"   - Goiania: {len(df_roteiro_goiania)} registros")
        
        return df_roteiro_aparecida, df_roteiro_goiania
        
    except Exception as e:
        print(f"❌ Erro ao carregar roteiros: {e}")
        return None, None
    
