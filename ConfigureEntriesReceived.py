import pandas as pd

# Import a list of all entries to a pandas dataframe. 
dfOld = pd.read_csv('Brew_Slam_2019_Entries_All_All_11-20-2019.csv', delimiter=',')

# Then make a new dataframe with columns: JudgingNumber, Received, Renamed.
dfNew = dfOld[['Received', 'Judging Number']].copy()
dfNew['Judging Number'] = dfNew['Judging Number'].str.upper()
dfNew.insert(2, 'Renamed', 0)

dfNew.to_csv('Entries_Received_Renamed.csv', index = False, sep = ',')