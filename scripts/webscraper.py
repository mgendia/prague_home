import selenium as sel
import pandas as pd
import re
import os
import requests
import time
from selenium import webdriver
from bs4 import BeautifulSoup

class Webscraper:
    def __init__(self, main_url, url):
        self.main_url = main_url
        self.url = url
        self.driver = webdriver.Chrome()
        self.driver.get(self.url)
        self.driver.implicitly_wait(10)
        self.api_url= 'https://www.sreality.cz/api/en/v2/estates'

    def __get_units_url(self):
        '''extracts the url of each unit from the target url and
        returns a list of urls'''
        soup= BeautifulSoup(self.driver.execute_script("return document.documentElement.outerHTML"), 'lxml')
        unit_urls = [item.get('href') for item in soup.find_all('a',
                                                                class_= 'title',
                                                                attrs= {'href': re.compile('^/en/detail/')}
                                                                )
                    ]
        return unit_urls

    def extract_units_details(self):
        '''loops through all the unit urls and extracts the unit details'''
        unit_urls = self.__get_units_url()
        unit_details = [['url', 'unit_id', 'Address', 'unit_type', 'bedrooms',  'unit_description',
                        'rent_price', 'floor_num', 'usable_area','garage', 'balcony', 'terrace',
                        'furnished', 'elevator', 'energy_class','Shop', 'Playground', 'tram', 
                        'metro', 'bus', 'drugstore', 'medic','pictures']]
        
        for url in unit_urls:         
            unit_id= url.split('/')[-1]
            req= requests.get(self.api_url + '/'+ unit_id).json()
            #Getting nearby locations lat and lon
            nearby= {i :[item for item in req['poi'] if item['name'] == i]\
                for i in ['Shop', 'Playground', 'Tram', 'Metro', 'Bus', 'Drugstore', 'Medic']}
            shop= (nearby.get('Shop')[0]['lat'], nearby.get('Shop')[0]['lon']) \
                if nearby.get('Shop') != [] else None
            playground= (nearby.get('Playground')[0]['lat'], nearby.get('Playground')[0]['lon']) \
                if nearby.get('Playground') != [] else None
            tram= (nearby.get('Tram')[0]['lat'], nearby.get('Tram')[0]['lon'])  \
                if nearby.get('Tram') != [] else None
            metro= (nearby.get('Metro')[0]['lat'], nearby.get('Metro')[0]['lon']) \
                if nearby.get('Metro') != [] else None
            bus= (nearby.get('Bus')[0]['lat'], nearby.get('Bus')[0]['lon'])\
                if nearby.get('Bus') != [] else None
            drugstore= (nearby.get('Drugstore')[0]['lat'], nearby.get('Drugstore')[0]['lon'])\
                if nearby.get('Drugstore') != [] else None
            medic= (nearby.get('Medic')[0]['lat'], nearby.get('Medic')[0]['lon'])\
                if nearby.get('Medic') != [] else None 
            ad_title= req['meta_description'].replace('\xa0', '')
            if 'Family house' in ad_title:
                unit_type= 'house'
                num_bedrooms= req.get('recommendations_data').get('room_count_cb')
            elif ('apartment' in ad_title) | ('flat' in ad_title):
                unit_type= 'apartment'
                num_bedrooms= re.findall(r'(?<=en/detail/lease/flat/)([a-z0-9\-+]+)(?=/)', url)[0]
                
            else:
                unit_type= 'other'
                num_bedrooms= None
            try:
                address= re.findall(r'(?<= rent )([\w\s-]+)(?=;)', ad_title)[0]
            except:
                address= re.findall(r'(?<= sale )([\w\s-]+)(?=;)', ad_title)[0]
            unit_description= req['text']['value'].replace('\xa0', '')
            rent_price= req.get('recommendations_data').get('price_summary_czk')            
            garage= req.get('recommendations_data').get('garage')
            balcony= req.get('recommendations_data').get('balcony')
            terrace= req.get('recommendations_data').get('terrace')
            usable_area= [ item['value'] for item in req['items']\
                        if item['name']== 'Usable area'][0]
            floor_num= [item['value'] for item in req['items']\
                                if item['name']== 'Floor']
            floor_num= re.findall(r'\w+', floor_num[0])[0] if floor_num != [] else None
            energy_class= [item['value'] for item in req['items']\
                        if item['name']== 'Energy Performance Rating']
            energy_class= re.findall(r'(?<=^Class )([a-zA-Z]{1})',
                                    energy_class[0])[0] if energy_class != [] else None
            for item in req['items']:
                if item['name']== 'Furnished':
                    furnished= item['value']
                elif item['name']== 'Elevator':
                    elevator= item['value']
            img_lst= req.get('_embedded').get('images')
            pictures= [img_lst[i].get('_links').get('view').get('href') for i in range(len(img_lst))]
            unit_details.append([url,unit_id, address, unit_type, num_bedrooms, unit_description, 
                                rent_price, floor_num, usable_area, garage, balcony, terrace,
                        furnished, elevator, energy_class, shop,
                                playground, tram, bus, metro, drugstore, medic,  pictures])
        return unit_details 