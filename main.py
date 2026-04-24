from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "API Agro funcionando"
    }

@app.get("/debug")
def debug():
    return {
        "agrobr_funcoes": dir(agrobr)
    }

@app.get("/preco/{produto}")
def buscar_preco(produto: str):
    try:
        if not hasattr(agrobr, "consultar"):
            return {
                "erro": "A função agrobr.consultar não existe",
                "funcoes_disponiveis": dir(agrobr)
            }

        preco = agrobr.consultar(produto)

        return {
            "produto": produto,
            "preco": preco,
            "moeda": "BRL"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
