from decimal import Decimal
from pydantic import BaseModel, Field


class TunedModel(BaseModel):
    class Config:
        orm_mode = True


class CurrencyBase(TunedModel):
    code: str = Field(..., max_length=3)
    name: str 
    value: Decimal


class CurrencyActual(CurrencyBase):
    datetime: str


class CurrencyResult(CurrencyBase):
    pass
