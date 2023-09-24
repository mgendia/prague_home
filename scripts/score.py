import pandas as pd

from pathlib import Path


class Score:
    def __init__(self, 
                df:pd.DataFrame,
                nearby_places):
        self.data= df
        self.nearby_places= nearby_places

    def __get_score(self, row):
        '''returns the score of the row'''
        score = 0
        try:
            if int(row['bedrooms'].split('+')[0]) > 2:
                score += 2
        except:
            if int(row['bedrooms']) > 2:
                score += 2
        if row['usable_area'] >= 95:
            score += 10
        if row['usable_area'] >= 80:
            score += 5
        if row['energy_class'] in ['A', 'B']:
            score += 1
        if row['energy_class'] == 'C':
            score += 2
        if row['energy_class'] == 'D':
            score += 1
        for place in self.nearby_places:
            if row[f'{place}_walking_dur'] <= 10:
                score += 3
            if row[f'{place}_walking_dur'] <= 15:
                score += 1
        if row['school_transit_dur'] < row['school_walking_dur']:
            if (row['school_transit_dur'] <= 15) & (row['school_transit_twalk'] <= 5):
                score += 10
            if (row['school_transit_dur'] <= 20) & (row['school_transit_twalk'] <= 5):
                score += 8
            if (row['school_transit_dur'] <= 25) & (row['school_transit_twalk'] <= 10):
                score += 6
            if (row['school_transit_dur'] <= 30) & (row['school_transit_twalk'] <= 10):
                score += 4
            if (row['school_transit_dur'] <= 35) & (row['school_transit_twalk'] <= 10):
                score += 2
            if (row['school_transit_dur'] >= 35) :
                score -= 10
        if row['school_walking_dur'] < row['school_transit_dur']:
            if row['school_walking_dur'] <= 5:
                score += 10
            if row['school_walking_dur'] <= 10:
                score += 8
            if row['school_walking_dur'] <= 15:
                score += 6
            if row['school_walking_dur'] <= 20:
                score += 4
        if row['crossfit_mode'] == 'walking':
            if row['crossfit_dur'] <= 10:
                score += 5
            if row['crossfit_dur'] <= 15:
                score += 3
            if row['crossfit_dur'] <= 20:
                score += 2
            if row['crossfit_dur'] <= 25:
                score += 1
        if row['crossfit_mode'] == 'transit':
            if row['crossfit_dur'] <= 20:
                score += 5
            if row['crossfit_dur'] <= 25:
                score += 3
            if row['crossfit_dur'] <= 30:
                score += 2
            if row['crossfit_dur'] <= 35:
                score += 1
        return score

    def get_score(self):
        '''returns the score of the dataframe'''
        self.data['score']= self.data.apply(self.__get_score, axis=1)
        return self.data