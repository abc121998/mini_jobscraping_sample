# Scraping Linked-In and Indeed to Simplify Job Search
### Coding Example #2 
<br>
<b> About Project: </b><br>
<br>
This project is a modified version of a larger Flask 
application for job application purposes. It's significantly smaller and data is stored in csvs 
rather than a mysql database. Users can search and scrape two job board sites (linkedin and indeed). 
It processes the free text from job postings using spaCy to find information like education requirements, 
expected years of experience, salaries, and skills. The created dataframe can be displayed in a html page 
or saved and exported as a csv. Once a csv is stored it can be read into a dataframe at a later date.
Users can also add new job results into an existing dataframe. Finally, rows with closed postings can be dropped from a dataframe.
The larger application is much more interactive and comprehensive, including an internal search page and job application tracking.
If you're interested in the full version, you can contact me below.
<br>

<b>Date Last Updated: </b> 7/19/23 
<br>
<br>
<b>Instructions:</b> <br>
1. install requirements.txt 
2. type "python -m spacy download en_core_web_sm" in the command line
3. run jobscraping-sample.py
<br>
<b>Contact: </b><br>
Author: Abigail (Abbey) Cotton <br>
E-mail: abig3@umbc.edu
