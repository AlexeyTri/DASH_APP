import dash
import dash_core_components as dcc
import dash_html_components as html
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import numpy as np
import dash_table

"""" READ DATA """

response = requests.get('http://asterank.com/api/kepler?query={}&limit=2000')
df = pd.json_normalize(response.json())
df = df[df['PER'] > 0]
df['KOI'] = df['KOI'].astype(int, errors='ignore')

# create Star size category
bins = [0, 0.8, 1.2, 100]
names = ['small', 'similar', 'bigger']
df['StarSize'] = pd.cut(df['RSTAR'], bins, labels=names)

# TEMPERATURE BINS
tp_bins = [0, 200, 400, 500, 5000]
tp_labels = ['low', 'optimal', 'high', 'extreme']
df['temp'] = pd.cut(df['TPLANET'], tp_bins, labels=tp_labels)

# SIZE BINS
rp_bins = [0, 0.5, 2, 4, 100]
rp_labels = ['low', 'optimal','high','extrim']
df['gravity'] = pd.cut(df['RPLANET'], rp_bins, labels=rp_labels)

# ESTIMATE OBJECT STATUS
df['status'] = np.where((df['temp'] == 'optimal') &
                        (df['gravity'] == 'optimal'),
                        'promising', None)
df.loc[:, 'status'] = np.where((df['temp'] == 'optimal') &
                               (df['gravity'].isin(['low', 'high'])),
                        'chalenging', df['status'])
df.loc[:, 'status'] = np.where((df['gravity'] == 'optimal') &
                               (df['temp'].isin(['low', 'high'])),
                        'chalenging', df['status'])
df['status'] = df.status.fillna('extreme')

df.loc[:, 'relative_dist'] = df['A']/df['RSTAR']
# print(df.groupby('status')['ROW'].count())
# GLOBAL DESIGN SETTINGS
CHARTS_TEMPLATE = go.layout.Template(
    layout=dict(
        font=dict(family='Century Gothic',
                  size=14),
        legend=dict(orientation='h',
                    title_text='',
                    x=0,
                    y=1.1)
    )
)

COLOR_STATUS_VALUES = ['lightgray','#1F85DE','#DE251F']

# Filters
options = []
for k in names:
    options.append({'label': k, 'value': k})

star_size_selector = dcc.Dropdown(
    id='star-selector',
    options=options,
    value=['small', 'similar', 'bigger'],
    multi=True
)

# fig = px.scatter(df, x = "TPLANET", y = "A")

rplanet_selector = dcc.RangeSlider(
    id='range-slider',
    min=min(df['RPLANET']),
    max=max(df['RPLANET']),
    marks={5: '5', 10: '10', 20: '20'},
    step=1,
    value=[min(df['RPLANET']), max(df['RPLANET'])]
)

#  TABS CONTENT
tab1_content = [dbc.Row([
                        dbc.Col([html.Div(id='dist-temp-chart')]),
                        dbc.Col([html.Div(id='celestial-chart')])
                        ], style={'margin-top': 20}),
                 dbc.Row([
                        dbc.Col(html.Div(id='relative-dist-chart'), md=6),
                        dbc.Col(html.Div(id='mstar-tstar-chart'), md=6)
                        ], style={'margin-top': 20})]

tab2_content = [dbc.Row(html.Div(id='data-table'),style={'margin-top': 20})]

# tab3 content
table_header = [html.Thead(html.Tr([html.Th("Field Name"), html.Th("details")]))]
expl = {
        'KOI' :	'Object of Interest number',
        'A': 'Semi-major axis (AU)',
        'RPLANET': 	'Planetary radius (Earth radii)',
        'RSTAR': 'Stellar radius (Sol radii)',
        'TSTAR': 'Effective temperature of host star as reported in KIC (k)',
        'KMAG':'Kepler magnitude (kmag)',
        'TPLANET':	'Equilibrium temperature of planet, per Borucki et al. (k)',
        'T0': 'Time of transit center (BJD-2454900)',
        'UT0': 'Uncertainty in time of transit center (+-jd)',
        'UT0': 'Uncertainty in time of transit center (+-jd)',
        'PER': 'Period (days)',
        'UPER': 'Uncertainty in period (+-days)',
        'DEC': 'Declination (@J200)',
        'RA': 'Right ascension (@J200)',
        'MSTAR': 'Derived stellar mass (msol)'
        }
tbl_rows = []
for i in expl:
    tbl_rows.append(html.Tr([html.Td(i), html.Td(expl[i])]))
table_body = [html.Tbody(tbl_rows)]
table = dbc.Table(table_header + table_body, bordered=True)


text = 'Data are sourced from API via asterank.com'
tab3_content = [dbc.Row(html.A(text, href='http://www.asterank.com/kepler'),
                        style={'margin-top': 20}),
                dbc.Row(html.Div(children=table), style={'margin-top':20})]

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.FLATLY])

""" LAYOUT """

app.layout = html.Div([
    # header
    dbc.Row([
        dbc.Col(
            html.Img(src=app.get_asset_url('images/a.png'),
                     style={
                         'width': '100px',
                         'margin-left': '40px'
                     }),
            width={'size': 1}
        ),
        dbc.Col([
            html.H1('Exoplanet Data Visualization'),
            html.A('Readabout exoplanets', href='https://spaceplace.nasa.gov/')],
                width={'size': 7}),
        dbc.Col(
            html.Div([
                html.P('Developed by'),
                html.A('LitovchenkoA.Corporate', href='', style={'margin-left': '2px'})
                     ], className='app-referral'),
            width={'size': 4})],
        className='app-header'),
    # body
    html.Div([
    # filters
        dbc.Row([
            dbc.Col([html.H6('Select planet main semi-axis range'),
                     html.Div(rplanet_selector)
                     ],
                        width={'size': 3}),
            dbc.Col([html.H6('Star size '),
                     html.Div(star_size_selector)
                    ],
                    width={'size': 3, 'offset': 1}),
            dbc.Col(dbc.Button('Apply',
                               id='submit-val',
                               n_clicks=0,
                               className='mr-2'))
                ], style={'margin-bottom': 40}),
        # charts
        dbc.Tabs([
            dbc.Tab(tab1_content, label="Charts"),
            dbc.Tab(tab2_content, label='Data'),
            dbc.Tab(tab3_content, label='About')
        ])

        ], className='app-body')
    ])


""" CALL BACKS """

# таблица бцдет восприимчева к фильтрам , сели она созадана внитри calback
@app.callback(
    [Output(component_id='dist-temp-chart', component_property='children'),
     Output(component_id='celestial-chart', component_property='children'),
     Output(component_id='relative-dist-chart', component_property='children'),
     Output(component_id='mstar-tstar-chart', component_property='children'),
     Output(component_id='data-table', component_property='children')],
    [Input(component_id='submit-val', component_property='n_clicks')],
    [State(component_id='range-slider', component_property='value'),
     State(component_id='star-selector', component_property='value')]
)
def update_dist_temp_chart(n, radius_range, star_size):
    # print(n)
    chart_data = df[(df['RPLANET'] > radius_range[0]) &
                    (df['RPLANET'] < radius_range[1]) &
                    (df['StarSize'].isin(star_size))]
    if len(chart_data) == 0:
        return html.Div('Please select more data'), html.Div(), html.Div(), html.Div()


    fig1 = px.scatter(chart_data, x='TPLANET', y='A', color='StarSize')
    fig1.update_layout(template=CHARTS_TEMPLATE)
    html1 = [
        html.H4('Planet Temperature ~ Distance from the Star'),
        dcc.Graph(figure=fig1)
    ]
    fig2 = px.scatter(chart_data, x='RA', y='DEC', size='RPLANET',
                      color='status',
                      color_discrete_sequence=COLOR_STATUS_VALUES)
    fig2.update_layout(template=CHARTS_TEMPLATE)
    html2 = [
        html.H4('Position in the Celestial Sphere'),
        dcc.Graph(figure=fig2)
    ]

    # RELATIVE DIST CHART
    fig3 = px.histogram(chart_data, x='relative_dist',
                        color='status', barmode='overlay',
                        marginal='violin')
    fig3.add_vline(x=1, y0=0, annotation_text='Earth', line_dash='dot')
    fig3.update_layout(template=CHARTS_TEMPLATE)
    html3 = [html.H4('Relative Distance (AU/Sol radius)'),
           dcc.Graph(figure=fig3)]

    fig4 = px.scatter(chart_data, x='MSTAR', y='TSTAR', size='RPLANET',
                      color='status',
                      color_discrete_sequence=COLOR_STATUS_VALUES)
    fig4.update_layout(template=CHARTS_TEMPLATE)
    html4 = [html.H4('Star Mass ~ star Temperature'),
             dcc.Graph(figure=fig4)]

    # RAW DATA TABLE
    raw_data = chart_data.drop(['relative_dist',
                                'StarSize',
                                'ROW',
                                'temp',
                                'gravity'], axis=1)
    tbl = dash_table.DataTable(data=raw_data.to_dict('records'),
                               columns=[{'name': i, 'id': i} for i in raw_data.columns],
                               style_data={
                                   'width': '100px',
                                   'maxWidth': '100px',
                                   'minWidth': '100px'
                               },
                               style_header={'textAlign': 'center'},
                               page_size=40)
    html5 = [html.H4('Raw Data'), tbl]

    return html1, html2, html3,html4, html5


if __name__ == "__main__":
    app.run_server(debug=True)




