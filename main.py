from fastapi import FastAPI
from pydantic import BaseModel
import subprocess

app = FastAPI()

class IAParams(BaseModel):
    email: str
    senha: str
    tipoConta: str
    valorEntrada: float
    stopGain: float
    stopLoss: float
    ativo: str

@app.post("/iniciar-ia")
async def iniciar_ia(params: IAParams):
    args = [
        "python", "ia_executor.py",
        params.email,
        params.senha,
        params.tipoConta,
        str(params.valorEntrada),
        str(params.stopGain),
        str(params.stopLoss),
        params.ativo,
    ]
    subprocess.Popen(args)
    return {"status": "IA iniciada com sucesso"}