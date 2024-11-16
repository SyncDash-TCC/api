from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import user_router, planilha_router, dashboard_router, historico_router

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def health_check():
    return "Ok, it's working"

app.include_router(user_router)
app.include_router(planilha_router)
app.include_router(dashboard_router)
app.include_router(historico_router)