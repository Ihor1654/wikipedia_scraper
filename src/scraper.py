from httpx import AsyncClient
from bs4 import BeautifulSoup
import re
import requests as r
import asyncio
import time
import threading
import json


class RunThread(threading.Thread):
    def __init__(self, coro):
        self.coro = coro
        self.result = None
        super().__init__()

    def run(self):
        self.result = asyncio.run(self.coro)




class WikipediaScraper:
    """
    
    """
    def __init__(self) -> None:
        self.base_url = "https://country-leaders.onrender.com"
        self.country_endpoint = '/countries'
        self.leaders_endpoint = '/leaders'
        self.cookies_endpoint = '/cookie'
        self.check_endpoint = '/check'
        self.leaders_data = {}
        self.cookie = None

    def get_cookies(self):
        self.cookie = r.get(f"{self.base_url}{self.cookies_endpoint}").cookies


    def check_cookies(self):
        req = r.get(f'{self.base_url}{self.check_endpoint}')
        match req.json()['message']:
            case "The cookie is missing":
                return False
            case "The cookie is expired":
                return False
            case "The cookie is valid":
                return True
            case _:
                return False

    def refresh_cookie(self):
        if not self.check_cookies():
            self.get_cookies()
            return self.cookie
        else:
            return self.cookie
        

    def get_countries_list(self):
            countries_list = r.get(f"{self.base_url}{self.country_endpoint}",cookies=self.refresh_cookie()).json()
            return countries_list
    
    def run_as(self,coro):
        try:
            global_loop = asyncio.get_running_loop()
        except  RuntimeError:
            loop = None
        if global_loop and global_loop.is_running():
            thread = RunThread(coro)
            thread.start()
            thread.join()
            return thread.result
        else:
            print('Starting new event loop')
            return asyncio.run(coro)


        
    async def get_leaders_for_country_async(self,country: str,session: AsyncClient):
        response = await session.get(f'{self.base_url}{self.leaders_endpoint}?country={country}',cookies=self.refresh_cookie())
        res_json = response.json()
        res_json.append(country)
    
        return res_json
    

    async def get_leaders_for_countries_async(self):
        async with AsyncClient( ) as session:
            tasks = [asyncio.create_task(self.get_leaders_for_country_async(ctr,session)) for ctr in self.get_countries_list()]
            responses = await asyncio.gather(*tasks)
            links_per_country_dict ={country[-1]: [_['wikipedia_url'] for _ in country[:-1]] for country in responses}
            return links_per_country_dict
    

    async def get_first_paragraph(self,wikipedia_url,session):
        try:
            print(wikipedia_url)
            response = await session.get(wikipedia_url)
        except:
            print(1)
        soup = BeautifulSoup(response.content,features='html')
        paragraphs = soup.find_all('p')
        for paragraph in paragraphs:
            if re.search(r'\d{4}.*?\d{4}',str(paragraph)):
                first_paragraph = str(paragraph)
                break
        patern_list = [re.compile(patern) for patern in [r'<sup class="reference" .*?>.*?</sup>', r'[(]<span .*?>.*?>[)]', r'<.*?>', r'.mw.*Écouter']]
        for patern in patern_list:
            first_paragraph = patern.sub('',first_paragraph)
        return first_paragraph
    
    async def get_paragraphs_for_country(self,links_per_country_dict: dict, country_code : str):
        async with AsyncClient() as session:
            tasks = [asyncio.create_task(self.get_first_paragraph(link,session)) for link in links_per_country_dict[country_code]]
            response = await asyncio.gather(*tasks)
            print(response)
            return response
    
    def get_final_dict(self):
        for country in  self.get_countries_list():
            while True:
                self.leaders_data[country]  = self.run_as(self.get_paragraphs_for_country(self.run_as(self.get_leaders_for_countries_async()),country))
                if self.leaders_data[country]:
                     break
        return self.leaders_data
    
    def to_json_file(self, filepath:str):
        with open(filepath,mode='w',encoding='utf8') as write_file:
            json.dump(self.leaders_data,write_file,ensure_ascii=False)


