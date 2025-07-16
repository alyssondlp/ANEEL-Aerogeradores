# ---------- BIBLIOTECAS ----------
import requests
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# ---------- FUNÇÃO DE QUERY, EXTRAÇÃO, PAGINAÇÃO E AGRUPAMENTO ----------


def extract_aneel_data(url: str) -> Optional[Dict[str, Any]]:
    # Extração de todos os dados de aerogeradores da API ArcGIS da ANEEL
    # É realizada uma paginação devido a uma limitação de 1000 registros por consulta
    # É passado como argumento a URL do site da ANEEL

    all_features = []
    offset = 0
    max_records = 1000

    logging.info(f"Iniciando extração de dados da URL: {url} (com paginação)")

    # Aplicado as condições para a query para coletar todas as colunas do dataset e retornar um arquivo GEOJSON
    while True:
        params = {
            'where': '1=1',
            'outFields': '*',
            'f': 'geojson',
            'resultOffset': offset,          # Define o ponto de partida da página
            'resultRecordCount': max_records  # Define o tamanho da página
        }

        # Tratamento de paginação para coletar todos os registros
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            features = data.get('features', [])
            num_features = len(features)

            if num_features > 0:
                all_features.extend(features)
                logging.info(
                    f"Página obtida com {num_features} registros. Total acumulado: {len(all_features)}")

            # Se a página retornada tiver menos que o máximo, é a última página.
            if num_features < max_records:
                logging.info("Última página de dados alcançada.")
                break

            # Prepara para a próxima página
            offset += max_records

        # Condição de erro
        except requests.exceptions.RequestException as e:
            logging.error(
                f"Falha na extração de dados na página com offset {offset}: {e}")
            return None

    # Finalização e agrupamento de todas as informações coletadas em um arquivo GEOJSON
    if data:
        data['features'] = all_features
        logging.info(
            f"Extração de dados concluída. Total de {len(all_features)} registros obtidos.")
        return data
    else:
        return None
