import emailHelpers
import weatherData
import appConfig
import deliveryData
import sys
import datetime
import numpy as np
import csv
import matplotlib.pyplot as plt

def do_make_estimate(configFileName):
    # Read application configuration, weather data, and delivery data
    config = appConfig.read_values_from_xml(configFileName)
    updateDates = appConfig.read_values_from_xml(config['DATE_FILE'], 'OIL_ESTIMATOR_DATES')
    weather_data = weatherData.get_weather_history(float(config['LATITUDE']), float(config['LONGITUDE']), float(config['ELEVATION']))
    delivery_data = deliveryData.read_delivery_data()
    
    #check_for_missing_weather_data(weather_data)
    
    # Assemble email information into a helper object
    emailInfo = emailHelpers.EmailInformation(config['SENDER_EMAIL'], config['TO_EMAIL'])
    
    # Estimate the remaining oil level in the tank
    volume_to_fill = estimate_fill_volume(weather_data, delivery_data, float(config['REF_TEMP']), float(config['ALPHA']))
    remaining_volume = int(config['TANK_VOLUME']) - volume_to_fill
    print('Estimated fill volume = ' + str(int(volume_to_fill + 0.5)) + ' gal')
    print('Remaining volume = ' + str(int(remaining_volume + 0.5)) + ' gal')
    
    # Send emails as appropriate
    sent_email = False
    if remaining_volume < float(config['MIN_VOLUME']):
        sent_email = send_warning_email(emailInfo, volume_to_fill, remaining_volume)
    elif time_to_send_update_email(updateDates['LAST_EMAIL_SENT'], int(config['MAX_NO_EMAIL_DAYS'])):
        sent_email = send_update_email(emailInfo, volume_to_fill, remaining_volume)
    
    if sent_email:
        appConfig.write_to_xml(config['DATE_FILE'], datetime.date.today())
    
    # TODO:  If an error occurs, send email
    # TODO:  Once a year, send a summary email including average temperature over the season and total oil consumed?

def estimate_fill_volume(weather_data, delivery_data, reference_temp, alpha):
    lastDeliveryDate = None
    knownXs = []
    knownYs = []
    for delivery in delivery_data:
        if delivery[0] == 'missing':
            # Reset; need to ignore previous period's data
            lastDeliveryDate = None
            continue
        
        deliveryDate = datetime.datetime.strptime(delivery[0], '%Y-%m-%d').date()
        deliveryVolume = delivery[2]
        if lastDeliveryDate is None:
            lastDeliveryDate = deliveryDate
            continue
            
        xValues = compute_x_values(lastDeliveryDate, deliveryDate, weather_data, reference_temp)
        
        # TODO:  solve for every x delivery periods, so we have many sets of coefficients; use alpha to smooth between them (this will account better for thermostat changes, etc.)
        knownXs.append(xValues)
        knownYs.append(deliveryVolume)
        lastDeliveryDate = deliveryDate
    
    if False:
        print('Xs')
        print(knownXs)
        print('\nYs')
        print(knownYs)
    
    coefficients = np.linalg.lstsq(knownXs, knownYs)[0]
    
    #with open('test.csv', 'w', newline='') as csvfile:
    #    writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    #    writer.writerow(['x1', 'x2', 'y'])
    #    for idx, row in enumerate(knownXs):
    #        writer.writerow([row[0], row[1], knownYs[idx]])
    
    xValuesForEstimate = compute_x_values(lastDeliveryDate, datetime.date.today(), weather_data, reference_temp)
    #print(xValuesForEstimate)
    #print(coefficients)
    
    if False:
        estimatedFillVolumes = knownXs @ coefficients
        errorValues = estimatedFillVolumes - knownYs
        #print(errorValues)
        fig = plt.figure(figsize=(12, 12))
        ax = fig.add_subplot(projection='3d')
        knownXs = np.array(knownXs)
        ax.scatter(knownXs[:,0], knownXs[:,1], knownYs, c='r', marker='o')
        ax.scatter(knownXs[:,0], knownXs[:,1], estimatedFillVolumes, c='b', marker='o')
        ax.set_xlabel('Tavg Integral (deg F-day)')
        ax.set_ylabel('Days Below Tref (day)')
        ax.set_zlabel('Estimated Fill Volume (gal)')
        plt.show()
    
    lastDataDate = datetime.datetime.strptime(weather_data[-1][0], '%Y-%m-%d').date()
    print('Weather data exists through ' + str(lastDataDate))
    estimateOnLastDataDate = xValuesForEstimate[0] * coefficients[0] + xValuesForEstimate[1] * coefficients[1]
    print('Estimated fill volume on ' + str(lastDataDate) + ' is ' + str(estimateOnLastDataDate) + ' gal')
    
    # Since we don't have better data, assume the same average temperature as the last data day
    # Always add one more day, since tank will generally be filled tomorrow
    additionalDays = (datetime.date.today() - lastDataDate).days + 1
    print(str(additionalDays) + ' more days')
    lastDataTavg = 0.5 * (weather_data[-1][1] + weather_data[-1][2])
    estimateToday = (xValuesForEstimate[0] + additionalDays * lastDataTavg) * coefficients[0] + (xValuesForEstimate[1] + additionalDays) * coefficients[1]
    
    return estimateToday

def compute_x_values(start_date, end_date, weather_data, reference_temp):
    # TODO:  Make more efficient
    # TODO:  Need to check to make sure every day is accounted for?
    degree_days = 0
    days_below_ref_temp = 0
    for daily_temp in weather_data:
        d = datetime.datetime.strptime(daily_temp[0], '%Y-%m-%d').date()
        if d > end_date:
            break
        elif d > start_date:
            avg_temp = 0.5 * (daily_temp[2] + daily_temp[1])
            if avg_temp < reference_temp:
                degree_days += reference_temp - avg_temp
                days_below_ref_temp += 1
    
    return [degree_days, days_below_ref_temp]

def time_to_send_update_email(last_update_date, max_no_email_days):
    if last_update_date is None:
        return True
    
    lastDate = datetime.datetime.strptime(last_update_date, '%Y-%m-%d').date()
    today = datetime.date.today()
    return (today - lastDate).days

def send_warning_email(emailInfo, volume_to_fill, remaining_volume):
    emailHelpers.send_email(emailInfo.senderEmail, emailInfo.toEmails, 'Low Estimated Oil Level', generate_email_body(volume_to_fill, remaining_volume))
    return True

def send_update_email(emailInfo, volume_to_fill, remaining_volume):
    emailHelpers.send_email(emailInfo.senderEmail, emailInfo.toEmails, 'Estimated Oil Level Update', generate_email_body(volume_to_fill, remaining_volume))
    return True

def generate_email_body(volume_to_fill, remaining_volume):
    return 'Remaining oil level is estimated to be ' + str(int(remaining_volume + 0.5)) + ' gal; estimated fill volume is ' + str(int(volume_to_fill + 0.5)) + ' gal.'

def check_for_missing_weather_data(weather_data):
    firstDate = datetime.datetime.strptime(weather_data[0][0], '%Y-%m-%d').date()
    lastDate = datetime.datetime.strptime(weather_data[-1][0], '%Y-%m-%d').date()
    print('Weather data exists from ' + str(firstDate) + ' to ' + str(lastDate))
    
    expectedDate = firstDate
    for wd in weather_data:
        dataDate = datetime.datetime.strptime(wd[0], '%Y-%m-%d').date()
        while expectedDate != dataDate:
            print('No weather data for ' + str(expectedDate))
            expectedDate += datetime.timedelta(days=1)
        expectedDate += datetime.timedelta(days=1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python makeEstimate.py <xml_file>")
        sys.exit(1)
    
    do_make_estimate(sys.argv[1])
