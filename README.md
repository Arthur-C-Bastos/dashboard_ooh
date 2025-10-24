# 🚀 OOH Dashboard BR: Plataforma de Inteligência Tática para Mídia Externa

## Introdução

Este projeto é uma **Plataforma Interativa de Análise Tática para Mídia Out-Of-Home (OOH)**, desenvolvida para transformar dados geográficos e contextuais em inteligência de negócios.

Utilizando **geocoding**, análise de **sazonalidade** e visualizações **geoespaciais avançadas (Folium/GeoPandas)**, o Dashboard permite a otimização da seleção de pontos de mídia, a projeção de investimentos e a criação de relatórios executivos.

O objetivo é demonstrar proficiência em **Data Apps (Streamlit)**, **Geoprocessamento** e **Integração de APIs** em um caso de uso real do mercado brasileiro.

---

### ✨ Destaques e Valor de Negócio

| Recurso Principal | Benefício Estratégico |
| :--- | :--- |
| **🗺️ Análise Geoespacial Dinâmica** | Identificação e visualização imediata da densidade de mídias OOH e seus competidores (POIs) por região. |
| **🎯 Cálculo de Proximidade (Buffer)** | Avaliação precisa do **raio de impacto** (e.g., 500m) de cada ponto de mídia em relação a locais de alto tráfego (Ex: Paradas de Ônibus). |
| **🔎 Pesquisa por Endereço/Bairro** | Usabilidade aprimorada, permitindo centralizar a análise em qualquer ponto do mapa com apenas um termo de busca. |
| **📈 Projeção Sazonal** | Simulação tática de campanhas futuras, aplicando taxas de crescimento percentuais para previsão de ROI. |
| **📄 Geração de Relatórios (PDF)** | Demonstra a capacidade de construir um pipeline de dados do zero até a entrega executiva. |

---

### 💻 Tecnologias (Tech Stack)

Este projeto foi construído sobre uma arquitetura moderna, com foco em performance e análise geoespacial.

| Categoria | Tecnologia | Função no Projeto |
| :--- | :--- | :--- |
| **Frontend/App** | **Streamlit** | Desenvolvimento rápido da UI interativa e sistema multipáginas. |
| **Geoprocessamento** | **GeoPandas** / **Shapely** | Manipulação de geometrias vetoriais, criação de buffers e cálculo de intersecções. |
| **Visualização** | **Folium** / `streamlit-folium` | Renderização de mapas dinâmicos, clusters de marcadores e HeatMaps. |
| **Data/APIs** | **Pandas** / **Requests** | ETL, manipulação de dados e consumo da **Overpass API** (OpenStreetMap) para POIs. |
| **Geocoding** | **Geopy** (Nominatim) | Conversão de nomes de bairros/endereços em coordenadas de Lat/Lon. |

---

### ⚙️ Como Executar Localmente

Siga os passos abaixo para rodar a aplicação em sua máquina:

1.  **Clone o Repositório:**
    ```bash
    git clone [link suspeito removido]
    cd dashboard_ooh
    ```

2.  **Crie e Ative o Ambiente Virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # venv\Scripts\activate    # Windows
    ```

3.  **Instale as Dependências:**
    *(É crucial ter todas as bibliotecas de geoprocessamento (`geopandas`, `shapely`, `geopy`) instaladas corretamente.)*
    ```bash
    pip install -r requirements.txt
    ```

4.  **Inicie a Aplicação Streamlit:**
    ```bash
    streamlit run app.py
    ```

O Dashboard será aberto automaticamente em seu navegador (geralmente em `http://localhost:8501`).

---

### 🤝 Contribuições

Contribuições, sugestões e críticas são muito bem-vindas! Se você tiver ideias para melhorias na UX, performance do geoprocessamento ou adição de novas APIs de dados, sinta-se à vontade para abrir uma *issue* ou um *pull request*.

**Desenvolvido por:** [Arthur Bastos / https://www.linkedin.com/in/arthur-bastos-566674106/]
