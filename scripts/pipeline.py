import pandas as pd
import numpy as np
import math
import pickle

from pathlib import Path
from webscraper import Webscraper
from gmaps import Gmaps

class Pipeline:
    def __init__(self,
                url,
                api_url,
                data_file_path:str= Path(r'../data/data.pkl'),
                nearby_places_path:str= Path(r'../data/nearby_places.txt')):
        self.url= url
        self.api_url= api_url
        self.data_file_path= data_file_path
        if Path(data_file_path).is_file():
            with open(data_file_path, 'rb') as f:
                self.data= pickle.load(f)
            # self.data= pd.read_pickle(data_file_path)
        else:
            self.data= pd.DataFrame()
        self.new_data= None
        self.scrapper= Webscraper(self.api_url, self.url)
        self.gmaps= Gmaps()
        with open(nearby_places_path, 'r') as f:
            nearby_places= f.read().split(',')
        self.nearby_places= nearby_places

    def __get_unique_links(self):
        links= self.scrapper.get_units_urls()
        unique_links= list(set(links) - set(self.data.url)) if self.data.shape[0] > 0 else links
        return unique_links

    # def __check_df_params(self):
    #     '''checks if the dataframe has the required columns before concatenating the old data'''
    #     if not all(item in self.data.columns for item in ['url', 'unit_id', 'Address', 'unit_type', 'bedrooms',  'unit_description',
    #                     'rent_price', 'floor_num', 'usable_area','garage', 'balcony', 'terrace',
    #                     'furnished', 'elevator', 'energy_class','Shop', 'Playground', 'tram', 
    #                     'metro', 'bus', 'drugstore', 'medic','pictures','Shop_walk_time',
    #                     'Shop_walk_dist','Shop_walk_dur','Shop_transit_dur','Shop_transit_dist',
    #                     'Shop_transit_twalk', 'Playground_walk_dur','Playground_walk_dist', 'Playground_transit_dur',
    #                     'Playground_transit_dist', 'Playground_transit_twalk', 'tram_walk_dur', 'tram_walk_dist',
    #                     'tram_transit_dur','tram_transit_dist', 'tram_transit_twalk', 'metro_walk_dur',
    #                     'metro_walk_dist', 'metro_transit_dur', 'metro_transit_dist','metro_transit_twalk',
    #                     'bus_walk_dur','bus_walk_dist','bus_transit_dur','bus_transit_dist',
    #                     'bus_transit_twalk','drugstore_walk_dur', 'drugstore_walk_dist',
    #                     'drugstore_transit_dur','drugstore_transit_dist', 'drugstore_transit_twalk',
    #                     'medic_walk_dur','medic_walk_dist', 'medic_transit_dur', 'medic_transit_dist',
    #                     'medic_transit_twalk', 'school_transit_dur', 'school_dist','school_transit_twalk',
    #                     'school_walk_dur', 'school_walk_twalk', 'crossfit_name', 'crossfit_mode', 'crossfit_dur']):
    #         raise Exception('The dataframe does not have the required columns')

    def update_data(self, mode:list= ['transit', 'walking']):
        '''updates the dataframe with the new data'''
        # self.__check_df_params()
        unique_links= self.__get_unique_links()
        if len(unique_links) == 0:
            print('No new units to update')
        else:
            details= self.scrapper.extract_units_details(unique_links)
            self.new_data= pd.DataFrame(details[1:], columns= details[0])
            self.new_data.insert(self.new_data.columns.get_loc('Address')+1, 'home_geo',
                            self.new_data.Address.map(self.gmaps._get_home_location))
            #adding the nearby journey details
            for col in self.nearby_places:
                for m in mode:
                    if m == 'tranist':
                        self.new_data[f'{col}_{m}_dur'], self.new_data[f'{col}_{m}_dist'], self.new_data[f'{col}_{m}_twalk']=\
                            self.gmaps.journey_details(self.home_geo,
                                                self.new_data.col,
                                                mode= m)
                    else:
                        self.new_data[f'{col}_{m}_dur'], self.new_data[f'{col}_{m}_dist'],_=\
                            self.gmaps.journey_details(self.new_data.home_geo,
                                                self.new_data[col],
                                                mode= m)
            #adding the school journey details
            self.new_data= pd.concat([self.new_data, pd.concat([self.new_data.apply(lambda x: pd.Series(self.gmaps.get_school_journey_details(x['home_geo'],
                                                                                                mode=m),
                                                            index=[f'school_{m}_dur',
                                                                f'school_{m}_dist',
                                                                f'school_{m}_twalk']), 
                                                                        axis=1) for m in mode],
                                                    axis=1)],
                                axis=1)
            #adding the nearest crossfit box and it's journey details
            self.new_data= pd.concat([self.new_data, self.new_data.apply(lambda x: pd.Series(self.gmaps.get_closest_crossfitbox(x['home_geo']), index= ['crossfit_name',
                                                                                                                                            'crossfit_mode',
                                                                                                                                            'crossfit_dur']),
                                                            axis= 1)],
                                axis=1)
            if len(self.data) == 0:
                self.data= self.new_data
            else:
                self.data= pd.concat([self.data, self.new_data], ignore_index= True)
            self.data.to_pickle(self.data_file_path)
            print(f'{len(unique_links)} new links updated')

if __name__ == '__main__':
    user_url= input('Enter search Url: ')
    pipeline= Pipeline(url= user_url,
                        api_url= 'https://www.sreality.cz/api/cs/v2/estates',
                        data_file_path= Path(r'../data/data.pkl'),
                        nearby_places_path= Path(r'../data/nearby_places.txt'))
    pipeline.update_data()