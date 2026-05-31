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
        with open(Path(r'../data/school_address.txt'), 'r', encoding='utf-8') as f:
            self.school_address= ast.literal_eval(f.read())

    def _get_home_location(self, address):
        '''returns the latitude and longitude of the address'''
        geocode_result = self.gmaps.geocode(address)
        if not geocode_result:
            return None
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
        if (type(origin) == pd.Series) and (type(destination) == pd.Series):
            journey_details_lst= []
            for origin_, destination_ in zip(origin, destination):                
                if (type(origin_) == tuple) and (type(destination_) == tuple):
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
            if (type(origin) == tuple) and (type(destination) == tuple):
                directions_result = self.__get_directions(origin= origin,
                                                        destination= destination,
                                                        mode= mode,
                                                        arrival_time= arrival_time)
                return self.__extract_journey_details(directions_result)
                
            else:   
                raise ValueError(f'journey_details: expected tuple origins/destinations, got {type(origin)}/{type(destination)}')
            
    def get_school_journey_details(self,
                                origin,
                                mode= 'transit',
                                arrival_time= datetime.strptime(
                                                    datetime.strftime(
                                                            datetime.today() + timedelta(days= (14 - datetime.today().weekday()) % 7)
                                                            , format= '%Y-%m-%d')+ ' 07:30:00 GMT',
                                                    '%Y-%m-%d %H:%M:%S %Z') + timedelta(hours= 2)):
        '''returns the total duration, total distance, and total walking time from origin to school'''
        
        return self.journey_details(origin= origin,
                                    destination= self.school_address,
                                    mode= mode,
                                    arrival_time=arrival_time)

    PLACE_TYPE_MAP = {
        'Shop':       'supermarket',
        'Playground': 'park',
        'tram':       'transit_station',
        'metro':      'subway_station',
        'bus':        'bus_station',
        'drugstore':  'pharmacy',
        'medic':      'hospital',
    }

    def get_nearest_poi(self, home_geo, category):
        '''Return (lat, lng) of the nearest Google Places result for a category,
        or None if unmapped or no results found.'''
        place_type = self.PLACE_TYPE_MAP.get(category)
        if not place_type or not isinstance(home_geo, tuple):
            return None
        results = self.gmaps.places_nearby(
            location=home_geo,
            rank_by='distance',
            type=place_type
        ).get('results', [])
        if not results:
            return None
        loc = results[0]['geometry']['location']
        return (loc['lat'], loc['lng'])

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
        
        