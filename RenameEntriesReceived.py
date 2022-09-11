# -*- coding: utf-8 -*-
"""
Created on Sun Feb  7 19:58:14 2021

@author: Emily Storey

Note to self: Programming this is a virtual environment. To enable: 
$ Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process; .venv\scripts\activate

Another note to self... instead of $ pip list etc do $ python -m pip list. IDK why the former isn't working it gives this https://stackoverflow.com/questions/37220055/pip-fatal-error-in-launcher-unable-to-create-process-using

This is a program that I am using to replace the GTA Brews score 
sheet software that I built in matlab... 

Stuff that is still to do... 
4) write a README. 
5) make a 'gemfile' https://stackoverflow.com/questions/19280249/python-equivalent-of-a-ruby-gem-file https://fuzzyblog.io/blog/python/2019/09/10/building-a-python-requirements-txt-file.html


    
"""
# Import modules
from dotenv import load_dotenv
import easygui as eg
import numpy as np
import os
import pandas as pd
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfFileWriter, PdfFileReader
import re

load_dotenv()
TESSERACT_OCR_PATH = os.getenv('TESSERACT_OCR_PATH')
ENTRY_TRACKING_FILE = os.getenv('ENTRY_TRACKING_FILE')
DIGITAL_EVALUATION_FILE = os.getenv('DIGITAL_EVALUATION_FILE')
WORKING_DIRECTORY = os.getenv('WORKING_DIRECTORY')
JUDGING_PDF_FILE = os.getenv('JUDGING_PDF_FILE')

PDF_IMAGE_RESOLUTION = int(os.getenv('PDF_IMAGE_RESOLUTION'))

# Set a 4-tuple defining the left, upper, right, and lower coordinate 
# of the sticker crop box (inches) (assumes 8.5x11 pagesize). Convert to pixels.
sticker_pixel_location = tuple(np.array([3.6, 1.5, 7, 2.6]) * PDF_IMAGE_RESOLUTION)
judge_pixel_location = tuple(np.array([0.2, 1.5, 3.6, 2.6]) * PDF_IMAGE_RESOLUTION)

# Declare tesseract OCR path.
pytesseract.pytesseract.tesseract_cmd = TESSERACT_OCR_PATH

df_entries = pd.read_csv(WORKING_DIRECTORY + '\\' + ENTRY_TRACKING_FILE, delimiter=',')
df_entries['Pagenumber'] = df_entries['Pagenumber'].astype('object')

# Convert the pdf into images for iterating
pages = convert_from_path(WORKING_DIRECTORY + '\\' + JUDGING_PDF_FILE, PDF_IMAGE_RESOLUTION, grayscale=True)

def show_selector_box(entry_sticker):
    # stupid workaround because I can't pass the image as a variable.
    entry_sticker.save('temp.jpg')
    choice = eg.enterbox("Input entry number or choose Cancel to skip", image = 'temp.jpg')
    os.remove('temp.jpg')

    return choice


# For each page in the PDF, perform OCR. Update the tracking file to match entry number with page number.
for i in range(len(pages)):
    this_page = pages[i]

    # For each page, crop to where the stickers are, and do OCR.
    entry_sticker = this_page.crop(sticker_pixel_location)
    entry_text = str(((pytesseract.image_to_string(entry_sticker, config="-c tessedit_char_whitelist=0123456789MCls- --psm 6"))))
    
    # Try finding the entry number, based on its expected pattern.
    entry_number = re.findall(r'[MCls0-3]\d\-\d{3}', entry_text)
    if entry_number == []:
        # look in the judge sticker location in case the stickers are swapped
        judge_sticker = this_page.crop(judge_pixel_location)
        judge_text = str(((pytesseract.image_to_string(judge_sticker, config="-c tessedit_char_whitelist=0123456789MCls- --psm 6"))))
        entry_number = re.findall(r'[MCls0-3]\d\-\d{3}', judge_text)

    # Shouldn't be finding 2 entry numbers. If it does, run a human check.
    if len(entry_number) != 1:
        entry_number = [show_selector_box(entry_sticker)]
        if entry_number[0] is None:
            continue
        
    if entry_number != []:
        # If an entry number was found, update the corresponding row in the df and add its page number.
        row = df_entries[df_entries['Judging Number'].str.contains(entry_number[0].upper())]
        # df_entries.loc[row.index[0], 'Renamed'] += 1

        # If the row number is not found, do a human verification. Might not 
        # be a valid scoresheet. Maybe a category summary sheet got slipped in.
        if row.empty:
            entry_number = [show_selector_box(entry_sticker)]
            if entry_number[0] is None:
                continue
            else:
                row = df_entries[df_entries['Judging Number'].str.contains(entry_number[0].upper())]
                # If it's still not found, something's fucky. Skip it. 
                if row.empty:
                    continue

        # I'm doing things a weird way, pagenumber will either be nan (float), or a list. So to check for nan check for float.
        if type(df_entries.loc[row.index[0], 'Pagenumber']) == float:
            df_entries.loc[row.index[0], 'Pagenumber'] = [i]
        else: 
            df_entries.loc[row.index[0], 'Pagenumber'].append(i)

# once all of the pages have been gone through, filter the df to remove rows where pagenumber is na
df_withpages = df_entries.dropna()

# for each row in df_withpages, in a 'Results-Success' folder, write new pdfs of the pages indicated.
inputpdf = PdfFileReader(open(WORKING_DIRECTORY + '\\' + JUDGING_PDF_FILE, "rb"))

# Look for missing page numbers. Write to a text file with the missing ones. 
pgs_should_exist = set(range(inputpdf.numPages))
pgs_got_matched = set(sum(df_withpages['Pagenumber'].tolist(), []))
pgs_missing_matches = list(pgs_should_exist - pgs_got_matched)

with open(WORKING_DIRECTORY + '\\' + 'pages_missing_matches.txt', 'w') as outfile:
    if pgs_missing_matches != []:
        outfile.writelines('Pages not matched to an entry\n')
        outfile.writelines((str(i+1)+'\n' for i in pgs_missing_matches))
    else: 
        outfile.writelines('All pages in the pdf were matched to an entry')

# Source for pdf split https://stackoverflow.com/a/490203
# Write each file that succeeded to a separate pdf in a new folder.
Path(WORKING_DIRECTORY + '\\Results-Success\\').mkdir(parents=True, exist_ok=True)
for i in range(df_withpages.shape[0]) :
    row = df_withpages.iloc[i]
    output = PdfFileWriter()
    for j in range(len(row['Pagenumber'])) :
        output.addPage(inputpdf.getPage(row['Pagenumber'][j]))
    with open(WORKING_DIRECTORY + '\\Results-Success\\' + row['Judging Number'] + '.pdf', 'wb') as outputStream:
        output.write(outputStream)

# Write each page that failed to a separate pdf in a new folder.
Path(WORKING_DIRECTORY + '\\Results-Fail\\').mkdir(parents=True, exist_ok=True)
for i in pgs_missing_matches :
    output = PdfFileWriter()
    output.addPage(inputpdf.getPage(i))
    with open(WORKING_DIRECTORY + '\\Results-Fail\\' + 'page-%s.pdf' % (i+1), 'wb') as outputStream:
        output.write(outputStream)





### BELOW THIS POINT SHOULD REALLY BE ITS OWN FILE... 




# deal with the df_entries file. Flag entries that do not have exactly 2 pages found. 

# Load the digital evaluations list. Needs to be cleaned up because HTML tables... 
df_evaluations = pd.read_csv(WORKING_DIRECTORY + '\\' + DIGITAL_EVALUATION_FILE, delimiter=',').dropna(how = 'all').query('`Number` != "Number"').fillna(method = 'pad')
df_evaluations = df_evaluations[df_evaluations['Notes'].str.contains('Submitted|submitted')]

# add a column for digital evaluations, tally up how many are already in the system. 
def numSubmitted(row):
    if re.search('Submitted: (\d)', row['Notes']):
        return int(re.search('Submitted: (\d)', row['Notes']).group(1))
    else:
        return 0
df_evaluations['Evaluations Submitted'] = df_evaluations.apply(lambda row: numSubmitted(row), axis = 1)

# left join to put digital evaluations on the entries df. 
df_entries = df_entries.merge(
    df_evaluations[['Number', 'Evaluations Submitted']], 
    left_on = 'Judging Number', right_on = 'Number', how = 'left'
    )

# tally up number of pages found in ocr, and how many total entries (btwn digita/analog)
df_entries['Pages Found'] = df_entries['Pagenumber'].str.len()
df_entries['Total Evaluations'] = df_entries['Pages Found'] + df_entries['Evaluations Submitted']

# flag entries that don't have exactly 2 evaluations between digital and analog. 
df_entries[df_entries['Total Evaluations'] != 2].to_csv(WORKING_DIRECTORY + '\\entries_without_2_evaluations.csv', index = False, sep = ',')

df_entries[['Received', 'Judging Number', 'Pagenumber', 'Evaluations Submitted', 'Pages Found', 'Total Evaluations']].to_csv(WORKING_DIRECTORY + '\\' + ENTRY_TRACKING_FILE, index = False, sep = ',')
        