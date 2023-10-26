import pandas as pd

from pathlib import Path

#TODO: TEST IF THE SCORING CAPTURES ONLY 1 SCORE FOR EACH CATEGORY
class Score:
    def __init__(self, 
                df:pd.DataFrame,
                nearby_places):
        self.data= df
        self.nearby_places= nearby_places

    def __get_school_weighted_score(self, row, weight: float=0.5):
        '''returns the weighted score for the school travel time'''
        score_dict= dict()
        if row['school_transit_dur'] < row['school_walking_dur']:
            if (row['school_transit_dur'] <= 15) & (row['school_transit_twalk'] <= 5):
                score = 100 * weight
                score_dict['School'] = row['school_transit_dur']
                score_dict['School_score']= score
            elif (row['school_transit_dur'] <= 20) & (row['school_transit_dur'] >15) & (row['school_transit_twalk'] <= 5):
                score = 80 * weight 
                score_dict['School'] = row['school_transit_dur']
                score_dict['School_score']= score
            elif (row['school_transit_dur'] <= 25) & (row['school_transit_dur'] > 20) & (row['school_transit_twalk'] <= 10):
                score = 60 * weight
                score_dict['School'] = row['school_transit_dur']
                score_dict['School_score']= score
            elif (row['school_transit_dur'] <= 30) & (row['school_transit_dur'] > 25) & (row['school_transit_twalk'] <= 10):
                score = 40 * weight
                score_dict['School'] = row['school_transit_dur']
                score_dict['School_score']= score
            elif (row['school_transit_dur'] <= 35) & (row['school_transit_dur'] > 30) & (row['school_transit_twalk'] <= 10):
                score = 0 * weight
                score_dict['School'] = row['school_transit_dur']
                score_dict['School_score']= score
            else:
                score = -50 * weight
                score_dict['School'] = row['school_transit_dur']
                score_dict['School_score']= score
                
        elif row['school_walking_dur'] <= row['school_transit_dur']:
            if row['school_walking_dur'] <= 10:
                score = 100 * weight
                score_dict['School'] = row['school_walking_dur']
                score_dict['School_score']= score
            elif (row['school_walking_dur'] <= 15) & (row['school_walking_twalk'] > 10):
                score = 80 * weight
                score_dict['School'] = row['school_walking_dur']
                score_dict['School_score']= score
            elif (row['school_walking_dur'] <= 20) & (row['school_walking_twalk'] > 15):
                score = 60 * weight
                score_dict['School'] = row['school_walking_dur']
                score_dict['School_score']= score
            elif (row['school_walking_dur'] <= 25) & (row['school_walking_twalk'] > 20):
                score = 40 * weight
                score_dict['School'] = row['school_walking_dur']
                score_dict['School_score']= score
            else:
                score= 0 * weight
                score_dict['School'] = row['school_walking_dur']
                score_dict['School_score']= score
        return score, score_dict
    
    def __get_crossfit_weighted_score(self, row, weight: float=0.05):
        '''returns the weighted score for the crossfit travel time'''
        score_dict= dict()
        if row['crossfit_mode'] == 'walking':
            if row['crossfit_dur'] <= 10:
                score = 100 * weight
                score_dict['Crossfit'] = row['crossfit_dur']
                score_dict['Crossfit_score']= score
            elif (row['crossfit_dur'] <= 15) & (row['crossfit_dur'] > 10):
                score = 80 * weight
                score_dict['Crossfit'] = row['crossfit_dur']
                score_dict['Crossfit_score']= score
            elif (row['crossfit_dur'] <= 20) & (row['crossfit_dur'] > 15):
                score = 40 * weight
                score_dict['Crossfit'] = row['crossfit_dur']
                score_dict['Crossfit_score']= score
            elif (row['crossfit_dur'] <= 25) & (row['crossfit_dur'] > 20):
                score = 20 * weight
                score_dict['Crossfit'] = row['crossfit_dur']
                score_dict['Crossfit_score']= score
            else:
                score = 0 * weight
                score_dict['Crossfit'] = row['crossfit_dur']
                score_dict['Crossfit_score']= score
                
        elif row['crossfit_mode'] == 'transit':
            if row['crossfit_dur'] <= 15:
                score = 100 * weight
                score_dict['Crossfit'] = row['crossfit_dur']
                score_dict['Crossfit_score']= score
            elif (row['crossfit_dur'] <= 20) & (row['crossfit_dur'] > 15):
                score = 80 * weight
                score_dict['Crossfit'] = row['crossfit_dur']
                score_dict['Crossfit_score']= score
            elif (row['crossfit_dur'] <= 25) & (row['crossfit_dur'] > 20):
                score = 60 * weight
                score_dict['Crossfit'] = row['crossfit_dur']
                score_dict['Crossfit_score']= score
            elif (row['crossfit_dur'] <= 30) & (row['crossfit_dur'] > 25):
                score = 40 * weight
                score_dict['Crossfit'] = row['crossfit_dur']
                score_dict['Crossfit_score']= score
            else:
                score = 0 * weight
                score_dict['Crossfit'] = row['crossfit_dur']
                score_dict['Crossfit_score']= score
        return score, score_dict

    def __get_nearby_places_weighted_score(self, row, weight: float=0.25):
        '''returns the weighted average score for the nearby places'''
        score_lst= []
        score_dict= dict()
        num_places= len(self.nearby_places)
        for place in self.nearby_places:
            if row[f'{place}_walking_dur'] <= 5:
                score = 100 * weight /num_places
                score_dict[f'{place}'] = row[f'{place}_walking_dur']
                score_dict[f'{place}_score']= score
                score_lst.append(score)                
            elif (row[f'{place}_walking_dur'] <= 10) & (row[f'{place}_walking_dur'] > 5):
                score = 80 * weight /num_places
                score_dict[f'{place}'] = row[f'{place}_walking_dur']
                score_dict[f'{place}_score']= score
                score_lst.append(score)
            elif (row[f'{place}_walking_dur'] <= 15) & (row[f'{place}_walking_dur'] > 10):
                score = 60 * weight /num_places
                score_dict[f'{place}'] = row[f'{place}_walking_dur']
                score_dict[f'{place}_score']= score
                score_lst.append(score)
            elif (row[f'{place}_walking_dur'] <= 20) & (row[f'{place}_walking_dur'] > 15):
                score = 40 * weight /num_places
                score_dict[f'{place}'] = row[f'{place}_walking_dur']
                score_dict[f'{place}_score']= score
                score_lst.append(score)
            else:
                score = 0 * weight /num_places
                score_dict[f'{place}'] = row[f'{place}_walking_dur']
                score_dict[f'{place}_score']= score
                score_lst.append(score)
        avg_score= sum(score_lst) 
        return avg_score, score_dict

    
    def __get_unit_details_weighted_score(self, row, weight:float= 0.2):
        '''returns the weighted average score for the unit details'''
        score_dict= dict()
        score_lst= []
        num_features= 3
        try:
            if int(row['bedrooms'].split('+')[0]) > 2:
                score= 100 * weight /num_features
                score_dict['bedrooms'] = int(row['bedrooms'].split('+')[0])
                score_dict['bedrooms_score']= score
                score_lst.append(score)
            else:
                score= 50 * weight /num_features
                score_dict['bedrooms'] = int(row['bedrooms'].split('+')[0])
                score_dict['bedrooms_score']= score
                score_lst.append(score)
        except:
            if int(row['bedrooms']) > 2:
                score= 100 * weight /num_features
                score_dict['bedrooms'] = int(row['bedrooms'])
                score_dict['bedrooms_score']= score
                score_lst.append(score)
            else:
                score= 50 * weight /num_features
                score_dict['bedrooms'] = int(row['bedrooms'])
                score_dict['bedrooms_score']= score
                score_lst.append(score)
        if row['usable_area'] >= 120:
            score= 100 * weight /num_features
            score_dict['usable_area'] = row['usable_area']
            score_dict['usable_area_score']= score
            score_lst.append(score)
        elif (row['usable_area'] < 120) & (row['usable_area'] >= 100):
            score= 80 * weight /num_features
            score_dict['usable_area'] = row['usable_area']
            score_dict['usable_area_score']= score
            score_lst.append(score)
        elif (row['usable_area'] < 100) & (row['usable_area'] >= 90):
            score= 60 * weight /num_features
            score_dict['usable_area'] = row['usable_area']
            score_dict['usable_area_score']= score
            score_lst.append(score)
        elif (row['usable_area'] < 90) & (row['usable_area'] >= 80):
            score= 40 * weight /num_features
            score_dict['usable_area'] = row['usable_area']
            score_dict['usable_area_score']= score
            score_lst.append(score)
        elif row['usable_area'] < 80:
            score= 0 * weight /num_features
            score_dict['usable_area'] = row['usable_area']
            score_dict['usable_area_score']= score 
            score_lst.append(score)           
        elif row['energy_class'] in ['A', 'B']:
            score= 100 * weight /num_features
            score_dict['energy_class'] = row['energy_class']
            score_dict['energy_class_score']= score
            score_lst.append(score)
        elif row['energy_class'] == 'C':
            score= 80 * weight /num_features
            score_dict['energy_class'] = row['energy_class']
            score_dict['energy_class_score']= score
            score_lst.append(score)
        elif row['energy_class'] == 'D':
            score= 40 * weight /num_features
            score_dict['energy_class'] = row['energy_class']
            score_dict['energy_class_score']= score
            score_lst.append(score)
        elif row['energy_class'] not in ['A', 'B', 'C', 'D']:
            score= 0 * weight /num_features
            score_dict['energy_class'] = row['energy_class']
            score_dict['energy_class_score']= score
            score_lst.append(score)
        avg_score= sum(score_lst)
        return avg_score, score_dict

    def __get_score(self, row):
        '''returns the score for each unit'''
        score_dict= dict()
        score= 0
        
        school_score, school_score_dict= self.__get_school_weighted_score(row)
        score += school_score        
        score_dict.update(school_score_dict)
        
        crossfit_score, crossfit_score_dict= self.__get_crossfit_weighted_score(row)
        score += crossfit_score        
        score_dict.update(crossfit_score_dict)
        
        nearby_places_score, nearby_places_score_dict= self.__get_nearby_places_weighted_score(row)
        score += nearby_places_score
        score_dict.update(nearby_places_score_dict)
        
        unit_details_score, unit_details_score_dict= self.__get_unit_details_weighted_score(row)
        score += unit_details_score
        score_dict.update(unit_details_score_dict)
        
        return score, score_dict   
        
        

    def get_score(self):
        '''returns the score of the dataframe'''
        self.data['score'], self.data['score_dict']= zip(*self.data.apply(self.__get_score, axis=1))
        # return self.data