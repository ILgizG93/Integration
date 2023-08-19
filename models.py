import json
import asyncio
from datetime import datetime
from sqlalchemy import Column, Index, Integer, DECIMAL, String
from sqlalchemy.dialects.postgresql import TSRANGE

from config.database import Base, async_session_maker

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import get_async_session

from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger
from alembic_utils.pg_view import PGView
from alembic_utils.replaceable_entity import register_entities


class Currency(Base):
    __tablename__ = "currency"
    id = Column(Integer, primary_key=True)
    code = Column(String(3), nullable=False)
    name = Column(String, nullable=False)
    value = Column(DECIMAL(20, 4), nullable=False)
    period = Column(TSRANGE[datetime], nullable=True)


    def __repr__(self):
        return json.dumps(f'"id": {self.id}, "code": {self.code}, "name": {self.name}, "value": {self.value}, "period": {self.period}')
    
    def get_name(self):
        return self.name

    async def get_currency(self, code, session: AsyncSession = Depends(get_async_session)):
        async with async_session_maker() as session:
            query = await session.execute(select(self.__tablename__).where(self.c.code == code))
            return await query.scalars().first().data


index_currency_code = Index("ix_currency_code", Currency.code)


f_currency = PGFunction(
  schema = 'payments',
  signature = 'f_currency()',
  definition="""
  RETURNS trigger language plpgsql as
  $$
    declare
        current_currency payments.currency%rowtype;
        version timestamp := coalesce(lower(new.period), current_timestamp at time zone 'utc');
        new_id integer = new.id;
    begin
        select * into current_currency from payments.currency where code = new.code and period @> version;

        current_currency.id = null;
        current_currency.period = null;
        new.id = null;
        new.period = null;

        if current_currency = new then
            return null;
        end if;

        update payments.currency set period = tsrange(lower(period), version) where code = new.code and period @> version;

        new.id = new_id;
        new.period = tsrange(version, null);

        return new;
    end;
  $$;
  """
)

t_currency = PGTrigger(
  schema = 'payments',
  on_entity = 'payments.currency',
  signature = 't_currency',
  definition="""
    before insert
	on payments.currency
	for each row
    execute procedure payments.f_currency()
  """
)

v_currency = PGView(
  schema = 'payments',
  signature = 'v_currency',
  definition="""
    select to_char(lower(period),'dd.mm.yyyy hh24:mi:ss') datetime_utc, code, name, value
    from payments.currency c 
    where period @> now() at time zone 'utc'
    order by code, lower(period)
  """
)

register_entities([f_currency, t_currency, v_currency])
