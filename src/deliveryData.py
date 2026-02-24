import datetime
import csv

def read_delivery_data():
    fileName = 'data/deliveryData.csv'
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
                datetime.datetime.strptime(row[0], '%Y-%m-%d')
            except:
                #print(row[0] + " is not a date")
                data.append(['missing', None, None])
                continue
                    
            try:
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