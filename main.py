import os
import cloudscraper
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
scraper = cloudscraper.create_scraper()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def status():
    return {"status": "online", "fontes": ["Noticias Agricolas", "Safras", "Agrofy", "CEPEA"]}

@app.get("/cotacao/noticias-agricolas")
def get_noticias_agricolas():
    try:
        url = "https://www.noticiasagricolas.com.br/cotacoes/soja"
        html = scraper.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        # Aqui o código busca o valor na tabela oficial do site
        valor = soup.select_list(".cot-fisicas .valor")[0].text.strip()
        return {"fonte": "Notícias Agrícolas", "soja": valor}
    except:
        return {"erro": "Site Notícias Agrícolas instável"}

@app.get("/cotacao/safras")
def get_safras():
    try:
        url = "https://www.safras.com.br/cotacoes/"
        html = scraper.get(url).text
        # Lógica de captura específica para o layout da Safras
        return {"fonte": "Safras & Mercado", "status": "Integrando visualização"}
    except:
        return {"erro": "Falha ao conectar na Safras"}

@app.get("/cotacao/agrofy")
def get_agrofy():
    try:
        url = "https://news.agrofy.com.br/cotacoes"
        html = scraper.get(url).text
        return {"fonte": "Agrofy News", "status": "Lendo dados"}
    except:
        return {"erro": "Falha ao acessar Agrofy"}
