import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.routes import user_router, planilha_router, dashboard_router, historico_router

# Log básico pra stdout — em produção (Render/Docker) isso já é coletado
# pela plataforma. Sem isso, exceções tratadas (except/raise HTTPException)
# não deixavam nenhum rastro pra diagnosticar problemas depois do fato.
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI()

# Lista separada por vírgula, ex: "https://meu-ui.onrender.com,http://localhost:3000"
# Definida via env var pra não precisar mudar código a cada novo
# deploy/domínio.
origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,https://ui-6kpo.onrender.com"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.get('/')
def health_check():
    return "Ok, it's working"


app.include_router(user_router)
app.include_router(planilha_router)
app.include_router(dashboard_router)
app.include_router(historico_router)
