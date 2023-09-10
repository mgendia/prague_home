import googlemaps
import os

from datetime import time, datetime, timedelta


class gmaps:
    def __init__(self,
                arrival_time:time, 
                mode:str='transit'):
        self.gmaps = googlemaps.Client(key=os.environ.get('PragueHouseGMAPKey'))
        self.school_address= open('..\data\school_address.txt', 'r').read()
        self.arrival_time= arrival_time
        self.mode= mode

    def __get_directions(self, origin, destination):
        '''returns the directions from origin to destination'''
        directions_result = self.gmaps.directions(origin,
                                                destination,
                                                mode=self.mode,
                                                arrival_time=self.arrival_time)
        return directions_result

    def journey_details(self, origin, destination):
        '''returns the total duration, total distance, and total walking time from origin to destination'''
        directions_result = self.__get_directions(origin, destination)
        duration= directions_result[0]['legs'][0]['duration']['text']
        distance= directions_result[0]['legs'][0]['distance']['text']
        total_walking_time= sum([int(step['duration']['text'].split(' ')[0])\
            for step in directions_result[0]['legs'][0]['steps']\
                if step['travel_mode'] == 'WALKING'])
        return duration, distance, total_walking_time