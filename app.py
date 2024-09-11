import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# Load your dataset
df = pd.read_excel('Cooperator Map_ XC.xlsx', sheet_name='data')

# Rename columns for consistency
df.rename(columns={'Ranking (3 is highest, indicated by darkest color)': 'Ranking'}, inplace=True)

# Generate unique identifier for each entry
df['id'] = df.groupby(['Name', 'city lat', 'city long']).cumcount()

# Offset coordinates for duplicates
offset = 0.2
df['city lat'] += df['id'] * offset
df['city long'] -= df['id'] * offset

# Define color shades for each Portfolio based on Ranking
colors = {
    'Fungicide': {
        3: 'darkgreen',
        2: 'green',
        1: 'lightgreen'
    },
    'Herbicide': {
        3: 'darkred',
        2: 'red',
        1: 'lightcoral'
    },
    'Insecticide': {
        3: '#520154',  # Dark purple
        2: '#f503fc',  # purple
        1: '#fc99ff'   # Light purple
    },
    'Nematicide': {
        3: '#758204',  # Dark Yellow
        2: '#edff4d',  # Yellow
        1: '#eaf590'   # Light yellow
    }
}

# Create a column for color based on Portfolio and Ranking
def get_color(row):
    return colors[row['Portfolio']].get(row['Ranking'], '#808080')  # Default to gray

df['Color'] = df.apply(get_color, axis=1)

# Create a new column that combines Portfolio and Ranking for the legend
df['Portfolio_Ranking'] = df['Portfolio'] + ' (Ranking ' + df['Ranking'].astype(str) + ')'

# Define the desired order for the legend
ordered_categories = [
    'Fungicide (Ranking 3)', 'Fungicide (Ranking 2)', 'Fungicide (Ranking 1)',
    'Herbicide (Ranking 3)', 'Herbicide (Ranking 2)', 'Herbicide (Ranking 1)',
    'Insecticide (Ranking 3)', 'Insecticide (Ranking 2)', 'Insecticide (Ranking 1)',
    'Nematicide (Ranking 3)', 'Nematicide (Ranking 2)', 'Nematicide (Ranking 1)'
]

# Sort the DataFrame based on the ordered categories
df['Portfolio_Ranking'] = pd.Categorical(df['Portfolio_Ranking'], categories=ordered_categories, ordered=True)
df.sort_values('Portfolio_Ranking', inplace=True)

# Define a function to map Ranking to marker sizes
def size_mapper(ranking):
    size_mapping = {
        3: 20,  # Largest size for the highest ranking
        2: 15,   # Medium size
        1: 10    # Smallest size
    }
    return size_mapping.get(ranking, 5)  # Default to size 5

df['Size'] = df['Ranking'].apply(size_mapper)

# Initialize the Dash app
app = Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.H1('Portfolio Distribution Map'),
    
    # Dropdown for Portfolio filter
    dcc.Dropdown(
        id='portfolio-filter',
        options=[{'label': p, 'value': p} for p in df['Portfolio'].unique()],
        value=df['Portfolio'].unique().tolist(),  # Default to all
        multi=True
    ),
    
    # Dropdown for Ranking filter
    dcc.Dropdown(
        id='ranking-filter',
        options=[{'label': f'Ranking {r}', 'value': r} for r in df['Ranking'].unique()],
        value=df['Ranking'].unique().tolist(),  # Default to all
        multi=True
    ),
    
    # Map
    dcc.Graph(id='map', style={'height': '80vh', 'width': '100vw'})  # Adjust the size here
])

# Define callback to update the map based on filters
@app.callback(
    Output('map', 'figure'),
    [Input('portfolio-filter', 'value'),
     Input('ranking-filter', 'value')]
)
def update_map(selected_portfolios, selected_rankings):
    filtered_df = df[
        (df['Portfolio'].isin(selected_portfolios)) &
        (df['Ranking'].isin(selected_rankings))
    ]
    
    fig = go.Figure()
    
    # Add traces for each category in the filtered data
    for category in ordered_categories:
        category_df = filtered_df[filtered_df['Portfolio_Ranking'] == category]
        
        fig.add_trace(go.Scattergeo(
            locationmode='USA-states',
            lon=category_df['city long'],
            lat=category_df['city lat'],
            text=category_df['Name'],  # Static text labels for names
            marker=dict(
                size=category_df['Size'],
                color=category_df['Color'],
                opacity=0.8,
                line=dict(width=0.5, color='black')
            ),
            mode='markers+text',  # Ensure both markers and text are displayed
            textposition='top center',  # Position the static labels
            name=category,  # Name shown in the legend
            hovertemplate=(
                '<b>Name:</b> %{text}<br>' +
                '<b>Ranking:</b> %{customdata[0]}<br>' +
                '<b>State:</b> %{customdata[1]}<br>' +
                '<extra></extra>'
            ),
            customdata=category_df[['Ranking', 'State']].values  # Include Ranking and State in hover info
        ))

    # Update layout for the map
    fig.update_layout(
        title='Portfolio Distribution with Ranking across the US',
        geo=dict(
            scope='usa',
            showland=True,
            landcolor='lightgrey',
            showcountries=True,
            countrycolor='black',
            showocean=True,
            oceancolor='lightblue'
        ),
        legend_title_text='Portfolio and Ranking',  # Legend title
        title_x=0.5
    )

    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)