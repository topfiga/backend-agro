from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/preco/milho")
def milho():
    return {"produto": "milho", "preco": 68.5}
