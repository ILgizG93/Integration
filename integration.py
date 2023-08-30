#   СКРИПТ ДЛЯ ПАРСИНГА КУРСА ВАЛЮТ ЦБ

#   Устанавливаем необходимые компоненты
#   pip install pydantic_xml fastapi_soap

from datetime import datetime
import xml.etree.ElementTree as et
from pydantic import BaseModel
import requests
from decimal import *


URL = f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={datetime.now().strftime('%d/%m/%Y')}"

class Currency(BaseModel):
    id: int = None
    code: str = None
    name: str = None
    value: float = None


class CBSrapper:
    CURRENCY_LIST = ["R01235", "R01239", "R01375"]
    CURRENCY_CODE = ["USD", "EUR", "CNY"]

    def __init__(self, url):
        self.url = url

    
    def get_xml(self):
        try:
            return et.fromstring(requests.get(self.url).content)
        except RuntimeError as err:
            return {"error":err}
    

    def export_data(self):
        list = []
        for item in self.get_xml().findall('.//Valute'):
            if item[1].text in self.CURRENCY_CODE:
                list.append({"id":item.attrib["ID"], "code":item[1].text, "name":item[3].text, "value":item[4].text})
                if len(list) == len(self.CURRENCY_CODE):
                    break
        return list
    

    def export_data_with_pydantic(self):
        list = []
        i = 0
        for item in self.get_xml().findall('.//Valute'):
            if item.attrib["ID"] in self.CURRENCY_LIST:
                list.append(Currency())
                list[i].id = item.attrib["ID"]
                list[i].code = item[1].text
                list[i].name = item[3].text
                list[i].value = item[4].text
                list[i] = list[i].__dict__
                i+= 1
        return list
    
    
    def main(self):
        data = self.export_data_with_pydantic()
        return data

if __name__ == '__main__':
    scrapper = CBSrapper(URL)
    result = scrapper.main()
    #asyncio.run(scrapper.main())
    print(result)
