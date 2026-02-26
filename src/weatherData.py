import datetime
#import matplotlib.pyplot as plt
import meteostat as ms
import csv

def get_weather_history(latitude, longitude, altitude):
    weatherHistoryFile = 'data/weatherData.csv'
    
    # Read history from csv to see how much history is needed
    old_weather = read_weather_history_csv(weatherHistoryFile)
    lastDataDate = datetime.datetime.strptime(old_weather[-1][0], '%Y-%m-%d')
    today = datetime.date.today()
    
    # Get data from lastDataDate + 1 day until yesterday
    startDate = lastDataDate.date() + datetime.timedelta(days=1)
    endDate = today - datetime.timedelta(days=1)
    if endDate == startDate:
        return old_weather
    
    # Need to get recent weather info
    print('Requesting weather data from ' + str(startDate) + ' to ' + str(endDate))
    recent_weather = download_weather_history(latitude, longitude, altitude, startDate, endDate)
    weather_data = old_weather + recent_weather;
    write_weather_history_csv(weatherHistoryFile, weather_data)
    return weather_data

def read_weather_history_csv(fileName):
    data = []

    with open(fileName, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)

        for row_number, row in enumerate(reader):
            # Ignore the header row
            if row_number == 0:
                continue;
                
            if len(row) != 3:
                raise ValueError(
                    f"Row {row_number} does not have exactly 3 columns: {row}"
                )

            try:
                if row[1] == '<NA>' or row[2] == '<NA>':
                    continue
                
                converted_row = [
                    row[0],
                    float(row[1]),
                    float(row[2])
                ]
            except ValueError:
                raise ValueError(
                    f"Row {row_number} contains non-numeric data "
                    f"in column 2 or 3: {row}"
                )

            data.append(converted_row)

    return data

def write_weather_history_csv(fileName, data):
    with open(fileName, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Date', 'Tmin (deg F)', 'Tmax (deg F)'])
        for idx, row in enumerate(data):
            writer.writerow(row)

def download_weather_history(latitude, longitude, altitude, startDate, endDate):
    # Specify location and time range
    POINT = ms.Point(latitude, longitude, altitude)
    
    # Get nearby weather stations
    stations = ms.stations.nearby(POINT, limit=4)
    #print(stations)
    
    # Get daily data & perform interpolation
    ts = ms.daily(stations, startDate, endDate)
    df = ms.interpolate(ts, POINT).fetch()
    print(ts)
    
    if df is None:# No results found
        print('Failed to find new weather data')
        return []
    
    data = []
    for idx, row in df.iterrows():
        data.append([row.name.to_pydatetime().strftime('%Y-%m-%d'), row['tmin'] * 1.8 + 32, row['tmax'] * 1.8 + 32])

    # Plot line chart including average, minimum and maximum temperature
    #df.plot(y=[ms.Parameter.TEMP, ms.Parameter.TMIN, ms.Parameter.TMAX])
    #plt.show()
    print('Downloaded ' + len(data) + ' new data points')
    return data
    