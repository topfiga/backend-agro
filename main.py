import cloudscraper
from bs4 import BeautifulSoup
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import re

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_cache = {}
_cache_time = {}
CACHE_SEGUNDOS = 3600

PRODUTOS_INFO = {
    "soja":    {"unidade": "saca 60kg",  "fallback": 135.0, "min": 80,   "max": 250},
    "milho":   {"unidade": "saca 60kg",  "fallback": 68.0,  "min": 40,   "max": 150},
    "cafe":    {"unidade": "saca 60kg",  "fallback": 900.0, "min": 500,  "max": 2000},
    "boi":     {"unidade": "arroba",     "fallback": 315.0, "min": 200,  "max": 500},
    "frango":  {"unidade": "kg",         "fallback": 7.5,   "min": 4,    "max": 20},
    "suino":   {"unidade": "kg",         "fallback": 10.5,  "min": 5,    "max": 25},
    "arroz":   {"unidade": "saca 50kg",  "fallback": 82.0,  "min": 50,   "max": 180},
    "batata":  {"unidade": "saca 50kg",  "fallback": 95.0,  "min": 30,   "max": 200},
    "feijao":  {"unidade": "saca 60kg",  "fallback": 280.0, "min": 100,  "max": 600},
    "trigo":   {"unidade": "saca 60kg",  "fallback": 90.0,  "min": 50,   "max": 200},
    "algodao": {"unidade": "arroba",     "fallback": 95.0,  "min": 50,   "max": 200},
    "leite":   {"unidade": "litro",      "fallback": 2.8,   "min": 1.5,  "max": 6},
}

URLS_CEPEA = {
    "soja":    "https://www.cepea.esalq.usp.br/br/indicador/soja.aspx",
    "milho":   "https://www.cepea.esalq.usp.br/br/indicador/milho.aspx",
    "cafe":    "https://www.cepea.esalq.usp.br/br/indicador/cafe.aspx",
    "boi":     "https://www.cepea.esalq.usp.br/br/indicador/boi-gordo.aspx",
    "frango":  "https://www.cepea.esalq.usp.br/br/indicador/frango.aspx",
    "suino":   "https://www.cepea.esalq.usp.br/br/indicador/suino.aspx",
    "arroz":   "https://www.cepea.esalq.usp.br/br/indicador/arroz.aspx",
    "feijao":  "https://www.cepea.esalq.usp.br/br/indicador/feijao.aspx",
    "trigo":   "https://www.cepea.esalq.usp.br/br/indicador/trigo.aspx",
    "algodao": "https://www.cepea.esalq.usp.br/br/indicador/algodao.aspx",
    "leite":   "https://www.cepea.esalq.usp.br/br/indicador/leite.aspx",
}

URLS_NA = {
    "soja":   "https://www.noticiasagricolas.com.br/cotacoes/soja",
    "milho":  "https://www.noticiasagricolas.com.br/cotacoes/milho",
    "cafe":   "https://www.noticiasagricolas.com.br/cotacoes/cafe",
    "boi":    "https://www.noticiasagricolas.com.br/cotacoes/boi-gordo",
    "frango": "https://www.noticiasagricolas.com.br/cotacoes/frango",
    "suino":  "https://www.noticiasagricolas.com.br/cotacoes/suinos",
    "arroz":  "https://www.noticiasagricolas.com.br/cotacoes/arroz",
    "feijao": "https://www.noticiasagricolas.com.br/cotacoes/feijao",
    "trigo":  "https://www.noticiasagricolas.com.br/cotacoes/trigo",
}

def valor_valido(v, produto):
    info = PRODUTOS_INFO[produto]
    return info["min"] <= v <= info["max"]

def buscar_cepea(produto: str):
    if produto not in URLS_CEPEA:
        return None
    try:
        scraper = cloudscraper.create_scraper()
        r = scraper.get(URLS_CEPEA[produto], timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        tabela = soup.find("table", {"id": "imagenet-indicador1"})
        if tabela:
            linha = tabela.find("tbody").find("tr")
            celulas = linha.find_all("td")
            if len(celulas) >= 2:
                txt = celulas[1].text.strip().replace(".", "").replace(",", ".")
                v = float(re.sub(r"[^\d.]", "", txt))
                if valor_valido(v, produto):
                    return v
    except Exception as e:
        print(f"CEPEA {produto}: {e}")
    return None

def buscar_na(produto: str):
    if produto not in URLS_NA:
        return None
    try:
        scraper = cloudscraper.create_scraper()
        r = scraper.get(URLS_NA[produto], timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        # Pega tabela de cotações
        tabela = soup.find("table", {"class": "cotacoes-table"})
        if not tabela:
            tabela = soup.find("table")
        if tabela:
            linhas = tabela.find_all("tr")
            for linha in linhas[1:]:
                tds = linha.find_all("td")
                for td in tds:
                    txt = td.text.strip().replace(".", "").replace(",", ".")
                    nums = re.findall(r'\d+\.\d{2}', txt)
                    for n in nums:
                        v = float(n)
                        if valor_valido(v, produto):
                            return v
    except Exception as e:
        print(f"NA {produto}: {e}")
    return None

@app.get("/")
def home():
    return {"status": "ok", "app": "Calculadora Caipira", "versao": "4.0", "produtos": list(PRODUTOS_INFO.keys())}

@app.get("/preco/{produto}")
def preco(produto: str):
    produto = produto.lower().strip()
    if produto not in PRODUTOS_INFO:
        return {"erro": "Produto inválido", "validos": list(PRODUTOS_INFO.keys())}

    agora = datetime.now().timestamp()
    if produto in _cache and (agora - _cache_time.get(produto, 0)) < CACHE_SEGUNDOS:
        return {**_cache[produto], "cache": True}

    info = PRODUTOS_INFO[produto]
    
    # 1. Tenta CEPEA
    preco_real = buscar_cepea(produto)
    fonte = "cepea" if preco_real else None

    # 2. Tenta Noticias Agricolas
    if not preco_real:
        preco_real = buscar_na(produto)
        fonte = "noticiasagricolas" if preco_real else None

    # 3. Fallback
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
    return {"precos": {p: preco(p) for p in PRODUTOS_INFO}, "atualizado": datetime.now().strftime("%d/%m/%Y %H:%M")}
