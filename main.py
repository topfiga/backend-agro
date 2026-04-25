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
    "soja":    {"unidade": "saca 60kg",  "fallback": 135.0, "ref": 135.0},
    "milho":   {"unidade": "saca 60kg",  "fallback": 68.0,  "ref": 68.0},
    "cafe":    {"unidade": "saca 60kg",  "fallback": 900.0, "ref": 900.0},
    "boi":     {"unidade": "arroba",     "fallback": 315.0, "ref": 315.0},
    "frango":  {"unidade": "kg",         "fallback": 7.5,   "ref": 7.5},
    "suino":   {"unidade": "kg",         "fallback": 10.5,  "ref": 10.5},
    "arroz":   {"unidade": "saca 50kg",  "fallback": 82.0,  "ref": 82.0},
    "batata":  {"unidade": "saca 50kg",  "fallback": 95.0,  "ref": 95.0},
    "feijao":  {"unidade": "saca 60kg",  "fallback": 280.0, "ref": 280.0},
    "trigo":   {"unidade": "saca 60kg",  "fallback": 90.0,  "ref": 90.0},
    "algodao": {"unidade": "arroba",     "fallback": 95.0,  "ref": 95.0},
    "leite":   {"unidade": "litro",      "fallback": 2.8,   "ref": 2.8},
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

def checar_variacao(preco_real, produto):
    ref = PRODUTOS_INFO[produto]["ref"]
    variacao = abs((preco_real - ref) / ref) * 100
    if variacao > 30:
        return f"⚠️ VARIAÇÃO ALTA ({variacao:.1f}%) — verifique a fonte"
    return None

def extrair_numero(txt):
    txt = txt.strip().replace(".", "").replace(",", ".")
    nums = re.findall(r'\d+\.\d{2}', txt)
    return float(nums[0]) if nums else None

def buscar_cepea(produto):
    if produto not in URLS_CEPEA:
        return None
    try:
        s = cloudscraper.create_scraper()
        r = s.get(URLS_CEPEA[produto], timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        tabela = soup.find("table", {"id": "imagenet-indicador1"})
        if tabela:
            tds = tabela.find("tbody").find("tr").find_all("td")
            if len(tds) >= 2:
                return extrair_numero(tds[1].text)
    except Exception as e:
        print(f"CEPEA {produto}: {e}")
    return None

def buscar_na(produto):
    if produto not in URLS_NA:
        return None
    try:
        s = cloudscraper.create_scraper()
        r = s.get(URLS_NA[produto], timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        tabela = soup.find("table")
        if tabela:
            for tr in tabela.find_all("tr")[1:]:
                for td in tr.find_all("td"):
                    v = extrair_numero(td.text)
                    if v and v > 1:
                        return v
    except Exception as e:
        print(f"NA {produto}: {e}")
    return None

@app.get("/")
def home():
    return {"status": "ok", "app": "Calculadora Caipira", "versao": "5.0", "produtos": list(PRODUTOS_INFO.keys())}

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
        preco_real = buscar_na(produto)
        fonte = "noticiasagricolas" if preco_real else None

    if not preco_real:
        preco_real = info["fallback"]
        fonte = "fallback"

    alerta = checar_variacao(preco_real, produto)

    resultado = {
        "produto": produto,
        "preco": round(preco_real, 2),
        "unidade": info["unidade"],
        "fonte": fonte,
        "alerta": alerta,
        "atualizado": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "status": "ok"
    }
    _cache[produto] = resultado
    _cache_time[produto] = agora
    return resultado

@app.get("/precos")
def todos_precos():
    return {"precos": {p: preco(p) for p in PRODUTOS_INFO}, "atualizado": datetime.now().strftime("%d/%m/%Y %H:%M")}
