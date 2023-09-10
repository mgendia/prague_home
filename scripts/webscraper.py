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
        # soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        soup= BeautifulSoup(self.driver.execute_script("return document.documentElement.outerHTML"), 'lxml')
        unit_urls = [item.get('href') for item in soup.find_all('a',
                                                                class_= 'title',
                                                                attrs= {'href': re.compile('^/en/detail/')}
                                                                )
                    ]
        # for link in soup.find_all('span', class_='basic'):
        #     unit_urls.append(self.main_url + link.find('a').get('href'))
        return unit_urls

    def extract_units_details(self):
        '''loops through all the unit urls and extracts the unit details'''
        unit_urls = self.__get_units_url()
        unit_details = [['Address', 'unit_type', 'bedrooms',  'unit_description',
                        'rent_price', 'floor_num', 'usable_area','garage', 'balcony', 'terrace',
                        'furnished', 'elevator', 'energy_class','Shop', 'Playground', 'tram', 
                        'metro', 'bus', 'drugstore', 'medic','pictures']]
        
        for url in unit_urls:
            # self.driver.get(url)
            # time.sleep(5.0) #sleep to allow the page to load
            # soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            # soup= BeautifulSoup(self.driver.execute_script("return document.documentElement.outerHTML"), 'lxml')           
            req= requests.get(self.api_url + '/'+ url.split('/')[-1]).json()

            #Getting nearby locations lat and lon
            nearby= {i :[item for item in req.json()['poi'] if item['name'] == i]\
                for i in ['Shop', 'Playground', 'Tram', 'Metro', 'Bus', 'Drugstore', 'Medic']}
            shop= (nearby['Shop']['lat'], nearby['Shop']['lon'])\
                if nearby['Shop'] != [] else None
            playground= (nearby['Playground']['lat'], nearby['Playground']['lon'])\
                if nearby['Playground'] != [] else None
            tram= (nearby['Tram']['lat'], nearby['Tram']['lon'])\
                if nearby['Tram'] != [] else None
            metro= (nearby['Metro']['lat'], nearby['Metro']['lon'])\
                if nearby['Metro'] != [] else None
            bus= (nearby['Bus']['lat'], nearby['Bus']['lon'])\
                if nearby['Bus'] != [] else None
            drugstore= (nearby['Drugstore']['lat'], nearby['Drugstore']['lon'])\
                if nearby['Drugstore'] != [] else None
            medic= (nearby['Medic']['lat'], nearby['Medic']['lon'])\
                if nearby['Medic'] != [] else None

            #Extracting unit type and number of bedrooms
            # ad_title= soup.find_all('title', class_= 'ng-binding')[0].text.replace('\xa0', '')
            # if 'family house' in ad_title:
            #     unit_type= 'house'
            #     num_bedrooms= req.get('recommendations_data').get('room_count_cb')
            # elif ('apartment' in ad_title) | ('flat' in ad_title):
            #     unit_type= 'apartment'
            #     num_bedrooms= re.findall(r'(?<=en/detail/lease/flat/)([a-z0-9\-+]+)(?=/)', url)[0]
            # else:
            #     unit_type= 'other'
            #     num_bedrooms= None
            # address= re.findall(r'(?>\d+m², )(.+)(?= • Sreality.cz)', ad_title)

            ad_title= req['meta_description'].replace('\xa0', '')
            if 'family house' in ad_title:
                unit_type= 'house'
                num_bedrooms= req.get('recommendations_data').get('room_count_cb')
            elif ('apartment' in ad_title) | ('flat' in ad_title):
                unit_type= 'apartment'
                num_bedrooms= re.findall(r'(?<=en/detail/lease/flat/)([a-z0-9\-+]+)(?=/)', url)[0]
            else:
                unit_type= 'other'
                num_bedrooms= None
            address= re.findall(r'(?<= rent )([\w\s-]+)(?=;)', ad_title)

            #Get unit details           
            # unit_description= soup.find_all('div', class_= 'description ng-binding')[0].text
            
            # dictionary= dict()
            # for item in soup.find_all('li', class_= 'param ng-scope'):
            #     dictionary[item.find_all('label', class_='param-label ng-binding')[0].text[:-1]] =\
            #         item.find_all('span', class_= 'ng-binding ng-scope')[0].text.replace('\xa0', '')
            # rent_price= int(re.findall(r'\d+', dictionary['Total price'])[0])
            # try:
            #     floor_num= int(re.findall(r'\d+', dictionary['Floor'])[0])
            # except:
            #     floor_num= None
            # usable_area= int(re.findall(r'\d+', dictionary['Usable area'])[0])
            # energy_class= re.findall(r'\w+', dictionary['Energy Performance Rating'])[-1]

            unit_description= req['text']['value'].replace('\xa0', '')
            rent_price= req.get('recommendations_data').get('price_summary_czk')            
            garage= req.get('recommendations_data').get('garage')
            balcony= req.get('recommendations_data').get('balcony')
            terrace= req.get('recommendations_data').get('terrace')
            usable_area= [ item['value'] for item in req.json()['items']\
                        if item['name']== 'Usable area'][0]
            floor_num= re.findall(r'\w+',
                                [item['value'] for item in req.json()['items']\
                                if item['name']== 'Floor']
                                )[0]
            energy_class= re.findall(r'(?<=^Class )([a-zA-Z]{1})',
                                    [item['value'] for item in req.json()['items']\
                                    if item['name']== 'Energy Performance Rating']
                                    )[0]
            furnished= [item['value'] for item in req.json()['items'] if item['name']== 'Furnished']
            elevator= [item['value'] for item in req.json()['items'] if item['name']== 'Elevator']
            
            img_lst= req.get('_embedded').get('images')
            # img_soup= soup.find_all('div', class_= 'ob-c-carousel__item')
            # img_lst= []
            # for img in img_soup:
            #     if img.find('img').get('src') != None:
            #         img_lst.append(img.find('img').get('src'))
            #     else:
            #         img_lst.append([i for i in img.find_all('img') if i.get('src') != None][0].get('src'))
            pictures= [img_lst[i].get('_links').get('view').get('href') for i in range(len(img_lst))]
            unit_details.append([address, unit_type, num_bedrooms, unit_description, 
                                rent_price, floor_num, usable_area, garage, balcony, terrace,
                        furnished, elevator, energy_class, shop,
                                playground, tram, bus, metro, drugstore, medic,  pictures])
        return unit_details 