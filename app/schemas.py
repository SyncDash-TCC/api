import re
from pydantic import BaseModel, validator


class User(BaseModel):
    username: str
    password: str

    @validator('username')
    def validate_username(cls, value):
        if not re.match('^([a-zA-Z0-9]+)$', value):
            raise ValueError('Username format invalid')
        return value
    

class LoginRequest(BaseModel):
    username: str
    password: str

    # Validação para verificar caracteres especiais no campo username
    @validator('username')
    def no_special_characters(cls, v):
        if re.search(r'[^a-zA-Z0-9_]', v):
            raise ValueError('O nome de usuário contém caracteres especiais inválidos.')
        return v
    

class PlanilhaCreate(BaseModel):
    nome_produto: str
    data_venda: str
    data_pagamento: str
    valor_bruto: str
    valor_liquido: str
    taxa: str
    forma_pagamento: str
    categoria: str