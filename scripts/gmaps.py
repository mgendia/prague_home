import googlemaps
import os
import math
import pandas as pd
import itertools
import ast

from datetime import time, datetime, timedelta




class gmaps:
    def __init__(self):
        self.gmaps = googlemaps.Client(key=os.environ.get('PragueHouseGMAPKey'))
        self.school_address= ast.literal_eval(open('..\data\school_address.txt', 'r').read())

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
        if type(origin)  | type(destination) == pd.Series:
            journey_details_lst= []
            for origin_, destination_ in zip(origin, destination):                
                if type(origin_)  | type(destination_) != tuple:
                    print(f'origin_ type: {type(origin_)}')
                    print(f'destination_ type: {type(destination_)}')
                    journey_details_lst.append((None, None, None))
                else:
                    directions_result = self.__get_directions(origin= origin_,
                                                            destination= destination_,
                                                            mode= mode,
                                                            arrival_time= arrival_time)
                    journey_details_lst.append(self.__extract_journey_details(directions_result))
            dur, dist, walk_time= zip(*journey_details_lst)
            return dur, dist, walk_time
        else:
            if type(origin)  | type(destination) != tuple:
                return None, None, None
            else:   
                directions_result = self.__get_directions(origin= origin_,
                                                        destination= destination_,
                                                        mode= mode,
                                                        arrival_time= arrival_time)
                return self.__extract_journey_details(directions_result)
            
    def get_school_journey_details(self,
                                origin,
                                mode= 'transit',
                                arrival_time= datetime.strptime('2023-10-01 07:20:00 GMT',
                                                                    '%Y-%m-%d %H:%M:%S %Z') + timedelta(hours= 2)):
        '''returns the total duration, total distance, and total walking time from origin to school'''
        return self.journey_details(origin,
                                    pd.Series(itertools.repeat(self.school_address, len(origin))),
                                    mode= mode,
                                    arrival_time=arrival_time)