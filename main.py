import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests # Necessário para ler o Google Sheets

# Tenta carregar a biblioteca agrobr
try:
    import agrobr
    from agrobr import preco as agro_preco
except ImportError:
    agro_preco = None
  
app = FastAPI()

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
    except Exception as e:
        print(f"❌ Erro Firebase: {e}")

@app.get("/preco-real/soja")
def motor_de_busca():
    """O Firebase decide para onde o motor deve ir buscar o preço"""
    if not db:
        raise HTTPException(status_code=500, detail="Firebase não conectado")

    try:
        # 1. Busca a instrução de onde ir no Firebase
        doc = db.collection("config").document("soja").get()
        if not doc.exists:
            return {"erro": "Configure a 'fonte' no Firebase (coleção: config, doc: soja)"}
        
        config = doc.to_dict()
        fonte = config.get("fonte") # Pode ser 'agrobr' ou 'google_sheets'

        # 2. SE A FONTE FOR AGROBR (Busca direta)
        if fonte == "agrobr" and agro_preco:
            return {
                "produto": "Soja",
                "valor": agro_preco.soja(),
                "metodo": "Direto via agrobr"
            }

        # 3. SE A FONTE FOR GOOGLE (Usa o Google como escudo contra bloqueio)
        if fonte == "google_sheets":
            url_planilha = config.get("url_csv") # URL da sua planilha publicada como CSV
            if not url_planilha:
                return {"erro": "URL da planilha não configurada no Firebase"}
            
            resposta = requests.get(url_planilha)
            valor = resposta.text.strip().split('\n')[-1] # Pega o último valor da planilha
            return {
                "produto": "Soja",
                "valor": float(valor.replace(',', '.')),
                "metodo": "Google Sheets (Escudo Anti-Bloqueio)"
            }

        return {"erro": f"Fonte '{fonte}' indicada pelo Firebase não está disponível"}

    except Exception as e:
        return {"erro": f"Falha no motor de busca: {str(e)}"}

@app.get("/")
def home():
    return {"status": "servidor_online", "database": "conectado" if db else "offline"}
