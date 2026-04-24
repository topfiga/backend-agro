from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/preco/{produto}")
def preco(produto: str):
    precos = {
        "soja": 150,
        "milho": 80
    }

    return {
        "produto": produto,
        "preco": precos.get(produto, "não encontrado")
    }
