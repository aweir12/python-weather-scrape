import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
from datetime import date, timedelta

# Before and after portions of the URL
url1 = r'https://english.wunderground.com/history/airport/OJAM/'
url2 = r'/DailyHistory.html?req_city=Amman&req_state=&req_statename=Jordan&reqdb.zip=&reqdb.magic=&reqdb.wmo'

# Building Date Timeline
begDate = date(2008, 1, 1)
endDate = date(2010, 1, 1)
delta = endDate - begDate
histDates = []

# Create a list of dates to get data for
for i in range(delta.days + 1):
    dt = begDate + timedelta(days=i)
    histDates.append(dt)

# Take a particular date and return table level data from html source code in a df
def histDfCreate(theDate):
    urlStr = url1 + theDate.strftime('%Y/%m/%d') + url2
    response = requests.get(urlStr)
    tbl = response.text.split("<div id=\"observations_details\" class=\"high-res\" >",1)
    try:
        tbl = tbl[1].split("<div class=\"obs-table-footer\">",1)
    except:
        return

    tbl = tbl[0]
    tbl = BeautifulSoup(tbl,'lxml')

    n_columns = 0
    n_rows = 0
    column_names = []
    
    # Find columns and rows
    for row in tbl.find_all('tr'):
        td_tags = row.find_all('td')
        if len(td_tags) > 0:
            n_rows+=1
            if n_columns == 0:
                n_columns = len(td_tags)
            
        th_tags = row.find_all('th')
        if len(th_tags) > 0 and len(column_names) == 0:
            for th in th_tags:
                column_names.append(th.get_text())
    
    columns = column_names if len(column_names) > 0 else range(0, n_columns)
    df = pd.DataFrame(columns = columns, index= range(0,n_rows))
    row_marker = 0
    
    # Get the data
    for row in tbl.find_all('tr'):
        column_marker = 0
        columns = row.find_all('td')
        for column in columns:
            df.iat[row_marker,column_marker] = column.get_text()
            column_marker += 1
        if len(columns) > 0:
            row_marker += 1

    # Get rid of bad characters, pun intended
    for column in df:
        df[column] = df[column].str.replace(r'\n','')
        df[column] = df[column].str.replace(r'\t','')
        df[column] = df[column].str.replace('°F','')
        df[column] = df[column].str.strip()
    
    # Add a date column
    df['Date'] = theDate
    
    # Dealing with column heading changes for time zones
    try:
        df['Time'] = df['Time (EET)'] + ' EET'
    except:
        df['Time'] = df['Time (EEST)'] + ' EEST'
    
    # Drop time zone specific columns
    cols = [c for c in df.columns if c.lower()[:6] != 'time (']
    df = df[cols]
    
    # Drop duplicate values, just take first value
    df.drop_duplicates(['Date','Time'],keep='first',inplace ='True')
    
    # Return the data frame
    return df
# End of function...


# Create initial df to put data in
wOutput = histDfCreate(histDates[0])

# Iterate over remaining dates and append df
for i in histDates:
    if histDates.index(i) > 0:
        wOutput = wOutput.append(histDfCreate(i))

# Reset Index
wOutput = wOutput.reset_index(drop="true")

# Pop a few columns (cleanup)
cols = list(wOutput)
cols
cols.insert(0, cols.pop(cols.index('Time')))
cols.insert(0, cols.pop(cols.index('Date')))
wOutput = wOutput.ix[:, cols]

# Output to .csv File
wOutput.to_csv('weatherData.csv')

