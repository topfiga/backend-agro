import os
import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "servidor_online", "fonte": "CEPEA/Noticias Agricolas"}

@app.get("/preco/{produto}")
async def get_preco_real(produto: str):
    if produto.lower() != "soja":
        raise HTTPException(status_code=404, detail="Produto não suportado ainda")

    try:
        # A URL da cotação que você usa como referência
        url = "https://www.noticiasagricolas.com.br/cotacoes/soja"
        
        async with httpx.AsyncClient() as client:
            # Simulamos um navegador real para o site não bloquear
            headers = {"User-Agent": "Mozilla/5.0"}
            response = await client.get(url, headers=headers, timeout=10.0)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscamos a tabela e o valor na classe 'vlr' que aparece no site
                tabela = soup.find('table', {'class': 'cot-lista'})
                if not tabela:
                    raise ValueError("Tabela de cotações não encontrada")
                
                # Pega o primeiro valor disponível na tabela
                primeiro_preco_texto = tabela.find('td', {'class': 'vlr'}).text
                
                # Converte "120,91" para o número 120.91
                valor_final = float(primeiro_preco_texto.replace('.', '').replace(',', '.'))
                
                return {
                    "produto": "soja",
                    "preco": valor_final,
                    "unidade": "sc 60kg",
                    "fonte": "Notícias Agrícolas/CEPEA",
                    "status": "vico"
                }
            else:
                raise HTTPException(status_code=502, detail="Erro ao acessar site de cotações")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
