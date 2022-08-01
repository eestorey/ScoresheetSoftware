# -*- coding: utf-8 -*-
"""
Created on Sun Feb  7 19:58:14 2021

@author: Midnight

This is a program that I am using to practice python, and also to replace my 
score sheet software that I built in matlab... Because $$. One of the main 
goals of this software is to get compensated by the club. Because $$. 

---
    
"""

# Import the modules
import tkinter as tk
import tkinter.filedialog as fd
# from PIL import Image, ImageOps
import pytesseract
# import sys
from pdf2image import convert_from_path
# import os
import numpy as np
import re
import pandas as pd

# Make sure the program can find the tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Midnight\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

#%% Set things up, import the csv of all entries and initialize a data structure for checking if entry was received, renamed.

# Import a list of all entries to a pandas dataframe. 
dfOld = pd.read_csv('Brew_Slam_2019_Entries_All_All_11-20-2019.csv', delimiter=',')

# Then make a new dataframe with columns: JudgingNumber, Received, Renamed.
dfNew = pd.DataFrame([dfOld['Received'], dfOld['Judging Number']])
dfNew = dfNew.T
dfNew.insert(2, 'Renamed', 0)


#%% Convert PDFs to images and crop them to area

# Get the paths of files to be processed. Store in an array named fileList
root = tk.Tk()
fileList = fd.askopenfilenames(parent=root, title='Select PDFs', filetypes=[('pdf file', '*.pdf')])

# For each PDF, convert into images. 
for thisFile in len(fileList):
    pages = convert_from_path(fileList[thisFile], 500, grayscale=True)
    entryNums = ['', '']
    for thisPage in len(pages):
        # For each page, crop to where the judge and entry stickers are, and do OCR.
        judgeImage = pages[thisPage].crop((100, 750, 1800, 1300))
        textJudge = str(((pytesseract.image_to_string(judgeImage))))
        entryImage = pages[thisPage].crop((1800, 750, 3500, 1300))
        textEntry = str(((pytesseract.image_to_string(entryImage))))
        
        # Try finding the entry number, based on its expected pattern.
        judgingNo = re.findall(r'[MC\d]\d\-\d\d\d', textEntry)
        if judgingNo == []:
            # look in the other location in case the stickers are swapped
            judgingNo = re.findall(r'[MC\d]\d\-\d\d\d', textJudge)
        if judgingNo != []:
            # If it successfully found an entry number, store it. 
            entryNums[thisPage] = judgingNo[0]
        
    if entryNums[0] == entryNums[1]:
        # if both entry numbers agree, great! Find the row index in the data frame. Make sure case insensitive.
        temp = dfNew['Judging Number'].str.lower().isin([entryNums[0].lower()])
        row = list(dfNew['Judging Number'][temp].index)
        
        # Up the counter in the associated row of the renamed column by 1. 
        # This will allow us to catch duplicate renamings.
        dfNew['Renamed'][row[0]] = dfNew['Renamed'][row[0]] + 1
        
        "A value is trying to be set on a copy of a slice from a DataFrame"

        "See the caveats in the documentation: https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy"
        
    else:
        