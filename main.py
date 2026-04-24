from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agrobr.sync import cepea
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PRODUTOS = {
    "soja":  {"unidade": "saca 60kg"},
    "milho": {"unidade": "saca 60kg"},
    "cafe":  {"unidade": "saca 60kg"},
    "boi":   {"unidade": "arroba"},
}

PRECOS_BASE = {
    "soja": 135.0, "milho": 68.0, "cafe": 900.0, "boi": 315.0
}

_cache = {}
_cache_time = {}
CACHE_SEGUNDOS = 3600

@app.get("/")
def home():
    return {"status": "ok", "app": "Calculadora Caipira", "versao": "2.0"}

@app.get("/preco/{produto}")
def preco(produto: str):
    produto = produto.lower().strip()
    if produto not in PRODUTOS:
        return {"erro": "Produto inválido", "validos": list(PRODUTOS.keys())}

    agora = datetime.now().timestamp()
    if produto in _cache and (agora - _cache_time.get(produto, 0)) < CACHE_SEGUNDOS:
        return _cache[produto]

    preco_real = None
    fonte = "base"

    try:
        df = cepea.indicador(produto)
        if df is not None and not df.empty:
            preco_real = float(df["preco"].iloc[-1])
            fonte = "cepea"
    except Exception as e:
        print(f"agrobr erro {produto}: {e}")

    if not preco_real:
        preco_real = PRECOS_BASE.get(produto, 0)

    resultado = {
        "produto": produto,
        "preco": round(preco_real, 2),
        "unidade": PRODUTOS[produto]["unidade"],
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
        "precos": {p: preco(p) for p in PRODUTOS},
        "atualizado": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
