import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Importamos a biblioteca que você achou (exemplo hipotético da agrobr)
try:
    from agrobr import preco 
except ImportError:
    preco = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "ok", "biblioteca_agro": "carregada" if preco else "erro"}

@app.get("/preco-real/{produto}")
def buscar_preco_agro(produto: str):
    if not preco:
        return {"erro": "Biblioteca agrobr não instalada"}
    
    try:
        # Aqui o Python faz o trabalho pesado que o HTML não consegue
        # Exemplo: busca a cotação atual usando a biblioteca
        dados = preco.get(produto) 
        return {
            "produto": produto,
            "valor": dados.valor, 
            "fonte": "agrobr",
            "data": dados.data
        }
    except Exception as e:
        return {"erro": f"Não consegui buscar o preço: {str(e)}"}
