import pickle
import re
import os
import ast
import googlemaps
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go



import dash_bootstrap_components as dbc

from dash import Dash, dcc, html, dash_table, Input, Output, State
from pathlib import Path


from pipeline import Pipeline


#TODO: Remove after adding to pipeline or webscrapping
main_url= 'https://www.sreality.cz'

#getting secret keys for APIs
mapbox_access_token = os.environ.get('MPBOX_PUBLIC_KEY')
gmap_access_token= os.environ.get('PragueHouseGMAPKey')
#reference example for flex layout using Dash Boostrapping
#https://community.plotly.com/t/dash-bootstrap-components-and-flexbox/40816/2
app= Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

########DATA########
with open(Path(r'../data/data.pkl'), 'rb') as f:
    df= pickle.load(f)
top_units_df= df.sort_values(by= ['score', 'rent_price'],
                            ascending= [False, True])\
                                .loc[:, ['url','score', 'unit_type', 'Address', 'rent_price',
                                        'bedrooms','school_transit_dur','school_transit_twalk','usable_area', 'floor_num', 'garage',
                                        'balcony', 'terrace','furnished', 'elevator', 'energy_class']]\
                                    .rename(columns= {'unit_type': 'Unit Type',
                                                    'rent_price': 'Rent Price',
                                                    'score': 'Score',
                                                    'bedrooms': 'Bedrooms',
                                                    'floor_num': 'Floor',
                                                    'usable_area': 'Area',
                                                    'garage': 'Garage',
                                                    'balcony': 'Balcony',
                                                    'terrace': 'Terrace',
                                                    'furnished': 'Furnished',
                                                    'elevator': 'Elevator',
                                                    'energy_class': 'Energy Class',
                                                    'school_transit_dur': 'Time to School(PT)',
                                                    'school_transit_twalk': 'Total Walk time(PT)'})
top_units_df['Address']= top_units_df.apply(lambda x: f"<a href= '{main_url}{x.url}' target= '_blank'> {x.Address}", axis= 1)
top_units_df['Furnished']= top_units_df['Furnished'].replace('', 'Unknown').replace(True, 'Yes').replace(False, 'No')
top_units_df['Elevator']= top_units_df['Elevator'].replace('', 'Unknown').replace(True, 'Yes').replace(False, 'No')

school_geo= ast.literal_eval(open(Path(r'../data/school_address.txt'), 'r').read())
########LAYOUT########

app.layout= dbc.Container([
    html.H1('Prague House Hunter', style= {'textAlign': 'center'}),

    ########ROW1########
    dbc.Row([
        dbc.Col([html.H2('Filter')])
    ]),
    html.Br(),
    ########ROW2########
    dbc.Row([
        dbc.Col([
            html.H3('Price (Czk)'),
            dcc.RangeSlider(id= 'price_slider',
                            min= 30000,
                            max= 50000,
                            step= 500,
                            value= [30000, 50000],
                            marks= {i: f'{i:,}' for i in range(30000, 50001, 1000)}),
        ], width= {'size':  '12'})
    ]),
    html.Br(),
    ########ROW3########
    dbc.Row([
        dbc.Col([
            html.H3('Unit Type'),
            dcc.Checklist(id= 'unit_type_dropdown',
                        options= [{'label': i.capitalize(), 'value':i}  for i in ['apartment', 'house']],
                        value= ['apartment', 'house'],
                        labelStyle= {'display': 'inline-block'},
                        inputStyle= {"margin-right": "5px",
                                    "margin-left": "10px"}),
                        
                        
            ], width= {'size':  '2'}),
        dbc.Col([
            html.H3('Number of Bedrooms'),
            dcc.Checklist(id= 'bedrooms_dropdown',
                        options= [{'label': i, 'value': i} for i in range(2, 5)],
                        value= [2, 3, 4],
                        labelStyle= {'display': 'inline-block'},
                        inputStyle= {"margin-right": "5px",
                                    "margin-left": "10px"}
                        )
        ], width= {'size':  '3'}),
        dbc.Col([
            html.H3('Furnished'),
            dcc.Checklist(id= 'furnished_dropdown',
                        options= [{'label': i, 'value': i} for i in top_units_df['Furnished'].unique()],
                        value= ['No', 'Unknown', 'Partially'],
                        labelStyle= {'display': 'inline-block'},
                        inputStyle= {"margin-right": "5px",
                                    "margin-left": "10px"}
                        )
        ], width= {'size':  '3'}),
        dbc.Col([    
            html.H3('Usable Area (m\u00b2)'),
            dcc.RangeSlider(id= 'area_slider',
                            min= 60,
                            max= 200,
                            step= 20,
                            value= [60, 200],
                            marks= {i: str(i) for i in range(60, 201, 20)}),
            ], width= {'size':  '4'})
        ]),    
    html.Br(),
    ########ROW4########
    dbc.Row([
        dbc.Col([
            #Add table
            dash_table.DataTable(data=top_units_df.to_dict('records'),
                                columns= [
                                    {'name': name, 'id': name, 'presentation': 'markdown'} if name == 'Address' else\
                                        {'name': name, 'id': name} \
                                        for name in top_units_df.columns if name != 'url'],
                                id= 'top_table',
                                markdown_options={"html": True},
                                row_selectable= 'multi',
                                page_size= 10,
                                selected_rows=[0,1],
                                style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgba(32, 178, 170, 0.7)',
                },
                {
                    'if': {'row_index': 'even'},
                    'backgroundColor': 'rgba(176, 196, 222, 0.7)',
                },
            ],
            )],
                width= dict(size= 4)),
        
    ]),
    html.Br(),
    ########ROW5########
    dbc.Row([
        dbc.Col([
            html.H4(id='unit1_title', style= {'textAlign': 'left'}),
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Tabs(
                            [
                                dbc.Tab(label="Unit Map",
                                        tab_id="unit1_map",
                                        children=[
                                                dcc.Graph(id= 'unit1_map_graph'
                                                        )
                                            
                                                ]),
                                dbc.Tab(label="Nearby Places", id="nearby1_places"),
                                dbc.Tab(label="Pictures", id="pictures1"),
                            ],
                            id="unit1_tabs",
                            active_tab="unit1_map",
                        )
                    ),
                    ]
                ),
            
            ], width= 6),
        dbc.Col([
            html.H4(id='unit2_title', style= {'textAlign': 'left'}),
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Tabs(
                            [
                                dbc.Tab(label="Unit Map",
                                        tab_id="unit2_map",
                                        children=[
                                                dcc.Graph(id= 'unit2_map_graph'
                                                        )
                                            
                                                ]
                                        ),
                                dbc.Tab(label="Nearby Places", id="nearby2_places", children=[]),
                                dbc.Tab(label="Pictures", id="pictures2", children=[]),
                            ],
                            id="unit2_tabs",
                            active_tab="unit2_map",
                        )
                    ),
                    ]
                ),
            
            ], width= 6),
        ]),
], fluid= True)

#####################################################
#CALL BACK FOR UPDATING TABLE
#####################################################
@app.callback(
    Output('top_table', 'data'),
    Input('price_slider', 'value'),
    Input('unit_type_dropdown', 'value'),
    Input('bedrooms_dropdown', 'value'),
    Input('furnished_dropdown', 'value'),
    Input('area_slider', 'value')
    )

def update_table(price_range, unit_types, bedroom_nums, furnished, usable_area):
    ddf= top_units_df.copy()
    
    
    filtered_data= ddf.loc[(top_units_df['Rent Price'] >= price_range[0]) & (ddf['Rent Price'] <= price_range[1]) &
                        (ddf['Unit Type'].isin(unit_types)) &
                        (ddf['Bedrooms'].apply(lambda x: re.findall(r'\d+', str(x))[0]).astype(int).isin(bedroom_nums)) &
                        (ddf['Furnished'].isin(furnished))&
                        (ddf['Area'] >= usable_area[0]) & (ddf['Area'] <= usable_area[1])]

    return filtered_data.sort_values(by= ['Score', 'Rent Price'], ascending= [False, True]).to_dict('records')



####################################################
#CALL BACK FOR UPDATING TABS
####################################################
@app.callback(
    Output("unit1_map_graph", "figure"),
    Output("unit2_map_graph", "figure"),
    Output("pictures1", "children"),
    Output("pictures2", "children"),
    Output('unit1_title','children'),
    Output('unit2_title','children'),
    Input("top_table", "selected_rows")
)

def update_unit_tabs(
    # unit1_tab, unit2_tab,
    selected_rows):
    def create_map(df, selected_row):
        gmaps= googlemaps.Client(key= gmap_access_token)
        directions_result= gmaps.directions(df.iloc[selected_row]['home_geo'],
                                    school_geo,
                                    mode= 'transit')
        # Extract coordinates from the directions result
        coordinates=[]
        for leg in directions_result[0]['legs']:
            for step in leg['steps']:
                coordinates.append((step['start_location']['lat'], step['start_location']['lng']))
                coordinates.append((step['end_location']['lat'], step['end_location']['lng']))
        lon=[lng for lat, lng in coordinates]
        lat=[lat for lat, lng in coordinates]
        figure= go.Figure(
            go.Scattermapbox(
                lat= lat,
                lon= lon,
                mode= 'markers+text+lines',
                marker= go.scattermapbox.Marker(
                    size= 10,
                    color= 'rgb(255, 0, 0)',
                    opacity= 0.7,
                    # symbol='circle'
                ),
                line=dict(width=2, color='blue'),
            )
                )
        figure.update_layout(
        hovermode='closest',        
        margin={"r":5,"t":5,"l":5,"b":5},
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=coordinates[0][0],
                lon=coordinates[0][1]
            ),
            style='streets',
            pitch=1,
            zoom=12, 
        )
    )
        # figure.update_traces(marker_symbol= 'lodging',
        #                     marker_size= 14,
        #                     marker_color= 'rgb(255, 0, 0)')
        return figure
        
    def unit_pictures(df, selected_row):
        return dbc.Carousel(
            items=[
                {'key': f'pic{i}', 'src': pic, 'caption': f'Pic {i+1}'} for i, pic in enumerate(df.iloc[selected_row]['pictures'])
                ],
            controls= True,
            indicators= True,
        )
    dict_tab= {'unit1_map': create_map(df, selected_row= selected_rows[0]),
            'unit2_map': create_map(df, selected_row= selected_rows[1]),
            'unit1_pictures': unit_pictures(df, selected_row= selected_rows[0]),
            'unit2_pictures': unit_pictures(df, selected_row= selected_rows[1])}

    return dict_tab.get('unit1_map'), \
            dict_tab.get('unit2_map'),\
                dict_tab.get('unit1_pictures'),\
                    dict_tab.get('unit2_pictures'),\
                        f"Unit 1: {df.iloc[selected_rows[0]]['Address']}",\
                            f"Unit 2: {df.iloc[selected_rows[1]]['Address']}"

# @app.callback(
#     Output('unit_specs_table', 'children'),
#     Input('top_table', 'selected_rows')

# )

# def display_selected_data(selected_rows):
#     if selected_rows:
#         # selected_data = df.iloc[selected_rows]
#         # selected_data= selected_data.loc[:, ['bedrooms', 'floor_num',
#         #                                     'usable_area', 'garage', 'balcony', 'terrace',
#         #                                     'furnished', 'elevator', 'energy_class']]

#         return [
#             html.H6(f"Unit {i+1}:\n {df.iloc[i]['unit_description']}", 
#                     style={'display': 'inline-block',
#                         'white_space':'normal',
#                         'max_width': '10px',
#                         'margin-right': '10px'
#                         }) for i in df.iloc[selected_rows].index]
#     else:
#         return []

if __name__ == '__main__':
    app.run_server(debug=True)
    