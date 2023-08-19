from fastapi import FastAPI, Depends, Request, status
import models, schemas
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from config.database import engine, get_async_session
from parsing import *
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
@app.get("/currency_values_all/?{offset}&{limit}")
async def get_currencies(offset: int, limit: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(models.Currency).offset(offset).limit(limit))
    result = result.scalars().all()
    if result:
        return [schemas.CurrencyResult(**r.__dict__) for r in result]
    else:
        return {"result": "Данные отсутствуют."}


# Вывод актуального курса по указанному коду (USD, EUR, CNY) из представления, сформированного в миграции
@app.get("/currency_actual/{code}/")
async def get_currencies(code: str, session: AsyncSession = Depends(get_async_session)):
    sql = f"SELECT * FROM payments.v_currency where code in ('{code}')"
    result = await session.execute(text(sql))
    result = result.first()
    if result:
        return [schemas.CurrencyActual(datetime=result[0], code=result[1], name=result[2], value=result[3])]
    else:
        return {"result": "Данные по введённому коду отсутствуют."}


# Парсинг сайта ЦБ с последующим сохранением курсов в бд
@app.post("/save_currency_values/")
async def save_currencies(session: AsyncSession = Depends(get_async_session)):
    scrapper = CBSrapper(URL)
    data = scrapper.main()
    try:
        session.begin()
        for d in data:
            value = round(Decimal(d["value"].replace(",", ".")),4)
            await session.execute(insert(models.Currency).values(code=d["code"], name=d["name"], value=Decimal(value)))
        await session.commit()
        return {"result": "Данные обработаны."}
    except Exception as err:
        return {"error": err}


"""
if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)

"""
