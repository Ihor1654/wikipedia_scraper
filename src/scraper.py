from httpx import AsyncClient
from bs4 import BeautifulSoup
import re
import requests as r
import asyncio
import time
import threading
import json


class RunThread(threading.Thread):
    """
    Class inheritance from threading.Thread and creates thread for coroutine
    :properties:
    coro
    result
    :methods:
    run()
    """
    def __init__(self, coro):
        self.coro = coro
        self.result = None
        super().__init__()

    def run(self)-> None:
        """
            Method run the coroutine
        """
        self.result = asyncio.run(self.coro)




class WikipediaScraper:
    """
        Class conects to API, get data about all leaders per contries from there,
        gets wikipedia links for each leader and scraps first paragraph from their wikipedia pages
        and save it to json file. 
        :property:
        self.base_url = "https://country-leaders.onrender.com"
        self.country_endpoint = '/countries'
        self.leaders_endpoint = '/leaders'
        self.cookies_endpoint = '/cookie'
        self.check_endpoint = '/check'
        self.leaders_data = {}
        self.cookie = None
        :methods:
        .get_cookies()
        .check_cookies()
        .refresh_cookie()
        .get_countries_list()
        .run_as()
        .get_leaders_for_country_async()
        .get_leaders_for_countries_async()
        .get_first_paragraph()
        .get_paragraphs_for_country()
        .get_final_dict()
        .to_json_file()
    """
    def __init__(self) -> None:
        self.base_url = "https://country-leaders.onrender.com"
        self.country_endpoint = '/countries'
        self.leaders_endpoint = '/leaders'
        self.cookies_endpoint = '/cookie'
        self.check_endpoint = '/check'
        self.leaders_data = {}
        self.cookie = None

    def get_cookies(self)-> None:
        """
            Method gets cookies from API
        """
        self.cookie = r.get(f"{self.base_url}{self.cookies_endpoint}").cookies


    def check_cookies(self)-> bool:
        """
            Method check if cookies available
            :return: bool, True if cookie is valid, False if missing or expired
        """
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
        """
            Method check state of cookie and refresh them if necessary
            :return: cookie
        """
        if not self.check_cookies():
            self.get_cookies()
            return self.cookie
        else:
            return self.cookie
        

    def get_countries_list(self) -> list:
            """
                Method get available countries from API and return them as a list
                :return: list countries_list, of available countries
            """
            countries_list = r.get(f"{self.base_url}{self.country_endpoint}",cookies=self.refresh_cookie()).json()
            return countries_list
    
    def run_as(self,coro)->None:
        """
            Method checks if there is a running loop if it so, creates and run thread with coroutine, otherwise run corutine in a loop
            :param: coro, coroutien function
        """
        try:
            global_loop = asyncio.get_running_loop()
        except  RuntimeError:
            global_loop = None
        if global_loop and global_loop.is_running():
            thread = RunThread(coro)
            thread.start()
            thread.join()
            return thread.result
        else:
            print('Starting new event loop')
            return asyncio.run(coro)


        
    async def get_leaders_for_country_async(self,country: str,session: AsyncClient)->list:
        """
            Method-coroutin gets all leaders data from API for specific country and appends 
            :param: str country, country code
            :param: session, instance of httpx.AsyncClient()
            :return: list res_json, that contains the dictionaries with data for each leader and the country code as the last element.
        """
        response = await session.get(f'{self.base_url}{self.leaders_endpoint}?country={country}',cookies=self.refresh_cookie())
        res_json = response.json()
        res_json.append(country)

        return res_json
    

    async def get_leaders_for_countries_async(self)-> dict:
        """
        Method-coroutine creates and runs asynchronous get_leaders_for_country_async coroutines,
        when they are done creats and return dictionarie with 
        leaders wikipedia links as a values and country codes as a keys.
        :return: dict links_per_country_dict 

        """
        async with AsyncClient( ) as session:
            tasks = [asyncio.create_task(self.get_leaders_for_country_async(ctr,session)) for ctr in self.get_countries_list()]
            responses = await asyncio.gather(*tasks)
            links_per_country_dict ={country[-1]: [_['wikipedia_url'] for _ in country[:-1]] for country in responses}
            return links_per_country_dict
    

    async def get_first_paragraph(self,wikipedia_url : str,session: AsyncClient)-> str:
        """
            Method-coroutine gets,cleans up and returns short-bio paragraph of specific leaders wiki page 
        :param: str wikipedia_url, wiki link
        :param: AsyncClient session instance of httpx.AsyncClient
        :return: str first_paragraph short-bio paragraph of the wiki page
        """
        while True:
            try:
                response = await session.get(wikipedia_url)
                break
            except Exception as e:
                print(1)
    
        soup = BeautifulSoup(response.content,features='html')
        paragraphs = soup.find_all('p')
        for paragraph in paragraphs:
            if re.search(r'\d{4}.*?\d{4}',str(paragraph)):
                first_paragraph = str(paragraph)
                break
        patern_list = [re.compile(patern) for patern in [r'<sup class="reference" .*?>.*?</sup>', r'[(]<span .*?>.*?>[)]', r'<.*?>', r'.mw.*Écouter'],r'uitspraak.?']
        for patern in patern_list:
            first_paragraph = patern.sub('',first_paragraph)
        return first_paragraph
    
    async def get_paragraphs_for_country(self,links_per_country_dict: dict, country_code : str)-> list:
        """
            Methode-coroutine gets the country code runs asynchronous get_first_paragraph coroutines and return list of first paragraphs for specific country
            :param: dict links_per_country_dict lost of links for country
            :param: str country_code 
            :return: list response, lists of first paragraphs for each leader
        """
        async with AsyncClient() as session:
            tasks = [asyncio.create_task(self.get_first_paragraph(link,session)) for link in links_per_country_dict[country_code]]
            response = await asyncio.gather(*tasks)
            print(response)
            return response
    
    def get_final_dict(self)-> dict:
        """
            Method runs all coroutines and builds a final dictonary
            :return: dict leaders_data dictionarie with leaders wikipedia short-bio list as a values and country codes as a keys.
        """
        for country in  self.get_countries_list():
            while True:
                self.leaders_data[country]  = self.run_as(self.get_paragraphs_for_country(self.run_as(self.get_leaders_for_countries_async()),country))
                if self.leaders_data[country]:
                     break
        return self.leaders_data
    
    def to_json_file(self, filepath : str)-> None:
        """
            Method creates json file with filepath name 
            :param: str filepath, the name of file
            :return: None
        """
        with open(filepath,mode='w',encoding='utf8') as write_file:
            json.dump(self.leaders_data,write_file,ensure_ascii=False)


