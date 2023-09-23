import googlemaps
import os
import math
import pandas as pd
import itertools
import ast
import pickle

from pathlib import Path
from datetime import time, datetime, timedelta




class Gmaps:
    def __init__(self):
        self.gmaps = googlemaps.Client(key=os.environ.get('PragueHouseGMAPKey'))
        self.school_address= ast.literal_eval(open(Path(r'../data/school_address.txt'), 'r').read())

    def _get_home_location(self, address):
        '''returns the latitude and longitude of the address'''
        geocode_result = self.gmaps.geocode(address)
        return tuple(geocode_result[0]['geometry']['location'].values())

    
    def __get_directions(self,
                        origin,
                        destination,
                        mode:str = 'transit',
                        arrival_time: datetime = None):
        '''returns the directions from origin to destination'''
        if arrival_time is None:
            directions_result = self.gmaps.directions(origin,
                                                    destination,
                                                    mode=mode)
        else:
            directions_result = self.gmaps.directions(origin,
                                                destination,
                                                mode= mode,
                                                arrival_time= arrival_time)
        return directions_result

    def __extract_journey_details(self, directions_result):
        '''returns the total duration, total distance, and total walking time from origin to destination'''
        duration= math.ceil(directions_result[0].get('legs')[0]['duration']['value'] /60)
        distance= directions_result[0]['legs'][0]['distance']['value']
        total_walking_time= math.ceil(sum([step['duration']['value']\
                                    for step in directions_result[0]['legs'][0]['steps']\
                                        if step['travel_mode'] == 'WALKING']) /60)
        return duration, distance, total_walking_time

    def journey_details(self, origin, destination, mode= 'transit', arrival_time= None):
        '''returns the total duration, total distance, and total walking time from origin to destination'''
        if (type(origin) == pd.Series)  & (type(destination) == pd.Series):
            journey_details_lst= []
            for origin_, destination_ in zip(origin, destination):                
                if (type(origin_) == tuple)  & (type(destination_) == tuple):
                    directions_result = self.__get_directions(origin= origin_,
                                                            destination= destination_,
                                                            mode= mode,
                                                            arrival_time= arrival_time)
                    journey_details_lst.append(self.__extract_journey_details(directions_result))
                else:
                    journey_details_lst.append((None, None, None))
                    
            dur, dist, walk_time= zip(*journey_details_lst)
            return dur, dist, walk_time
        else:
            if (type(origin) == tuple)  & (type(destination) == tuple):
                directions_result = self.__get_directions(origin= origin,
                                                        destination= destination,
                                                        mode= mode,
                                                        arrival_time= arrival_time)
                return self.__extract_journey_details(directions_result)
                
            else:   
                print('failing the else statement')
                print(type(origin))
                print(type(destination))
                return None, None, None
            
    def get_school_journey_details(self,
                                origin,
                                mode= 'transit',
                                arrival_time= datetime.strptime('2023-10-01 07:20:00 GMT',
                                                                    '%Y-%m-%d %H:%M:%S %Z') + timedelta(hours= 2)):
        '''returns the total duration, total distance, and total walking time from origin to school'''
        
        return self.journey_details(origin,
                                    self.school_address,
                                    mode= mode,
                                    arrival_time=arrival_time)

    def get_closest_crossfitbox(self,
                                origin,
                                mode:list= ['transit']):
        '''finds best crossfit box based on the shorted duration from origin
        return crossfit box name and journey details'''
        assert type(mode) == list, 'mode must be a list'
        assert len(mode) > 0, 'mode must have at least one element'
        assert type(origin) == tuple, 'origin must be a tuple'
        
        with open(Path(r'../data/crossfit.pkl'), 'rb') as f:
            crossfit= pickle.load(f)
        combination_lst= itertools.product(zip(crossfit.name, crossfit.geo), mode)
        
        dur_lst={f'{gym[0]}_{mode}': math.ceil(self.gmaps.directions(origin,
                                    gym[1], mode= mode)[0].get('legs')[0]['duration']['value'] /60)\
                                        for gym, mode in combination_lst}
        top_pick= sorted(dur_lst.items(), key= lambda item: item[1])[0]
        name, transit, duration= top_pick[0].split('_')[0], top_pick[0].split('_')[1], top_pick[1]
        return name, transit, duration
        
        