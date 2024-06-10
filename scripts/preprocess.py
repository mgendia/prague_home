import pandas as pd
import numpy as np
import re


class Preprocess:
    def __init__(self, data: pd.DataFrame):
        self.data= data


    def __get_lst_content(self, lst: list):
        '''extracts and returns the content from a list, nested list, and empty list'''
        while type(lst) == list:
            if len(lst) >0:
                lst= lst[0]
            else:
                lst= None
        return lst

    def clean_lst_columns(self, col_lst: list):
        '''cleans the columns with list values'''
        for col in col_lst:
            self.data[col]= self.data[col].map(self.__get_lst_content)

    def clean_data_format(self):
        '''fix the data format of specific columns'''
        nearby_places_cols = [col for col in self.data.columns if ('_dur' in col) | ('_dist' in col) | ('_twalk' in col)]
        self.data[nearby_places_cols] = self.data[nearby_places_cols].fillna(0)
        self.data['floor_num'] = self.data['floor_num'].fillna(0)
        self.data[['usable_area', 'floor_num']]= self.data[['usable_area', 'floor_num']].apply(pd.to_numeric, errors='coerce')