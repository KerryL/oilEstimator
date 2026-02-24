#import emailHelpers
import weatherData
import appConfig
import deliveryData
import sys

def do_make_estimate(configFileName):
    config = appConfig.read_values_from_xml(configFileName)
    #print(config)
    updateDates = appConfig.read_values_from_xml(config['DATE_FILE'], 'OIL_ESTIMATOR_DATES')
    #print(updateDates)
    weather_data = weatherData.get_weather_history(float(config['LATITUDE']), float(config['LONGITUDE']), float(config['ELEVATION']))
    #print(weather_data)
    delivery_data = deliveryData.read_delivery_data()
    #print(delivery_data)
    
    remaining_oil = estimate_oil_level(weather_data, delivery_data)
    sent_email = false
    if remaining_oil < float(config['MIN_VOLUME']):
        sent_email = send_warning_email()
    
    # TODO
    #8. Else if it's been 7 days since last email, send "I'm still working" email; write last update date + last email date
    
    if sent_email:
        # TODO
        #9. Else, write last update date (keep last email date unchanged)
        a = 0
    
    # TODO
    #10. If an error occurs, send email

def estimate_oil_level():
    # TODO
    return 0

def send_warning_email():
    # TODO
    return 0

def send_update_email():
    # TODO
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python makeEstimate.py <xml_file>")
        sys.exit(1)
    
    # TODO:  Read everything from the same file; call this function with config file name as argument
    do_make_estimate(sys.argv[1])