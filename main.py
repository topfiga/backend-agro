import cloudscraper
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache = {}
_cache_time = {}
CACHE_SEGUNDOS = 3600

PRODUTOS_INFO = {
    "soja":  {"unidade": "saca 60kg", "fallback": 135.0},
    "milho": {"unidade": "saca 60kg", "fallback": 68.0},
    "cafe":  {"unidade": "saca 60kg", "fallback": 900.0},
    "boi":   {"unidade": "arroba",    "fallback": 315.0},
}

URLS_CEPEA = {
    "soja":  "https://www.cepea.esalq.usp.br/br/indicador/soja.aspx",
    "milho": "https://www.cepea.esalq.usp.br/br/indicador/milho.aspx",
    "cafe":  "https://www.cepea.esalq.usp.br/br/indicador/cafe.aspx",
    "boi":   "https://www.cepea.esalq.usp.br/br/indicador/boi-gordo.aspx",
}

def buscar_cepea(produto: str):
    try:
        scraper = cloudscraper.create_scraper()
        r = scraper.get(URLS_CEPEA[produto], timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        tabela = soup.find("table", {"id": "imagenet-indicador1"})
        if tabela:
            linha = tabela.find("tbody").find("tr")
            celulas = linha.find_all("td")
            if len(celulas) >= 2:
                valor_txt = celulas[1].text.strip()
                valor_txt = valor_txt.replace(".", "").replace(",", ".")
                return float(valor_txt)
    except Exception as e:
        print(f"CEPEA erro {produto}: {e}")
    return None

def buscar_noticiasagricolas(produto: str):
    urls = {
        "soja":  "https://www.noticiasagricolas.com.br/cotacoes/soja",
        "milho": "https://www.noticiasagricolas.com.br/cotacoes/milho",
        "cafe":  "https://www.noticiasagricolas.com.br/cotacoes/cafe",
        "boi":   "https://www.noticiasagricolas.com.br/cotacoes/boi-gordo",
    }
    try:
        scraper = cloudscraper.create_scraper()
        r = scraper.get(urls[produto], timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        spans = soup.find_all("span", {"class": "intraday-price"})
        if spans:
            txt = spans[0].text.strip().replace(".", "").replace(",", ".")
            return float(txt)
        matches = re.findall(r'(\d{2,4}[,\.]\d{2})', r.text)
        if matches:
            txt = matches[0].replace(".", "").replace(",", ".")
            return float(txt)
    except Exception as e:
        print(f"NoticiasAgricolas erro {produto}: {e}")
    return None

@app.get("/")
def home():
    return {
        "status": "ok",
        "app": "Calculadora Caipira",
        "versao": "3.0",
        "produtos": list(PRODUTOS_INFO.keys())
    }

@app.get("/preco/{produto}")
def preco(produto: str):
    produto = produto.lower().strip()
    if produto not in PRODUTOS_INFO:
        return {"erro": "Produto inválido", "validos": list(PRODUTOS_INFO.keys())}

    agora = datetime.now().timestamp()
    if produto in _cache and (agora - _cache_time.get(produto, 0)) < CACHE_SEGUNDOS:
        return {**_cache[produto], "cache": True}

    info = PRODUTOS_INFO[produto]
    preco_real = buscar_cepea(produto)
    fonte = "cepea" if preco_real else None

    if not preco_real:
        preco_real = buscar_noticiasagricolas(produto)
        fonte = "noticiasagricolas" if preco_real else "fallback"

    if not preco_real:
        preco_real = info["fallback"]
        fonte = "fallback"

    resultado = {
        "produto": produto,
        "preco": round(preco_real, 2),
        "unidade": info["unidade"],
        "fonte": fonte,
        "atualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "status": "ok"
    }
    _cache[produto] = resultado
    _cache_time[produto] = agora
    return resultado

@app.get("/precos")
def todos_precos():
    return {
        "precos": {p: preco(p) for p in PRODUTOS_INFO},
        "atualizado": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
