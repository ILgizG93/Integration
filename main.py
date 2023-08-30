from fastapi import FastAPI, Depends, Request, status
import models, schemas
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from config.database import get_async_session
from integration import *
from decimal import *

app = FastAPI()

"""!!!ТОЛЬКО ДЛЯ ОТЛАДКИ!!!"""
"""↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓"""
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(ResponseValidationError)
async def validation_exception_handler(request: Request, exc: ResponseValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors()}),
    )
    

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors()}),
    )
"""↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑"""
"""!!!ТОЛЬКО ДЛЯ ОТЛАДКИ!!!"""


# Вывод записей из бд
@app.get("/currency_values_all/")
async def get_currencies(offset: int = 0, limit: int = 10, session: AsyncSession = Depends(get_async_session)):
    async with session.begin():
        result = await session.execute(select(models.Currency).offset(offset).limit(limit).order_by(models.Currency.period.desc(), models.Currency.code))
        result = result.scalars().all()
        if result is None:
            return {"result": "Данные отсутствуют."}
        else:
            return [schemas.CurrencyResult(**r.__dict__, period_begin=r.period.lower, period_end=r.period.upper) for r in result]


# Вывод актуального курса по указанному коду (USD, EUR, CNY) из представления, сформированного в миграции
@app.get("/currency_actual/{code}/")
async def get_currencies(code: str, session: AsyncSession = Depends(get_async_session)):
    async with session.begin():
        sql = f"SELECT * FROM payments.v_currency where code in ('{code}')"
        result = await session.execute(text(sql))
        result = result.first()
        if result is None:
            return {"result": "Данные по введённому курсу отсутствуют."}
        else:
            return [schemas.CurrencyActual(**result._mapping)]


# Интеграция с ЦБ с последующим сохранением курсов в бд
@app.post("/save_currency_values/")
async def save_currencies(session: AsyncSession = Depends(get_async_session)):
    scrapper = CBSrapper(URL)
    data = scrapper.main()
    result = []
    try:
        async with session.begin():
            for d in data:
                value = round(Decimal(d["value"].replace(",", ".")),4)
                stmt = await session.execute(insert(models.Currency).values(code=d["code"], name=d["name"], value=Decimal(value)).returning(models.Currency))
                if stmt.first() is None:
                    result.append({d["code"]: "Данные актуальны"})
                else:
                    result.append(stmt.first()[0])
            await session.commit()
            return {"result": "Данные обработаны.", "detail": result}
    except Exception as err:
        await session.rollback()
        return {"error": err}


"""
if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)

"""
