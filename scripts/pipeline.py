import pandas as pd
import numpy as np
import math
import pickle

from pathlib import Path
from webscraper import Webscraper
from gmaps import Gmaps
from score import Score

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
        return unique_links, links


    def update_data(self, mode:list= ['transit', 'walking']):
        '''updates the dataframe with the new data'''
        # self.__check_df_params()
        unique_links, total_links= self.__get_unique_links()
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
                self.new_data['score'], self.new_data['score_dict']= np.nan, np.nan
                self.data= pd.concat([self.data, self.new_data], ignore_index= True, axis=0)
                self.data= self.data.loc[self.data['url'].isin(total_links)]
        print(f'{len(unique_links)} new links updated')
        

    def preprocess_data(self):
        '''preprocesses the data'''
        nearby_places_cols = [col for col in self.data.columns if ('_dur' in col) | ('_dist' in col) | ('_twalk' in col)]
        self.data[nearby_places_cols] = self.data[nearby_places_cols].fillna(0)
        self.data['floor_num'] = self.data['floor_num'].fillna(0)
        self.data[['usable_area', 'floor_num']]= self.data[['usable_area', 'floor_num']].apply(pd.to_numeric, errors='coerce')
        
    def score_units(self):
        '''scores the units'''
        score= Score(self.data, self.nearby_places)
        score.get_score()
        
    def save_data(self):
        '''saves the data to a pickle file'''
        with open(self.data_file_path, 'wb') as f:
            pickle.dump(self.data, f)
        # self.data.to_pickle(self.data_file_path)
        

if __name__ == '__main__':
    with open('../data/search_urls.txt', 'r') as f:
        search_urls= f.read().split('\n')
    for url in search_urls:
        pipeline= Pipeline(url= url,
                            api_url= 'https://www.sreality.cz/api/cs/v2/estates',
                            data_file_path= Path(r'../data/data.pkl'),
                            nearby_places_path= Path(r'../data/nearby_places.txt'))
        print('updating data...')
        pipeline.update_data()
        print('preprocessing data...')
        pipeline.preprocess_data()
        print('scoring units...')
        pipeline.score_units()
        print('saving data...')
        pipeline.save_data()
        print('data saved!')