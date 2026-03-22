# Log_Viewer/LogViewer.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import base64
import re
import pandas as pd
import dash
from dash import dcc, html, dash_table, Input, Output, State
import plotly.express as px
import emoji

# Regex pattern to parse your specific log format:
LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d+\.\d+)\s+\|\s+(?P<level>\w+)\s+\|\s+(?P<partition>\w+)\s+\|\s+(?P<process>\w+)\s+\|\s+(?P<function>[\w\.]+)\s+\|\s+(?P<message>.*)$"
)

def extract_type(msg):
    match = re.search(r'\[(.*?)\]', msg)
    return match.group(1) if match else "UNKNOWN"

def extract_emojis(msg):
    """Returns a list of all emojis found in the message string."""
    return [char for char in msg if emoji.is_emoji(char)]

def parse_log_file(decoded_contents):
    data = []
    lines = decoded_contents.split('\n')
    for idx, line in enumerate(lines):
        match = LOG_PATTERN.match(line.strip())
        if match:
            row = match.groupdict()
            row['type'] = extract_type(row['message'])
            row['emojis'] = extract_emojis(row['message'])
            row['sequence'] = idx # Keep track of order for timeline
            data.append(row)
    return pd.DataFrame(data)

# --- Dark Mode Theme Constants ---
BG_COLOR = "#121212"
CARD_COLOR = "#1E1E1E"
TEXT_COLOR = "#E0E0E0"
ACCENT_COLOR = "#BB86FC"

app = dash.Dash(__name__)
app.title = "Log Visualizer: Dark Edition"

app.layout = html.Div(style={'fontFamily': 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif', 'backgroundColor': BG_COLOR, 'color': TEXT_COLOR, 'padding': '20px', 'minHeight': '100vh'}, children=[
    html.H1("Log Analytics Dashboard", style={'textAlign': 'center', 'color': ACCENT_COLOR, 'textTransform': 'uppercase', 'letterSpacing': '2px'}),
    
    # 1. File Upload Button
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Drag and Drop or ', html.B('Select Log File')]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '2px', 'borderStyle': 'dashed', 'borderColor': ACCENT_COLOR,
            'borderRadius': '10px', 'textAlign': 'center', 'marginBottom': '20px',
            'backgroundColor': CARD_COLOR, 'cursor': 'pointer', 'transition': '0.3s'
        },
        multiple=False
    ),
    
    dcc.Store(id='stored-data'),
    
    # 2. Filters
    html.Div([
        html.Div([
            html.Label("Filter by Process:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(id='filter-process', multi=True, style={'color': '#000'})
        ], style={'width': '32%', 'display': 'inline-block', 'marginRight': '1%'}),
        
        html.Div([
            html.Label("Filter by Type:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(id='filter-type', multi=True, style={'color': '#000'})
        ], style={'width': '32%', 'display': 'inline-block', 'marginRight': '1%'}),
        
        html.Div([
            html.Label("Filter by Function:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(id='filter-function', multi=True, style={'color': '#000'})
        ], style={'width': '32%', 'display': 'inline-block'})
    ], style={'marginBottom': '20px', 'backgroundColor': CARD_COLOR, 'padding': '15px', 'borderRadius': '10px'}),
    
    # 3. Flamboyant Interactive Charts Row 1
    html.Div([
        dcc.Graph(id='chart-sunburst', style={'width': '40%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        dcc.Graph(id='chart-emoji', style={'width': '60%', 'display': 'inline-block', 'verticalAlign': 'top'})
    ]),

    # 4. Flamboyant Interactive Charts Row 2
    html.Div([
        dcc.Graph(id='chart-heatmap', style={'width': '50%', 'display': 'inline-block'}),
        dcc.Graph(id='chart-timeline', style={'width': '50%', 'display': 'inline-block'})
    ], style={'marginTop': '20px'}),
    
    # 5. Drill-Down List
    html.H3("Drill-Down Data Viewer", style={'marginTop': '40px', 'color': ACCENT_COLOR}),
    dash_table.DataTable(
        id='log-table',
        columns=[
            {'name': 'Seq', 'id': 'sequence'},
            {'name': 'Process', 'id': 'process'},
            {'name': 'Type', 'id': 'type'},
            {'name': 'Function', 'id': 'function'}
        ],
        page_size=10,
        style_table={'overflowX': 'auto', 'borderRadius': '10px'},
        style_cell={'textAlign': 'left', 'padding': '12px', 'backgroundColor': CARD_COLOR, 'color': TEXT_COLOR, 'border': '1px solid #333'},
        style_header={'backgroundColor': '#2A2A2A', 'fontWeight': 'bold', 'color': ACCENT_COLOR, 'border': '1px solid #333'},
        style_data_conditional=[{'if': {'state': 'selected'}, 'backgroundColor': '#3b3b3b', 'border': '1px solid ' + ACCENT_COLOR}],
        row_selectable='single',
        filter_action="native",
        sort_action="native",
    ),
    
    # 6. Detail Viewer
    html.H3("Raw Detail Inspector", style={'marginTop': '30px', 'color': ACCENT_COLOR}),
    html.Pre(id='detail-viewer', style={
        'border': f'1px solid {ACCENT_COLOR}', 'padding': '20px', 
        'whiteSpace': 'pre-wrap', 'wordBreak': 'break-all', 
        'backgroundColor': '#000000', 'color': '#00FF41', # Matrix-style terminal green for raw logs
        'borderRadius': '10px', 'fontFamily': 'Consolas, monospace', 'boxShadow': '0px 0px 15px rgba(187, 134, 252, 0.2)'
    })
])

# Callback 1: Parse file
@app.callback(
    [Output('stored-data', 'data'),
     Output('filter-process', 'options'),
     Output('filter-type', 'options'),
     Output('filter-function', 'options')],
    Input('upload-data', 'contents')
)
def update_data(contents):
    if contents is None:
        return [], [], [], []
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string).decode('utf-8', errors='replace')
    df = parse_log_file(decoded)
    
    if df.empty:
        return [], [], [], []
        
    proc_opts = [{'label': i, 'value': i} for i in sorted(df['process'].unique())]
    type_opts = [{'label': i, 'value': i} for i in sorted(df['type'].unique())]
    func_opts = [{'label': i, 'value': i} for i in sorted(df['function'].unique())]
    
    return df.to_dict('records'), proc_opts, type_opts, func_opts


# Callback 2: Build Flamboyant Charts
@app.callback(
    [Output('chart-sunburst', 'figure'),
     Output('chart-emoji', 'figure'),
     Output('chart-heatmap', 'figure'),
     Output('chart-timeline', 'figure'),
     Output('log-table', 'data')],
    [Input('stored-data', 'data'),
     Input('filter-process', 'value'),
     Input('filter-type', 'value'),
     Input('filter-function', 'value')]
)
def update_visuals(data, procs, types, funcs):
    if not data:
        return {}, {}, {}, {}, []
        
    df = pd.DataFrame(data)
    
    # Apply dropdown filters
    if procs: df = df[df['process'].isin(procs)]
    if types: df = df[df['type'].isin(types)]
    if funcs: df = df[df['function'].isin(funcs)]
    
    layout_theme = 'plotly_dark'
    bg_color = '#000000' # True black background for charts

    # 1. Sunburst Chart
    fig_sun = px.sunburst(
        df, path=['process', 'function'], 
        title='Process & Function Hierarchy (Click to drill)',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_sun.update_layout(template=layout_theme, paper_bgcolor=bg_color, plot_bgcolor=bg_color)

    # 2. Emoji Bar Chart
    all_emojis = [emoji for sublist in df['emojis'] for emoji in sublist]
    if all_emojis:
        emoji_df = pd.Series(all_emojis).value_counts().reset_index()
        emoji_df.columns = ['Emoji', 'Count']
        fig_emoji = px.bar(
            emoji_df, x='Emoji', y='Count', text='Count',
            title=f"Emoji Breakdown (Top: {emoji_df['Emoji'].iloc[0]})",
            color='Count', color_continuous_scale='plasma'
        )
        fig_emoji.update_traces(textposition='outside', textfont_size=18, marker_line_color='rgb(8,48,107)', marker_line_width=1.5)
    else:
        fig_emoji = px.bar(title="No Emojis Found in Current Filter")
    fig_emoji.update_layout(template=layout_theme, paper_bgcolor=bg_color, plot_bgcolor=bg_color)

    # 3. Heatmap
    cross_tab = pd.crosstab(df['process'], df['type'])
    fig_heat = px.imshow(
        cross_tab, text_auto=True, aspect="auto",
        title="Density Heatmap: Process vs. Message Type",
        color_continuous_scale='purpor'
    )
    fig_heat.update_layout(template=layout_theme, paper_bgcolor=bg_color, plot_bgcolor=bg_color)

    # 4. Timeline/Sequence Chart
    seq_counts = df['sequence'].value_counts().reset_index()
    fig_time = px.histogram(
        df, x="sequence", color="type",
        title="Log Activity Sequence Timeline",
        nbins=50, barmode="stack", color_discrete_sequence=px.colors.qualitative.Vivid
    )
    fig_time.update_layout(template=layout_theme, paper_bgcolor=bg_color, plot_bgcolor=bg_color)

    # FIX: Convert the emojis list into a string so Dash DataTable doesn't crash
    df['emojis'] = df['emojis'].apply(lambda x: "".join(x) if isinstance(x, list) else x)

    return fig_sun, fig_emoji, fig_heat, fig_time, df.to_dict('records')


# Callback 3: Update Detail Viewer
@app.callback(
    Output('detail-viewer', 'children'),
    Input('log-table', 'selected_rows'),
    State('log-table', 'data')
)
def show_detail(selected_rows, table_data):
    if selected_rows and table_data:
        row = table_data[selected_rows[0]]
        detail_text = (
            f"TIMESTAMP : {row.get('timestamp')}\n"
            f"LEVEL     : {row.get('level')}\n"
            f"PARTITION : {row.get('partition')}\n"
            f"PROCESS   : {row.get('process')}\n"
            f"FUNCTION  : {row.get('function')}\n"
            f"TYPE TAG  : {row.get('type')}\n"
            f"EMOJIS    : {row.get('emojis', '')}\n"  # Safely handle the stringified emojis
            f"{'='*60}\n\n"
            f"{row.get('message')}"
        )
        return detail_text
    return "> AWAITING SELECTION... \n> Please select a radio button from the data table above."



if __name__ == '__main__':
    app.run(debug=True)
