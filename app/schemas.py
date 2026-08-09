import re
from datetime import date
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
            raise ValueError(
                'O nome de usuário contém caracteres especiais inválidos.')
        return v


class PlanilhaCreate(BaseModel):
    nome_produto: str
    data_venda: date
    data_pagamento: date
    valor_bruto: float
    valor_liquido: float
    taxa: float
    forma_pagamento: str
    categoria: str

    # A UI manda os campos numéricos como string (input type="number"/texto) e
    # pode conter vírgula como separador decimal (ex: "150,50") — normaliza
    # antes do Pydantic tentar converter pra float, senão um valor válido pro
    # usuário vira 422.
    @validator('valor_bruto', 'valor_liquido', 'taxa', pre=True)
    def normalize_decimal_separator(cls, value):
        if isinstance(value, str):
            value = value.strip().replace(',', '.')
        return value


class UpdateVendaRequest(BaseModel):
    id: int
    nome_produto: str
    data_venda: str
    data_pagamento: str
    valor_bruto: float
    valor_liquido: float
    taxa: float
    forma_pagamento: str
    categoria_produto: str
