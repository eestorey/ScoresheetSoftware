from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
BCOEM_EXPORT_ENTRIES_FILE = os.getenv('BCOEM_EXPORT_ENTRIES_FILE')
WORKING_DIRECTORY = os.getenv('WORKING_DIRECTORY')
ENTRY_TRACKING_FILE = os.getenv('ENTRY_TRACKING_FILE')

# Import a list of all entries to a pandas dataframe. 
dfOld = pd.read_csv(WORKING_DIRECTORY + '\\' + BCOEM_EXPORT_ENTRIES_FILE, delimiter=',', encoding='latin-1')

# Then make a new dataframe with columns: JudgingNumber, Received, Renamed.
dfNew = dfOld[['Received', 'Judging Number']].copy()
dfNew['Judging Number'] = dfNew['Judging Number'].str.upper()
dfNew.insert(2, 'Pagenumber', '')

dfNew.to_csv(WORKING_DIRECTORY + '\\' + ENTRY_TRACKING_FILE, index = False, sep = ',')