from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
BCOEM_EXPORT_ENTRIES_FILE = os.getenv('BCOEM_EXPORT_ENTRIES_FILE')
ENTRY_TRACKING_FILE = os.getenv('ENTRY_TRACKING_FILE')

# Import a list of all entries to a pandas dataframe. 
dfOld = pd.read_csv(BCOEM_EXPORT_ENTRIES_FILE, delimiter=',')

# Then make a new dataframe with columns: JudgingNumber, Received, Renamed.
dfNew = dfOld[['Received', 'Judging Number']].copy()
dfNew['Judging Number'] = dfNew['Judging Number'].str.upper()
dfNew.insert(2, 'Renamed', 0)

dfNew.to_csv(ENTRY_TRACKING_FILE, index = False, sep = ',')