import numpy as np
import re
import logging
import requests
import math
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from tqdm import tqdm


class Webscraper:
    def __init__(self, api_url, url):
        self.api_url = api_url
        self.url = url
        

    def get_units_urls(self):
        '''extracts the url of each unit from the target url and
        returns a list of urls'''
        # logging.basicConfig(level=logging.INFO)
        options = Options()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--headless')
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options) 
        self.driver.implicitly_wait(10)        
        self.driver.get(self.url)
        soup= BeautifulSoup(self.driver.execute_script("return document.documentElement.outerHTML"), 'lxml')
        try:
            num_pages= math.ceil(int(soup.find_all(class_= 'numero ng-binding')[-1].text.replace('\xa0', '')) / 20)
        except:
            num_pages= 1
        # unit_urls = [item.get('href') for item in soup.find_all('a',
        #                                                         class_= 'title',
        #                                                         attrs= {'href': re.compile('^/en/detail/')}
        #                                                         )
        #             ]
        unit_urls= []
        for i in tqdm(range(1, num_pages+1)):
            url = self.url + '&page=' + str(i)
            self.driver.get(url)
            sleep(np.random.uniform(2.0, 2.5))
            innerHTML= self.driver.execute_script("return document.body.innerHTML")
            soup= BeautifulSoup(innerHTML, 'lxml')
            unit_urls.append([item.get('href') for item in soup.find_all('a',
                                                                        class_= 'title',
                                                                        attrs= {'href': re.compile('^/en/detail/')}
                                                                        )
                            ])
        unit_urls= list(set([link for lst in unit_urls for link in lst]))
        # self.driver.close()
        return unit_urls

    def extract_units_details(self, url_list: list):
        '''loops through all the unit urls and extracts the unit details'''
        # unit_urls = self.get_units_urls()
        unit_details = [['url', 'unit_id', 'Address', 'unit_type', 'bedrooms',  'unit_description',
                        'rent_price', 'floor_num', 'usable_area','garage', 'balcony', 'terrace',
                        'furnished', 'elevator', 'energy_class','Shop', 'Playground', 'tram', 
                        'metro', 'bus', 'drugstore', 'medic','pictures']]
        
        for url in tqdm(url_list):         
            unit_id= url.split('/')[-1]
            req= requests.get(self.api_url + '/'+ unit_id.strip()).json()
            #Adding unit url
            unit_link= self.api_url+ url
            #Getting nearby locations lat and lon
            nearby= {item.get('name'): (item.get('lat'), item.get('lon')) for item in req.get('poi')}
            shop= nearby.get('Shop')
            playground= nearby.get('Playground')
            tram= nearby.get('Tram')
            metro= nearby.get('Metro')
            bus= nearby.get('Bus Public Transport')
            drugstore= nearby.get('Drugstore')
            medic= nearby.get('Medic')
            #Getting the unit type and number of bedrooms
            ad_title= req['meta_description'].replace('\xa0', '').lower()
            if ('family house' in ad_title) | ('villa' in ad_title) |\
                ('villas' in ad_title)| ('house' in ad_title):
                unit_type= 'house'
                num_bedrooms= req.get('recommendations_data').get('room_count_cb')
            elif ('apartment' in url) | ('flat' in url):
                unit_type= 'apartment'
                num_bedrooms= re.findall(r'(?<=en/detail/lease/flat/)([a-z0-9\-+]+)(?=/)', url)[0]
            else:
                unit_type= 'other'
                num_bedrooms= None
            address= req['seo']['locality']
            unit_description= req['text']['value'].replace('\xa0', '')
            rent_price= req.get('recommendations_data').get('price_summary_czk')            
            garage= req.get('recommendations_data').get('garage')
            balcony= req.get('recommendations_data').get('balcony')
            terrace= req.get('recommendations_data').get('terrace')
            usable_area= [ item['value'] for item in req['items']\
                        if item['name']== 'Usable area']
            floor_num= [re.findall(r'\w+', item['value']) for item in req['items']\
                                if item['name']== 'Floor']
            energy_class= [re.findall(r'(?<=^Class )([a-zA-Z]{1})',
                                    item['value']) for item in req['items']\
                        if item['name']== 'Energy Performance Rating']
            
            #Getting the furnished and elevator details
            furnished =[item['value']  for item in req['items'] if item['name'] == 'Furnished']           
            elevator =[item['value']  for item in req['items'] if item['name'] == 'Elevator']
            
            #Getting the pictures
            img_lst= req.get('_embedded').get('images')
            pictures= [img_lst[i].get('_links').get('view').get('href') for i in range(len(img_lst))]
            unit_details.append([unit_link,unit_id, address, unit_type, num_bedrooms, unit_description, 
                                rent_price, floor_num, usable_area, garage, balcony, terrace,
                                furnished, elevator, energy_class, shop,
                                playground, tram,  metro, bus, drugstore, medic,  pictures])
        return unit_details 