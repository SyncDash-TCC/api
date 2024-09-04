from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import user_router, test_router
from fastapi.security import OAuth2PasswordBearer

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
app.include_router(test_router)