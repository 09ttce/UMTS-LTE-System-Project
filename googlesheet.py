
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def update_values(range_name, _values):
  
  creds = None

  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "/home/admin2137/Programy/Python/UMTS_LTE_Project/client_auth.json", SCOPES)
  
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
      with open("token.json", "w") as token:
       token.write(creds.to_json())

  try:
    service = build("sheets", "v4", credentials=creds)

    values = _values
    data = [
        {"range": range_name, "values": values},
        # Additional ranges to update ...
    ]
    body = {"valueInputOption": "USER_ENTERED", "data": data}
    result = (
        service.spreadsheets()
        .values()
        .batchUpdate(spreadsheetId="1O465t4UPJ9pJu-AN4WFdYOTZHL6uD3d_UAXTRzaOir0", body=body)
        .execute()
    )
    print(f"{(result.get('totalUpdatedCells'))} cells updated.")
    return result
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error
