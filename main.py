from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/preco/{produto}")
def preco(produto: str):
    return {"produto": produto, "preco": 68.5}
