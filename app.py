import pandas as pd
import dash
from dash import dcc, html
import plotly.graph_objects as go

# 1. Leitura do CSV com separador, decimal e valores nulos
df = pd.read_csv(
    'data.csv',
    sep=';',
    decimal=',',
    parse_dates=['B'],
    dayfirst=True,
    na_values=['#DIV/0!']
)

# 2. Converter coluna F para float, ignorando valores inválidos
df['F'] = pd.to_numeric(df['F'], errors='coerce')

# 3. Filtragem de datas de 2015–2025 e F entre 195 e 240
df = df[df['B'].dt.year.between(2015, 2025)]
df = df[df['F'].between(195, 240)]

# 4. Agrupar por data para o gráfico principal
daily = df.groupby('B').agg({
    'F': 'mean',
    'D': 'sum',
    'C': lambda x: ', '.join(sorted(set(x)))
}).rename(columns={'F': 'meanF', 'D': 'sumD', 'C': 'machines'})

# 5. Definição de cores para as barras
def color(v):
    if v < 196 or v > 216:
        return 'red'
    if v > 206:
        return 'yellow'
    return 'green'
daily['color'] = daily['meanF'].apply(color)

# 6. Linha vertical para 01/11/2021 (óleo combustível BP)
line_main = dict(
    type='line',
    x0='2021-11-01',
    x1='2021-11-01',
    y0=180, y1=250,
    line=dict(color='blue', dash='dash')
)

# 7. Gráfico principal com hover customizado
fig_main = go.Figure()
fig_main.add_trace(go.Bar(
    x=daily.index,
    y=daily['meanF'],
    marker_color=daily['color'],
    hovertemplate=(
        "Data: %{x|%d/%m/%Y}<br>"
        "Média F: %{y:.1f}<br>"
        "Máquinas: %{customdata[0]}<br>"
        "Energia (MWh): %{customdata[1]:.1f}<extra></extra>"
    ),
    customdata=daily[['machines', 'sumD']].values
))
fig_main.update_layout(
    title="Consumo específico UTE Pernambuco 3",
    yaxis=dict(range=[180, 250], dtick=10),
    shapes=[line_main]
)

# 8. Datas de overhaul por DG
overhaul = {
    'DG#01': '2016-11-24', 'DG#03': '2018-09-07', 'DG#04': '2018-07-01',
    'DG#05': '2017-07-24', 'DG#06': '2016-10-15', 'DG#08': '2017-01-19',
    'DG#09': '2018-11-17', 'DG#10': '2020-04-26', 'DG#11': '2017-04-25',
    'DG#12': '2017-03-06', 'DG#13': '2019-10-31', 'DG#14': '2016-09-01',
    'DG#15': '2019-08-01', 'DG#16': '2020-03-01', 'DG#17': '2017-06-18',
    'DG#18': '2016-07-20', 'DG#20': '2019-01-09', 'DG#21': '2017-05-23',
    'DG#22': '2019-03-14', 'DG#23': '2016-05-02'
}

# 9. Montagem dos 23 gráficos para cada DG
graphs = []
for i in range(1, 24):
    dg = f'DG#{i:02d}'
    dfg = df[df['C'] == dg]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dfg['B'], y=dfg['E']))
    fig.update_layout(
        title=f'Consumo específico {dg}',
        yaxis=dict(range=[180, 250], dtick=10),
        shapes=[line_main]
    )
    if dg in overhaul:
        fig.add_shape(
            type='line',
            x0=overhaul[dg], x1=overhaul[dg],
            y0=180, y1=250,
            line=dict(color='green', dash='dash')
        )
    graphs.append(dcc.Graph(figure=fig, className='chart-card'))

# 10. Criação do app Dash
app = dash.Dash(__name__)
server = app.server  # necessário para deploy

app.layout = html.Div([
    html.Div(className='header', children=[
        html.Img(src=app.get_asset_url('logo.png')),
        html.H2("UTE Pernambuco 3")
    ]),
    html.Div(className='container', children=[
        html.Div(className='main-chart chart-card', children=dcc.Graph(figure=fig_main)),
        html.Div(className='dg-charts', children=graphs)
    ])
])

# 11. Execução local
if __name__ == '__main__':
    app.run_server(debug=True)
