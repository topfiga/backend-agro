import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Tenta carregar a biblioteca de preços que você encontrou
try:
    import agrobr
    from agrobr import preco as agro_preco
except ImportError:
    agro_preco = None

app = FastAPI()

# Permite que seu HTML (mesmo rodando local) converse com o Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURAÇÃO DO FIREBASE ---
db = None
firebase_key = os.getenv("FIREBASE_KEY_JSON")

if firebase_key:
    try:
        cred_dict = json.loads(firebase_key)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("✅ Firebase conectado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao carregar chave do Firebase: {e}")

# --- ROTAS (OS ENDEREÇOS DO SEU SITE) ---

@app.get("/")
def home():
    return {
        "status": "servidor_online",
        "database": "conectado" if db else "offline",
        "biblioteca_agro": "carregada" if agro_preco else "não_instalada"
    }

@app.get("/preco-real/soja")
def get_soja():
    """Busca o preço real usando a biblioteca Python agrobr"""
    if not agro_preco:
        raise HTTPException(status_code=500, detail="Biblioteca agrobr não disponível")
    
    try:
        # Tenta pegar a cotação atual da soja
        valor = agro_preco.soja()
        return {
            "produto": "Soja",
            "valor": valor,
            "fonte": "Cotação via agrobr (Python)",
            "status": "sucesso"
        }
    except Exception as e:
        return {"erro": f"Falha ao buscar cotação: {str(e)}"}

@app.get("/firebase-teste")
def teste_db():
    """Verifica se o Firebase está lendo dados"""
    if not db:
        return {"erro": "Firebase não configurado no Render"}
    return {"status": "sucesso", "mensagem": "Conexão com Firebase está ativa!"}
