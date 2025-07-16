# ---------- BIBLIOTECAS ----------
import geopandas as gpd
import pandas as pd
import numpy as np
import os
import logging
import math
from typing import Dict, Any, Optional

# ---------- FUNÇÕES AUXILIARES ----------


def normalizar_potencia_final(pot: float) -> float:
    # Essa função trata valores de potência superiores a 20 e inferiores a 0.1 (Outliers)
    # Ela irá condicionar o valor em uma escala entre 1 e 10
    if pd.isna(pot) or pot == 0:
        return pot

    # Valor dentro do normal, logo permanece o mesmo valor
    if 0.1 <= pot <= 20:
        return pot

    try:
        # Tratamento para valores superiores a 20
        if pot > 20:
            ordem_magnitude = math.floor(math.log10(pot))
            return pot / (10**ordem_magnitude)

        # Tratamento para valores inferior a 0.1
        if 0 < pot < 0.1:
            ordem_magnitude = math.floor(math.log10(pot))
            return pot * (10**(-ordem_magnitude))

    # Em caso de erro, retorna o valor original
    except (ValueError, OverflowError):
        return pot

    return pot

# ---------- FUNÇÃO PRINCIPAL ----------


def process_geodata(raw_data: Dict[str, Any]) -> Optional[gpd.GeoDataFrame]:
    # Essa função realiza o tratamento de valores indesejados, nulos, vazios, caracteres especiais
    # Além disso, retorna o valor de longitude e latitude por meio de uma função dos dados obtidos da ANEEL (Colunas X e Y)
    if not raw_data or 'features' not in raw_data:
        logging.error("Dados brutos são inválidos ou não contêm 'features'.")
        return None

    logging.info("Iniciando processamento dos dados GeoJSON.")
    # Coleta da longitude e latitude por meio de uma função dos dados obtidos da ANEEL (Colunas X e Y)
    gdf = gpd.GeoDataFrame.from_features(raw_data['features'])
    gdf.set_crs(epsg=4326, inplace=True)

    gdf['longitude'] = gdf.geometry.x
    gdf['latitude'] = gdf.geometry.y

    # Tratamento 1: Corrige a localização de usina de aerogeradores
    if 'NOME_EOL' in gdf.columns and 'UF' in gdf.columns:
        logging.info("Aplicando regra de negócio para 'Barra XI'...")
        mascara_barra_xi = gdf['NOME_EOL'].str.contains("Barra XI", na=False)
        gdf.loc[mascara_barra_xi, 'UF'] = 'MG'
        logging.info(
            f"Foram atualizados {mascara_barra_xi.sum()} registros de UF para 'MG' com base na regra.")

    # Tratamento 2: Remove todas as quebras de linhas do dataset (\n)
    logging.info("Removendo quebras de linha de todas as colunas de texto...")
    for col in gdf.select_dtypes(include='object').columns:
        # Substitui \n e \r por um espaço em branco para evitar juntar palavras
        gdf[col] = gdf[col].str.replace(r'\r|\n', ' ', regex=True)

    # Tratamento 3: Remoção das aspas simples e duplas da coluna PROPRIETARIO
    if 'PROPRIETARIO' in gdf.columns:
        logging.info(
            "Limpando aspas simples e duplas da coluna 'PROPRIETARIO'...")
        gdf['PROPRIETARIO'] = gdf['PROPRIETARIO'].astype(
            str).str.replace(r'["\']', '', regex=True)

    # Tratamento 4: Conversão de valores nulos e vazios para remoção posterior
    logging.info("Iniciando limpeza agressiva de valores nulos e vazios...")
    valores_nulos = [None, np.nan, '', ' ', 'null',
                     'Null', 'NULL', 'None', 'NaN', 'NaT']
    gdf.replace(valores_nulos, np.nan, inplace=True)

    # Tratamento 5: Conversão de colunas numéricas e data
    colunas_numericas = ['POT_MW', 'ALT_TOTAL',
                         'ALT_TORRE', 'DIAM_ROTOR', 'X', 'Y', 'OBJECTID']
    for col in [c for c in colunas_numericas if c in gdf.columns]:
        gdf[col] = pd.to_numeric(gdf[col], errors='coerce')
    if 'DATA_ATUALIZACAO' in gdf.columns:
        gdf['DATA_ATUALIZACAO'] = pd.to_datetime(
            gdf['DATA_ATUALIZACAO'], unit='ms', errors='coerce')

    # Tratamento 6: Arrendodar os valores de colunas numéricas
    logging.info("Padronizando valores de ponto flutuante...")
    if 'DIAM_ROTOR' in gdf.columns:
        gdf['DIAM_ROTOR'] = gdf['DIAM_ROTOR'].round(1)
    if 'POT_MW' in gdf.columns:
        gdf['POT_MW'] = gdf['POT_MW'].round(3)
    if 'ALT_TORRE' in gdf.columns:
        gdf['ALT_TORRE'] = gdf['ALT_TORRE'].round(1)
    if 'ALT_TOTAL' in gdf.columns:
        gdf['ALT_TOTAL'] = gdf['ALT_TOTAL'].round(1)

    logging.info(
        "Valores na coluna 'DIAM_ROTOR, POT_MW, POT_MW, ALT_TOTAL' foram arredondados.")

    # Tratamento 7: Tratamento de outliers dos dados de potência
    if 'POT_MW' in gdf.columns:
        logging.info("Aplicando normalização personalizada em 'POT_MW'...")
        gdf['POT_MW'] = pd.to_numeric(gdf['POT_MW'], errors='coerce')
        gdf['POT_MW'] = gdf['POT_MW'].apply(normalizar_potencia_final)

    # Tratamento 8: Substituição de valores 1 por Sim na coluna OPERAÇÃO
    if 'OPERACAO' in gdf.columns:
        logging.info(
            "Padronizando a coluna 'OPERACAO': substituindo '1' por 'Sim'...")
        # Usa np.where para substituir condicionalmente.
        # Primeiro, converte para string para garantir a comparação correta.
        gdf['OPERACAO'] = np.where(gdf['OPERACAO'].astype(
            str).str.strip() == '1', 'Sim', gdf['OPERACAO'])

    # Tratamento 9: Tratamento da Coluna DATUM_EMP para dois casos
    # Essa informação foi coletada do site da ANEEL: https://biblioteca.aneel.gov.br/acervo/detalhe/216018?guid=1752542703285&returnUrl=%2fresultado%2flistar%3fguid%3d1752542703285%26quantidadePaginas%3d1%26codigoRegistro%3d216018%23216018&i=1
    if 'NOME_EOL' in gdf.columns and 'DATUM_EMP' in gdf.columns:
        logging.info(
            "Aplicando regra de negócio para 'DATUM_EMP' em NOME_EOL específicos...")
        # Lista dos nomes dos parques eólicos a serem alterados
        nomes_alvo = ['Pedra de Amolar I', 'Pedra de Amolar II']

        # Cria uma máscara para encontrar as linhas onde NOME_EOL está na lista alvo
        mascara = gdf['NOME_EOL'].isin(nomes_alvo)

        # Usa .loc para atribuir o novo valor de forma segura e eficiente
        gdf.loc[mascara, 'DATUM_EMP'] = 'SIRGAS2000'
        logging.info(
            f"Foram atualizados {mascara.sum()} registros para DATUM_EMP = 'SIRGAS2000'.")

    # Tratamento 10: Remoção de linhas contendo valores ausentes desconsiderando a coluna ORIGEM (Todos os valores são ausentes)
    colunas_para_validar = gdf.columns.tolist()
    if 'ORIGEM' in colunas_para_validar:
        colunas_para_validar.remove('ORIGEM')
    gdf.dropna(subset=colunas_para_validar, inplace=True)

    # Tratamento Finalizado
    logging.info("Processamento de dados concluído.")
    return gdf

# Essa função salva o arquivo tratado no formato CSV


def save_geodata(gdf: gpd.GeoDataFrame, folder: str, filename: str) -> str:

    if gdf is None or gdf.empty:
        logging.warning(
            "O DataFrame está vazio ou nulo. Nenhum arquivo foi salvo.")
        return None

    logging.info(f"Iniciando salvamento do arquivo em '{folder}/{filename}'.")
    os.makedirs(folder, exist_ok=True)

    df_to_save = gdf.drop(columns=['geometry']).copy()

    full_path = os.path.join(folder, filename)
    df_to_save.to_csv(full_path, index=False, encoding='utf-8-sig')
    logging.info(f"Arquivo salvo com sucesso em: {full_path}")
    return full_path
