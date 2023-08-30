from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import datetime


class TunedModel(BaseModel):
    class Config:
        from_attributes = True


class CurrencyBase(TunedModel):
    code: str = Field(..., max_length=3)
    name: str 
    value: Decimal


class CurrencyActual(CurrencyBase):
    datetime_utc: str


class CurrencyResult(CurrencyBase):
    period_begin: datetime | None
    period_end: datetime | None
