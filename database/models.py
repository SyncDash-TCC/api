from sqlalchemy import Column, Date, Float, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, declarative_base


Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    panilhas = relationship("PanilhaModel", back_populates="user")


class PanilhaModel(Base):
    __tablename__ = "panilhas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("UserModel", back_populates="panilhas")
    data_venda = Column(Date, nullable=False)
    data_pagamento = Column(Date, nullable=False)
    valor_bruto = Column(Float, nullable=False)
    valor_liquido = Column(Float, nullable=False)
    taxa = Column(Float, nullable=False)
    forma_pagamento = Column(String, nullable=False)
    nome_produto = Column(String, nullable=False)
    categoria_produto = Column(String, nullable=False)