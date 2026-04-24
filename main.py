from fastapi import FastAPI
from agrobr import cepea

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/preco/{produto}")
def preco(produto: str):
    try:
        df = cepea.get(produto)

        # pega o último preço
        valor = df.iloc[-1]['preco']

        return {
            "produto": produto,
            "preco": float(valor)
        }

    except Exception as e:
        return {
            "erro": "produto inválido ou falha no agrobr",
            "detalhe": str(e)
        }
