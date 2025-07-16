# ANEEL-Aerogeradores
Utilização de Python, Web Scraping, Tableau, DataViz e Google Apresentações para Data Engineering, Data Visualization e Data Analysis em um dataset de aerogeradores do ArcGIS do SIGEL/ANEEL 

Clique na imagem abaixo para acessar e interagir com o dashboard completo publicado no Tableau Public.

[![Prévia do Dashboard](SIGEL-ANEEL-Aerogeradores-Tableau)](https://public.tableau.com/authoring/SIGELANEEL-Case-Aerogeradores/Painel1#1)

# Tecnologias Utilizadas
- **Python:** Linguagem principal para a extração e processamento.
- **Pandas:** Para manipulação e tratamento dos dados.
- **GeoPandas:** Para o processamento de dados geoespaciais (latitude e longitude).
- **Requests:** Para a extração de dados via web scraping da API da ANEEL.
- **Tableau Public:** Para a criação dos dashboards e visualizações interativas.

### Funções dos códigos
# query_data.py 
Este arquivo visa extração total dos dados disponível em: (https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/WFS/MapServer/0/query) por meio de Web Scraping paginado devido a uma limitação de 1000 linhas por consulta.

# processor_data.py
Este arquivo visa a transformação dos dados brutos de X e Y em longitude e latitude por meio da biblioteca geopandas e salva em um arquivo .csv.
Além disso, trata os seguintes casos:
- Corrige a localização da Usina XI que tem localização em MG e estava com a UF de RN.
- Remoção de quebra de texto (\n) que transformava uma amostra em duas com dados faltantes.
- Remoção de aspas simples e duplas que tinha na coluna PROPRIETARIO.
- Conversão de valores vazios e nulos para np.nan para remoção futura.
- Conversão de colunas numéricas e de data para valores apropriados.
- Arredondar valores de colunas numéricas.
- Tratamento de (Outliers) valores inferiores a 0.1 e superiores a 20 na coluna POT_MW.
- Substituição de valores "1" por "SIM" na coluna OPERACAO.
- Tratamento de valores inválidos da coluna DATUM_EMP para dois casos: Pedra de Amolar I, Pedra de Amolar II.
- Remoção de linhas contendo valores ausentes desconsiderando a coluna ORIGEM (coluna contém só valores nulos).

# notebook_data.py
Este arquivo notebook compila as funções presentes nos arquivos "query_data.py" e "processor_data".
As divisões das células estão descritas abaixo:
- Importação de bibliotecas.
- Definições de URL para extração e destino do arquivo csv.
- Executa a extração paginada da URL por meio da função no arquivo "query_data.py".
- Executa os tratamentos dos dados por meio das funções no arquivo "processor_data.py"
- Descreve brevemente os dados coletados.
- Salva o arquivo csv "aerogeradores_para_tableau.csv" na pasta "outputs" para utilização no Tableau.

### Dicionário dos dados
De acordo com o Site da ANEEL (https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/WFS/MapServer/0), os dados retirados via Web Scraping são:
- POT_MW ( type: esriFieldTypeDouble, alias: Potência (MW) );
- ALT_TOTAL ( type: esriFieldTypeDouble, alias: Altura total );
- ALT_TORRE ( type: esriFieldTypeDouble, alias: Altura da torre );
- DIAM_ROTOR ( type: esriFieldTypeDouble, alias: Diâmetro do rotor );
- DATA_ATUALIZACAO ( type: esriFieldTypeDate, alias: Data da atualização, length: 8 );
- EOL_VERSAO_ID ( type: esriFieldTypeInteger, alias: ID Empreendimento );
- NOME_EOL ( type: esriFieldTypeString, alias: Nome da EOL, length: 254 );
- DEN_AEG ( type: esriFieldTypeString, alias: Denominação do AG, length: 100 );
- X ( type: esriFieldTypeDouble, alias: E );
- Y ( type: esriFieldTypeDouble, alias: N );
- VERSAO ( type: esriFieldTypeString, alias: Versão atual, length: 50 );
- DATUM_EMP ( type: esriFieldTypeString, alias: Datum, length: 50 );
- OPERACAO ( type: esriFieldTypeString, alias: Operação Comercial, length: 50 , Coded Values: [1: SIM] , [2: NÃO] );
- FUSO_AG ( type: esriFieldTypeString, alias: Fuso, length: 50 );
- PROPRIETARIO ( type: esriFieldTypeString, alias: Proprietário, length: 1000 );
- ORIGEM ( type: esriFieldTypeString, alias: Origem do dado, length: 50 );
- OBJECTID ( type: esriFieldTypeOID, alias: OBJECTID );
- UF ( type: esriFieldTypeString, alias: UF, length: 50 );
- CEG ( type: esriFieldTypeString, alias: CEG, length: 21 );
- SHAPE ( type: esriFieldTypeGeometry, alias: SHAPE );

Além disso, foi gerado mais dois campos (longitude e latitude) no arquivo csv e um cálculo no Tableau (Md_Pot_GW).
