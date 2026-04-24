from fastapi import FastAPI, HTTPException
import agrobr

app = FastAPI()

@app.get("/")
def home():
    return {"status": "ok", "message": "API Agro funcionando!"}

@app.get("/preco/{produto}")
def buscar_preco(produto: str):
    try:
        # Busca o preço usando agrobr
        preco = agrobr.consultar(produto)
        return {
            "produto": produto,
            "preco": preco,
            "moeda": "BRL"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar preço: {str(e)}")

@app.get("/precos")
def listar_precos():
    try:
        produtos = ["soja", "milho", "cafe", "boi", "algodao"]
        precos = {}
        
        for produto in produtos:
            try:
                precos[produto] = agrobr.consultar(produto)
            except:
                precos[produto] = "Não disponível"
        
        return precos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
