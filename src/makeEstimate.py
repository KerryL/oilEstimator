import emailHelpers
import weatherData
import appConfig
import deliveryData
import sys
import datetime
import numpy as np
import csv

def do_make_estimate(configFileName):
    # Read application configuration, weather data, and delivery data
    config = appConfig.read_values_from_xml(configFileName)
    updateDates = appConfig.read_values_from_xml(config['DATE_FILE'], 'OIL_ESTIMATOR_DATES')
    weather_data = weatherData.get_weather_history(float(config['LATITUDE']), float(config['LONGITUDE']), float(config['ELEVATION']))
    delivery_data = deliveryData.read_delivery_data()
    
    # Assemble email information into a helper object
    emailInfo = emailHelpers.EmailInformation(config['SENDER_EMAIL'], config['TO_EMAIL'])
    
    # Estimate the remaining oil level in the tank
    remaining_oil = estimate_oil_level(weather_data, delivery_data, float(config['REF_TEMP']), float(config['ALPHA']))
    print('Estimated remaining oil = ' + str(remaining_oil) + ' gal')
    
    # Send emails as appropriate
    sent_email = False
    if remaining_oil < float(config['MIN_VOLUME']):
        sent_email = send_warning_email(emailInfo, remaining_oil)
    elif time_to_send_update_email(updateDates['LAST_EMAIL_SENT'], int(config['MAX_NO_EMAIL_DAYS'])):
        sent_email = send_update_email(emailInfo, remaining_oil)
    
    if sent_email:
        appConfig.write_to_xml(config['DATE_FILE'], datetime.date.today())
    
    # TODO: If an error occurs, send email

def estimate_oil_level(weather_data, delivery_data, reference_temp, alpha):
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
    
    #print('Xs')
    #print(knownXs)
    #print('\nYs')
    #print(knownYs)
    coefficients = np.linalg.lstsq(knownXs, knownYs)[0]
    
    #with open('test.csv', 'w', newline='') as csvfile:
    #    writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    #    writer.writerow(['x1', 'x2', 'y'])
    #    for idx, row in enumerate(knownXs):
    #        writer.writerow([row[0], row[1], knownYs[idx]])
    
    xValuesForEstimate = compute_x_values(lastDeliveryDate, datetime.date.today(), weather_data, reference_temp)
    #print(xValuesForEstimate)
    #print(coefficients)
    
    return xValuesForEstimate[0] * coefficients[0] + xValuesForEstimate[1] * coefficients[1]

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

def send_warning_email(emailInfo, oilVolume):
    emailHelpers.send_email(emailInfo.senderEmail, emailInfo.toEmails, 'Low Estimated Oil Level', 'Estimated oil level is ' + str(int(oilVolume)) + ' gal.')
    return True

def send_update_email(emailInfo, oilVolume):
    emailHelpers.send_email(emailInfo.senderEmail, emailInfo.toEmails, 'Estimated Oil Level Update', 'Estimated oil level is ' + str(int(oilVolume)) + ' gal.')
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python makeEstimate.py <xml_file>")
        sys.exit(1)
    
    do_make_estimate(sys.argv[1])
