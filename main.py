from fastapi import FastAPI
import firebase_admin
from firebase_admin import credentials, firestore

app = FastAPI()

# inicializa firebase (usa variável de ambiente depois)
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/salvar/{produto}/{preco}")
def salvar(produto: str, preco: float):
    db.collection("precos").document(produto).set({
        "valor": preco
    })

    return {"msg": "salvo"}

@app.get("/preco/{produto}")
def buscar(produto: str):
    doc = db.collection("precos").document(produto).get()

    if doc.exists:
        return doc.to_dict()
    else:
        return {"erro": "não encontrado"}
