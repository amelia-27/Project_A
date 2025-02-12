import pandas as pd
import plotly.express as px
from dash import dcc, Dash
from dash import html
from dash.dependencies import Input, Output

#this class works to prevent error with consolidating the month data - basically prevents duplicates
def load_single_year_data(file_path):
        #try block helped to debug the issues with compiling month data
    try:
        df = pd.read_csv(file_path)

        if "Date" in df.columns:
            df = df.loc[:, ~df.columns.duplicated()] #prevents duplicates that causes error
            #\/ formatting date, dropping values with hashtags instead of dates in csv
            df["Date"] = pd.to_datetime(df["Date"], errors = 'coerce', dayfirst = True)
            df = df.dropna(subset = ["Date"])
            df = df.replace('#', pd.NA)
            df = df.dropna() #drops row with NaNs

                #Extracts year and creates year and month columns
            year = int(file_path.split('_')[-1].split('.')[0])
            processed_data = pd.DataFrame()
            processed_data["Year"] = [year]*len(df)
            processed_data["Month"] = df["Date"].dt.month

            numeric_columns = df.select_dtypes(include = ['number']).columns.tolist()
            processed_data[numeric_columns] = df[numeric_columns]

            result_df = processed_data.groupby(["Year", "Month"])[numeric_columns].mean().reset_index()
            return result_df
        else:
            print("Date column is not found in the data")
    except Exception as e:
        print(f'Error reading {file_path}: {e}')
    else:
        print(f'File not found: {file_path}')
    return pd.DataFrame()

#With the data cleaned up, we load in multiple csv files to show multiple years
def load_data(years):
    dfs = []
    for year in years: #this loop consolidates all the csv files
        file_path = f'EPA_{year}.csv'
        df = load_single_year_data(file_path)
        if not df.empty:
            dfs.append(df)

    if not dfs:
        print('Error loading the files. Check file paths.')
        return pd.DataFrame()

    result_df = pd.concat(dfs, ignore_index = True)
    #used to check what data was loading in:
    # print("Loaded data:")
    # print(result_df.head())
    return result_df

#years to select from (based on my csv files)
available_years = [1999, 2004, 2009, 2014, 2019, 2024]
df = load_data(available_years)

stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = Dash(__name__, external_stylesheets = stylesheets)
app.layout = html.Div([
    html.Div(dcc.Dropdown(), className = "four columns"), #four columns is in the CSS sheet code
    html.Div(dcc.Dropdown(), className = "four columns"),
    html.Div(dcc.Dropdown(), className = "four columns"),
],
    className = "row"
)

app.layout = html.Div(
    [
        html.Div(
            html.H1(
                "PM2.5 Pollutant", style = {"textAlign":"center"}
            ),
            className = "row",
        ),
        html.Div(dcc.Graph(id = "line-chart", figure = {}), className = "row"),
        html.Div(
            [
                html.Div(
                    dcc.Dropdown(
                        id = "my-dropdown",
                        multi = True,
                        options = [{"label": year, "value": year} for year in available_years],
                        value = [1999, 2024],
                    ),
                    className = "three columns",
                ),
            ],
            className = "row",
            ),
        ]
)

@app.callback(
    Output(component_id = "line-chart", component_property = "figure"),
    [Input(component_id = "my-dropdown", component_property = "value")],
)
def update_graph(selected_years):
    df = load_data(selected_years)
    if df.empty:
        return {}


    fig = px.line(
       data_frame = df,
       x = "Month",
       y = "Daily Mean PM2.5 Concentration",
       color = "Year",
       title = "PM2.5 Levels in LA Over Time",
       labels = {"Daily Mean PM2.5 Concentration": "PM2.5 Concentration", "Month": "Month" },
        category_orders = {"Month": list(range(1, 13))}
    )
    return fig

#run app:
if __name__ == '__main__':
    app.run_server(debug=True)


