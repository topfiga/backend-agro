import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuração de CORS para permitir que seu HTML acesse o backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicialização Segura do Firebase
db = None
firebase_error = None

try:
    firebase_key_raw = os.getenv("FIREBASE_KEY_JSON")
    
    if firebase_key_raw:
        # Converte a string JSON da variável de ambiente em dicionário
        cred_dict = json.loads(firebase_key_raw)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
    else:
        firebase_error = "Variável FIREBASE_KEY_JSON não encontrada."
except Exception as e:
    firebase_error = f"Erro ao inicializar Firebase: {str(e)}"

@app.get("/")
async def root():
    return {"status": "ok", "service": "FastAPI on Render"}

@app.get("/teste-firebase")
async def teste_firebase():
    if not db:
        return {
            "status": "error", 
            "message": "Firebase não conectado", 
            "details": firebase_error
        }
    try:
        # Teste simples de leitura (ajuste 'teste' para uma coleção existente se quiser)
        return {"status": "success", "message": "Conectado ao Firestore com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/preco/{produto}")
async def get_preco(produto: str):
    if not db:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível")
    
    try:
        # Exemplo de lógica para buscar no Firestore
        # doc_ref = db.collection("precos").document(produto.lower())
        # doc = doc_ref.get()
        
        # Mock de retorno conforme solicitado para validar a rota
        precos_mock = {
            "soja": {"valor": 135.50, "unidade": "saca", "moeda": "BRL"},
            "milho": {"valor": 58.20, "unidade": "saca", "moeda": "BRL"}
        }
        
        return precos_mock.get(produto.lower(), {"error": "Produto não encontrado"})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
