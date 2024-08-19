from fastapi import FastAPI, APIRouter

app = FastAPI()
router = APIRouter()

@router.get('/')
def first():
    return "Hello World"

app.include_router(prefix="/first", router=router)