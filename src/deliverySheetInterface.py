import datetime
import gspread
from google.oauth2.service_account import Credentials

def get_delivery_data(credentialsFileName, workbookName, sheetName):
    # Define scope
    scope = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/drive']

    # Load credentials
    creds = Credentials.from_service_account_file(credentialsFileName, scopes=scope)

    # Authorize client
    client = gspread.authorize(creds)

    # Open spreadsheet by name
    spreadsheet = client.open(workbookName)

    # Open first worksheet
    worksheet = spreadsheet.worksheet(sheetName)

    # Read all values and extract the relevant information
    return extract_delivery_data(worksheet.get_all_values())

def extract_delivery_data(allData):
    data = []
    
    for row_number, row in enumerate(allData):
        #print("at row " + str(row_number) + "; contents = " + str(row))
        # Ignore the header row
        if row_number == 0:
            continue;
            
        if len(row) < 3:
            raise ValueError(
                f"Row {row_number} does not have at least 3 columns: {row}"
            )
            
        try:
            datetime.datetime.strptime(row[0], '%Y-%m-%d')
        except Exception as e:
            #print(e + ']n' + row[0] + " is not a date")
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