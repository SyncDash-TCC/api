from sqlalchemy import Column, Date, DateTime, Float, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, declarative_base


Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    planilhas = relationship("PlanilhaModel", back_populates="user")


class PlanilhaModel(Base):
    __tablename__ = "planilhas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("UserModel", back_populates="planilhas")
    data_venda = Column(Date, nullable=False)
    data_pagamento = Column(Date, nullable=False)
    valor_bruto = Column(Float, nullable=False)
    valor_liquido = Column(Float, nullable=False)
    taxa = Column(Float, nullable=False)
    forma_pagamento = Column(String, nullable=False)
    nome_produto = Column(String, nullable=False)
    categoria_produto = Column(String, nullable=False)
    historic_dashboard_id = Column(Integer, ForeignKey("historic_dashboard.id"))


class HistoricDashboard(Base):
    __tablename__ = "historic_dashboard"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    data_upload_planilha = Column(DateTime, nullable=False)