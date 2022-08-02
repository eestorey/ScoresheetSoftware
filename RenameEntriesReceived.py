# -*- coding: utf-8 -*-
"""
Created on Sun Feb  7 19:58:14 2021

@author: Emily Storey

Note to self: Programming this is a virtual environment. To enable: 
$ Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process; 
$ .venv\scripts\activate

This is a program that I am using to replace the GTA Brews score 
sheet software that I built in matlab... 

---
    
"""
# Import modules
from dotenv import load_dotenv
import numpy as np
import os
import pandas as pd
from pdf2image import convert_from_path
import pytesseract
import re
import tkinter as tk
import tkinter.filedialog as fd

load_dotenv()
TESSERACT_OCR_PATH = os.getenv('TESSERACT_OCR_PATH')
ENTRY_TRACKING_FILE = os.getenv('ENTRY_TRACKING_FILE')

# Declare tesseract OCR path. Put this location in an ENV file eventually...
pytesseract.pytesseract.tesseract_cmd = TESSERACT_OCR_PATH

df_entries = pd.read_csv(ENTRY_TRACKING_FILE, delimiter=',')

# Get the paths of files to be processed. Store them. 
working_directory = os.getcwd()
file_list = [file for file in os.listdir() if re.findall(r'.pdf$', file)]

# For each PDF, convert into images. Perform OCR. Do stuff if there is/isn't a match between pages on the pdf.
for this_file in file_list:
    pages = convert_from_path(working_directory + '\\' + this_file, 500, grayscale=True)
    potential_entry_numbers = []
    for this_page in pages:
        # For each page, crop to where the stickers are, and do OCR.
        entry_sticker = this_page.crop((1800, 750, 3500, 1300))
        entry_text = str(((pytesseract.image_to_string(entry_sticker))))
        
        # Try finding the entry number, based on its expected pattern.
        entry_number = re.findall(r'[MC\d]\d\-\d\d\d', entry_text)
        if entry_number == []:
            # look in the judge sticker location in case the stickers are swapped
            judge_sticker = this_page.crop((100, 750, 1800, 1300))
            judge_text = str(((pytesseract.image_to_string(judge_sticker))))
            entry_number = re.findall(r'[MC\d]\d\-\d\d\d', judge_text)
        if entry_number != []:
            # If an entry number was found, store it. 
            potential_entry_numbers.append(entry_number[0].upper())
        
    if np.unique(potential_entry_numbers).size == 1:
        # Find the row index in the data frame. 
        row = df_entries[df_entries['Judging Number'].str.contains(potential_entry_numbers[0])]

        # Do something to short circuit if that entry number is not found for some reason... 
        # Otherwise, increase the value in the 'Renamed' column of the appropriate row of the df. 
        # The goal of this is to ensure we are catching duplicate renamings which may occur. 
        if row.size: 
            os.rename(this_file, potential_entry_numbers[0] + '.pdf')
            df_entries.loc[row.index[0], 'Renamed'] += 1
        # else :
            # do something if the entry number is not found in the csv file
    # else: 
        # do something if the entry numbers between pages of the pdf do not agree. 

df_entries.to_csv(ENTRY_TRACKING_FILE, index = False, sep = ',')
        