import pandas as pd

from pathlib import Path

#BUG: FIX THE SCORING BUG TO CAPTURE ONLY 1 SCORE FOR EACH CATEGORY
#TODO: EXTRACT THE VALUE OF EACH CATEGORY AS WELL AS THE SCORE
class Score:
    def __init__(self, 
                df:pd.DataFrame,
                nearby_places):
        self.data= df
        self.nearby_places= nearby_places

    def __get_score(self, row):
        '''returns the score of the row'''
        score_dict= dict()
        score = 0        
        try:
            if int(row['bedrooms'].split('+')[0]) > 2:
                score += 5
                score_dict['bedrooms'] = 5
        except:
            if int(row['bedrooms']) > 5:
                score += 5
                score_dict['bedrooms'] = 5
        if row['usable_area'] >= 100:
            score += 10
            score_dict['usable_area'] = 10
        elif row['usable_area'] >= 90:
            score += 5
            score_dict['usable_area'] = 5
        elif row['usable_area'] <= 70:
            score+= -10
            score_dict['usable_area'] = -10
        elif row['energy_class'] in ['A', 'B']:
            score += 10
            score_dict['energy_class'] = 10
        elif row['energy_class'] == 'C':
            score += 5
            score_dict['energy_class'] = 5
        elif row['energy_class'] == 'D':
            score += -5
            score_dict['energy_class'] = -5
        for place in self.nearby_places:
            if row[f'{place}_walking_dur'] <= 5:
                score += 10
                score_dict[f'{place}'] = row[f'{place}_walking_dur']                
            elif (row[f'{place}_walking_dur'] <= 10) & (row[f'{place}_walking_dur'] > 5):
                score += 3
                score_dict[f'{place}'] = row[f'{place}_walking_dur']
            elif (row[f'{place}_walking_dur'] <= 20) & (row[f'{place}_walking_dur'] > 10):
                score+= -3
                score_dict[f'{place}'] = row[f'{place}_walking_dur']
            elif row[f'{place}_walking_dur'] > 20:
                score+= -10
                score_dict[f'{place}'] = row[f'{place}_walking_dur']
        if row['school_transit_dur'] < row['school_walking_dur']:
            if (row['school_transit_dur'] <= 15) & (row['school_transit_twalk'] <= 5):
                score += 10
                score_dict['School'] = 10
            elif (row['school_transit_dur'] <= 20) & (row['school_transit_dur'] >15) & (row['school_transit_twalk'] <= 5):
                score += 8
                score_dict['School'] = 8
            elif (row['school_transit_dur'] <= 25) & (row['school_transit_dur'] > 20) & (row['school_transit_twalk'] <= 10):
                score += 6
                score_dict['School'] = 6
            elif (row['school_transit_dur'] <= 30) & (row['school_transit_dur'] > 25) & (row['school_transit_twalk'] <= 10):
                score += 4
                score_dict['School'] = 4
            elif (row['school_transit_dur'] <= 35) & (row['school_transit_dur'] > 30) & (row['school_transit_twalk'] <= 10):
                score += -5
                score_dict['School'] = -5
            elif (row['school_transit_dur'] >= 35) :
                score += -50
                score_dict['School'] = -50
        elif row['school_walking_dur'] < row['school_transit_dur']:
            if row['school_walking_dur'] <= 5:
                score += 10
                score_dict['School'] = 10
            elif (row['school_walking_dur'] <= 10) & (row['school_walking_twalk'] > 5):
                score += 8
                score_dict['School'] = 8
            elif (row['school_walking_dur'] <= 15) & (row['school_walking_twalk'] > 10):
                score += 6
                score_dict['School'] = 6
            elif (row['school_walking_dur'] <= 20) & (row['school_walking_twalk'] > 15):
                score += 4
                score_dict['School'] = 4
        if row['crossfit_mode'] == 'walking':
            if row['crossfit_dur'] <= 10:
                score += 5
                score_dict['Crossfit'] = 5
            elif (row['crossfit_dur'] <= 15) & (row['crossfit_dur'] > 10):
                score += 3
                score_dict['Crossfit'] = 3
            elif (row['crossfit_dur'] <= 20) & (row['crossfit_dur'] > 15):
                score += 2
                score_dict['Crossfit'] = 2
            elif (row['crossfit_dur'] <= 25) & (row['crossfit_dur'] > 20):
                score += 1
                score_dict['Crossfit'] = 1
        elif row['crossfit_mode'] == 'transit':
            if row['crossfit_dur'] <= 20:
                score += 5
                score_dict['Crossfit'] = 5
            elif (row['crossfit_dur'] <= 25) & (row['crossfit_dur'] > 20):
                score += 3
                score_dict['Crossfit'] = 3
            elif (row['crossfit_dur'] <= 30) & (row['crossfit_dur'] > 25):
                score += 2
                score_dict['Crossfit'] = 2
            elif row['crossfit_dur'] > 30:
                score += -5
                score_dict['Crossfit'] = -5
        return score, score_dict

    def get_score(self):
        '''returns the score of the dataframe'''
        self.data['score'], self.data['score_dict']= zip(*self.data.apply(self.__get_score, axis=1))
        # return self.data