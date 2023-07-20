from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import contractions,glob,spacy,json,webbrowser
import pandas as pd
from spacy.matcher import Matcher,PhraseMatcher
from spacy.tokens import Span
from bs4 import BeautifulSoup

nlp = spacy.load("en_core_web_sm")

import time,datetime,lxml,requests,re

SKILL_GROUPS = ['Active Learning', 'Administrative Assistance', 'Analytical Reasoning', 'Anthropology',
                'Architecture', 'Artificial Intelligence', 'Biomedical Engineering', 'Bookkeeping', 'Cardiology',
                'Collaborative Style', 'Communication Disorders', 'Compensation & Benefits', 'Computer Graphics',
                'Computer Hardware', 'Computer Networking', 'Constitutional Law', 'Creativity Skills',
                'Criminal Law', 'Customer Service Systems', 'Data Science', 'Data Storage Technologies',
                'Data-driven Decision Making', 'Delivery Operations', 'Development Tools', 'Digital Literacy',
                'Documentation', 'Earth Science', 'Economics', 'Editing', 'Educational Administration',
                'Educational Research', 'Emergency Medicine', 'Enterprise Software', 'Environmental Science',
                'Evolutionary Biology', 'Family Medicine', 'Flexible Approach', 'Game Development',
                'Gastroenterology', 'General Surgery', 'Genetic Engineering', 'Graphic Design',
                'Healthcare Management', 'Higher Education', 'History', 'Human Computer Interaction',
                'Information Management', 'Insurance', 'International Law', 'Inventory Management', 'Journalism',
                'K-12 Education', 'Law', 'Leadership', 'Legislation', 'Library Science', 'Linguistics', 'Literature',
                'Manufacturing Operations', 'Mathematics', 'Mobile Application Development', 'Nanotechnology',
                'Natural Language Processing', 'Neurology', 'Nonprofit Management', 'Nursing', 'Obstetrics',
                'Oncology', 'Ophthalmology', 'Oral Communication', 'Oral Comprehension', 'Organic Chemistry',
                'Orthopedic Surgery', 'Paediatrics', 'Pathology', 'Pharmaceutical Manufacturing', 'Pharmaceutics',
                'Photography', 'Physiology', 'Plastics', 'Politics', 'Power Systems', 'Problem Solving',
                'Procurement', 'Product Development', 'Product Marketing', 'Product Testing', 'Project Management',
                'Psychiatry', 'Psychology', 'Public Health', 'Public Policy', 'Radiology', 'Reading Comprehension',
                'Research', 'Robotics', 'Scientific Computing', 'Social Media', 'Social Services', 'Sociology',
                'Software Development', 'Software Testing', 'Teaching', 'Technical Support', 'Telecommunications',
                'Time Management', 'Urban Planning', 'Urology', 'Utilities', 'Veterinary Medicine', 'Video',
                'Volunteer Management', 'Web Development', 'Writing']

columns = ['job_id','title','company','location','date_posted','website','url','employment_type','level','industry',
                 'job_functions','skills', 'education', 'experience','salary','raw_text','count_public_health',
                 'count_epidemiology','count_research', 'count_develop','count_data_science','count_analysis',
                 'count_software','count_programmer']

#actions user can take
def home():
    print('This is a Jobscraping Program for demonstration purposes (Based on a more complex Flask Application that includes a MySQL Database)')

    #users need to first create a dataframe of job postings or upload an old one
    action = input('Would you like to:\n(1)Create a new dataframe and csv?\n(2) Upload an old csv?\n(q) quit')
    while action not in ['1','2','q']:
        action = input('Invalid input. Try again!')
    job_df = pd.DataFrame(columns=columns)

    #continues until user quits
    while action != 'q':
        #create a dataframe
        if action == '1':
            keywords = getSearchTerms()
            if keywords != ['back']:
                job_df = createJobDataframe(keywords)
        #upload an old dataframe
        if action == '2':
            replace = ''
            if len(job_df) > 0:
                replace = input('Would you like to replace the current dataframe with the uploaded one (y/n/back to go back)')
                while replace not in ['y','n','back']:
                    replace = input('Invalid input. Try again:')
            temp = uploadJobDataFrame()
            if replace.lower() == 'y' or len(job_df)==0:
                job_df = temp
            else:
                job_df = pd.concat([job_df,temp])
        #add new postings to the dataframe
        if action == '3':
            keywords = getSearchTerms()
            if keywords != ['back']:
                job_df = searchSites(keywords, job_df)
        #delete jobs that have already closed
        if action == '4':
            job_df = closeJobPostings(job_df)
        #export a csv of the dataframe
        if action == '5':
            filename = input('Enter what you want the exported csv file to be called (default=job_posting_df.csv) (back to go back)')
            while 'csv' not in filename and filename != '' and filename!='back':
                filename = input('does not have a csv extension, try again or press enter to use default (back to go back)')
            if filename == 'back':
                continue
            if filename == '':
                filename = 'job_posting_df.csv'
            if filename != 'back':
                print('exported')
                job_df.to_csv(filename)
        #display the dataframe as a html page in the default browser
        if action == '6':
            html = job_df.drop('raw_text',axis=1).to_html()
            with open('job_df.html','w',encoding="utf-8") as html_file:
                html_file.write(html)
            webbrowser.open_new_tab('job_df.html')
        #asks user for their next action
        action = input('Would you like to:\n(1)Create a new dataframe and csv?\n(2) Upload an old csv?\n'
                       ' (3)Search and Add to a dataframe? \n (4)Delete closed job postings in a dataframe?'
                       '\n(5) Export a dataframe as a csv? \n  (6)Display dataframe\n q) quit')
#get the keywords that we're searching for
def getSearchTerms():
    search = input('What key words are you search for (use a comma to separate terms)\nDefault is: '
                   'Public+Health, Data+Analyst, Research, Data+Science, Epidemiology (type back to go back)')
    #the default search terms
    keywords = ['Public+Health', 'Data+Analyst', 'Research', 'Data+Science', 'Epidemiology']
    #if the user specifies keywords
    if search != '':
        #if there is more than one term, split the string into a list of terms
        if ',' in search:
            keywords = search.split(',')
        #otherwise simply put the search term in a list
        else:
            keywords = [search]
    return keywords

#create a new job posting dataframe and associated csv
def createJobDataframe(keywords=['Public+Health', 'Data+Analyst', 'Research', 'Data+Science', 'Epidemiology']):

    #get a filename for the csv
    filename = input('Enter the file name for the csv you want create (default=job_posting_df.csv)')
    while 'csv' not in filename and filename != '':
        filename = input('does not have a csv extension, try again or press enter to use default')
    #create the dataframe, search all sites, and write a csv
    job_df = pd.DataFrame(columns=columns)
    job_df = searchSites(keywords,job_df)
    if filename == '':
        job_df.to_csv('job_posting_df.csv')
    else:
        job_df.to_csv(filename)
    return job_df

#read a csv file of job postings and create a dataframe
def uploadJobDataFrame():
    filename = input('Enter the file name for the csv you want uploaded (default=job_posting_df.csv)')
    while filename not in glob.glob('*.csv') and filename!='':
        filename = input('csv file not in directory, try again or press enter to use default')
    if filename == '':
        job_df = pd.read_csv('job_posting_df.csv')
    else:
        job_df = pd.read_csv(filename)
    return job_df

#add to existing dataframe
def addToDataFrame(df,keywords=['Public+Health', 'Data+Analyst', 'Research', 'Data+Science', 'Epidemiology']):
    job_df = searchSites(keywords, df)
    return job_df

def addPosting(postData):

    #find out if the posting is from linkedin or indeed
    if 'linkedin' in postData['url']:
        source = 'LinkedIn'
    elif 'indeed' in postData['url']:
        source = 'Indeed'
    else:
        source = ''

    #create a basic dictionary for job's data
    new_posting = {'job_id':postData['job_id'],'title':postData['title'],'company':postData['company'],'location':postData['location'],
                   'url':postData['url'],'website':source}

    #add the date posted if that's found
    if 'datePosted' in postData:
        new_posting['date_posted'] = postData['datePosted']
    #add company industries if possible
    if 'industry' in postData:
        new_posting['industry'] = [re.sub(r'^[aA]nd','',indus.strip()).strip() for indus in postData['industry']]
    #add job functions if possible
    if 'job_functions' in postData:
        new_posting['job_functions'] = [re.sub(r'^[aA]nd', '', function.strip()).strip() for function in postData['job_functions']]
    #add level of job if possible
    if 'level' in postData:
        new_posting['level'] = [re.sub(r'^[aA]nd', '', level.split()[0].strip()).strip() for level in postData['level']]
    #add type of employment if possible
    if 'employment_type' in postData:
        new_posting['employment_type'] = [etype for etype in postData['employment_type']]

    #if we have the html page for job details
    if 'desc_html' in postData:

        #get the raw html and found skills
        textData = getDescription(postData['desc_html'])
        new_posting['raw_text'] = postData['desc_html']
        new_posting['skills'] = textData['skills']

        # get the keyword counts
        fieldDic = textData['fieldwords']
        new_posting['count_public_health'] = fieldDic['public health']
        new_posting['count_epidemiology'] = fieldDic['epidemiology']
        new_posting['count_research'] = fieldDic['research']
        new_posting['count_develop'] = fieldDic['develop']
        new_posting['count_data_science'] = fieldDic['data science']
        new_posting['count_analysis'] = fieldDic['analy']
        new_posting['count_software'] = fieldDic['software']
        new_posting['count_programmer'] = fieldDic['programm']

        #get a cleaned salary
        if 'salary' not in postData:
            salary_dic = textData['salary']
        else:
            salary_dic = cleanSalary([postData['salary'].replace(',','')])
        new_posting['salary'] = salary_dic
        #get experience info
        new_posting['experience'] = [' '.join(ex) for ex in textData['experience']]
        #get education info

        new_posting['education'] = textData['education']

    return new_posting

#find a job id based on title,company,and location in the dataframe
def findJobId(title,company,loc,df):
    return df.loc[(df['title']==title) & (df['company']==company) & (df['location']==loc),:]

#for linkedin: automatically scroll down to get all the possible jobs
def scroll(timeout,driver):
    try:
        scroll_pause_time = timeout
        # Get scroll height
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(scroll_pause_time)
            if driver.find_element(By.CLASS_NAME, "infinite-scroller__show-more-button").is_displayed():
                driver.execute_script("document.getElementsByClassName('infinite-scroller__show-more-button')[0].click()")
            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # If heights are the same it will exit the function
                break
            last_height = new_height
    except:
        print('scrolling error')
    return BeautifulSoup(driver.page_source, 'html.parser').findAll('div','base-search-card')

#start the webdriver for scraping
def startDriver():
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    return driver

#search through each site using given keywords and add them to the dataframe
def searchSites(keywords,df):
    driver = startDriver()
    for key in keywords:
        print(key)
       # try:
            #create a temporary dataframe from the list of job dictionaries from LinkedIn
        temp = pd.DataFrame.from_records(scrapeLinkedIn(key.lower(), driver, df))
            #if temp isn't empty add it to the original df
        if len(temp) > 0:
            df = pd.concat([df,temp],ignore_index=True)
        #except:
         #   print('unknown error scraping from Linkedin')

        try:
            # create a temporary dataframe from the list of job dictionaries from Indeed
            temp = pd.DataFrame.from_records(scrapeIndeed(key.lower(), driver, df))
            # if temp isn't empty add it to the original df
            if len(temp) > 0:
                df = pd.concat([df,temp],ignore_index=True)
        except:
            print('unknown error scraping from Indeed')

    driver.close()
    return df

#go to a specific job posting url and add it to the dataframe
def goToSpecificURL(url,df):
    driver = startDriver()
    driver.get(url)
    post = BeautifulSoup(driver.page_source,  'html.parser')
    #if its on linkedin
    if 'linkedin' in url:
        #get cleaned title,company,and location from page
        title = post.find('h1','top-card-layout__title').get_text()
        company = post.find('a','topcard__org-name-link topcard__flavor--black-link').get_text()
        if company:
            company = company.strip()
        location = post.find('span','topcard__flavor topcard__flavor--bullet').get_text()
        if location:
            location = location.strip()
        #only add it if it doesn't exist in the dataframe
        exists = findJobId(title, company, location,df)
        if len(exists) > 0:
            print(title, company, location,'is already in dataframe')
            return exists[0].idJobBoard

        #set up job record and add it to the dataframe as a new row
        job = {'title': title, 'company': company, 'location': location,'datePosted':None,'url':url}
        job['datePosted'] = None
        job = addPosting(scanLinkedInPosting(job))
        job['job_id'] = len(df) + 1
        df = df.concat([df,pd.DataFrame.from_dic(job)],ignore_index=True)
        return df

    #if its on indeed
    elif 'indeed' in url:
        #get data from html
        url = post.find('link',{'rel':'canonical'})['href']
        title = post.find('h1','jobsearch-JobInfoHeader-title').find('span').get_text()
        company = post.find('div', {'data-company-name':'true'}).get_text()
        location = post.find('div', 'css-6z8o9s').find('div').get_text()
        level = ['entry']

        #only adds a job if its not already in the dataframe
        exists = findJobId(title, company, location,df)
        if len(exists) > 0:
            print(title, company, location)
            return exists[0].idJobBoard

        #create a new row for job and add it to dataframe
        job = {'title': title, 'company': company, 'location': location, 'level': level,'url':url}
        job = addPosting(scanTextIndeed(driver, job))
        job['job_id'] = len(df) + 1
        df = df.concat([df, pd.DataFrame.from_dic(job)],ignore_index=True)
        return df
    else:
        print('Not a indeed or linkedin url (cannot be scraped)')
    driver.close()
    return

#scrapes the LinkedIn search page
def scrapeLinkedIn(key,driver,df):

    #create needed url
    location = 'Washington District of Columbia United States'
    position_level = 'f_E=2'
    past = {'Any Time': '', 'Past Month': '&f_TPR=r2592000&', 'Past Week': '&f_TPR=r604800&',
            'Past Day': '&f_TPR=r86400&'}
    URL = "https://www.linkedin.com/jobs/search?keywords=" + key + "&location=" + location + past['Past Week'] \
          + "&distance=10&" + position_level

    #make driver wait before accessing the url and scrolling down to get all the cards in the search html
    driver.implicitly_wait(5)
    driver.get(URL)
    soup_cards = scroll(1.5,driver)
    post_data = []

    #go through each job card on the search page to find title, location, date posted, and job posting url
    for card in soup_cards:

            title = ''
            if card.find("span", "sr-only"):
                title = card.find("span", "sr-only").text.strip()
            company = ''
            if card.find("h4", "base-search-card__subtitle"):
                company = card.find("h4", "base-search-card__subtitle").text.strip()
            location = ''
            if card.find("span", "job-search-card__location"):
                location = card.find("span", "job-search-card__location").text.strip()
            exists = findJobId(title, company, location,df)

            #skip card if the job is either already in the dataframe or is in the list of recently found jobs
            if len(exists) > 0:
                print(title,company,location,"is already in dataframe")
                continue
            if (title,company,location) in [(x['title'],x['company'],x['location']) for x in post_data]:
                print(title, company, location, "will already be added")
                continue

            #create a dictionary of known job data
            job = {'title': title, 'company': company, 'location': location}
            if card.find("time")['datetime']:
                date = card.find("time")['datetime']
                job['datePosted'] = date
            #if we can find the job's specific url, scrape again to get more detailed info
            if card.find('a', 'base-card__full-link'):
                job['url'] = card.find('a', 'base-card__full-link')['href']
                scanLinkedInPosting(job)
            #set the job id and add it to the list of new job recordss
            job['job_id'] = len(df) + len(post_data) + 1
            post_data.append(addPosting(job))
    return post_data

#scrapes details from the specific job posting on Linkedin
def scanLinkedInPosting(job):
    #request url page
    page = requests.get(job['url'],headers={
        "User-Agent" : "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"})
    #if the result is a 429 status code, wait 15 secs and try again
    if page.status_code == 429:
        time.sleep(15)
        page = requests.get(job['url'],headers={
        "User-Agent" : "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"})
    detailed_post = BeautifulSoup(page.content, 'lxml')

    #get job criteria information (employee level/type,job function, and company industries)
    job_criteria_list = detailed_post.findAll("li", "description__job-criteria-item")
    for criteria in job_criteria_list:
        if 'Seniority level' in criteria.find('h3').text:
            job['level'] = [val for val in criteria.find('span').text.strip().split(',')]
        if 'Employment type' in criteria.find('h3').text:
            job['employment_type'] = [val for val in criteria.find('span').text.strip().split(',')]
        if 'Job function' in criteria.find('h3').text:
            job['job_functions'] = [val for val in criteria.find('span').text.strip().split(',')]
        if 'Industries' in criteria.find('h3').text:
            job['industry'] = [val for val in criteria.find('span').text.strip().split(',')]
    #get the raw html and remove extra symbols if needed
    if detailed_post.find("div", "show-more-less-html__markup"):
        job['desc_html'] = removeSymbols(str(detailed_post.find("div", "show-more-less-html__markup")))
    else:
        job['desc_html'] = ""
    return job

#scrape the search page for Indeed
def scrapeIndeed(key,driver,df):

    #create the desired url
    location = 'Washington%2C%20DC&radius=10'
    exp_level = '0kf%3Aexplvl(ENTRY_LEVEL)%3B'
    past = {'Any Time': '', 'Past Two Weeks': '&fromage=14&', 'Past Week': '&fromage=7&','Past 3 days':'&fromage=3%=&',
            'Past Day': '&fromage=1&'}
    URL = 'https://www.indeed.com/jobs?q=' + key + '&l=' + location + '&sc=' + exp_level + past['Past Two Weeks']

    #force the driver to wait for a few secs before accessing url
    driver.implicitly_wait(5)
    driver.get(URL)

    #find the forward button on the page
    forward_button = driver.find_elements(By.CSS_SELECTOR,"[aria-label='Next Page']")
    post_data = []
    #until we get to the last page of results, go through each result and then press the forward arrow
    while forward_button:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        #go through all results on page
        for row in soup.findAll('td', 'resultContent'):
            #skip if whats found is a hiring event
            if row.find('a','jcs-JobTitle')['data-hiring-event'] == True:
                print('hiring event, exclude')
                continue
            #try to find the job's Indeed id, title, company, and location
            try:
                j_id = row.find('a','jcs-JobTitle')['data-jk']
                title = row.find('span', title=True).text
                company = row.find('span', 'companyName').text
                location = row.find('div', 'companyLocation').text
            except:
                print('missing info')
                continue
            level = ['entry']

            #skip if the current job posting is already in the dataframe or recently found posts
            exists = findJobId(title, company, location,df)
            if len(exists) > 0:
                print(title,company,location,'is already in dataframe')
                continue
            if (title,company,location) in [(x['title'],x['company'],x['location']) for x in post_data]:
                print(title, company, location, "will already be added")
                continue

            #create a dictionary for the job including the specific url
            job = {'title': title, 'company': company, 'location': location, 'level': level}
            job['url'] = 'http://indeed.com/viewjob?jk=' + j_id
            #try to click the job in order to get the details
            try:
                det_button = driver.find_element(By.CSS_SELECTOR, "a[data-jk='"+j_id+"']")
                driver.execute_script("arguments[0].click()", det_button)
                job = scanTextIndeed(driver,job)
            except TimeoutException:
                print('webdriver timed out',job['title'],job['company'],job['location'],job['url'])
            except:
                print('unable to click posting',job['title'],job['company'],job['location'],job['url'])
            #get the job's remaining information
            job['job_id'] = len(df) + len(post_data) + 1
            post_data.append(addPosting(job))
        #fix visibility issues with some of the elements before clicking on the arrow for the next page
        elements = driver.find_elements(By.CSS_SELECTOR,"div[class^='gnav-CookiePrivacy']")
        for el in elements:
            driver.execute_script("arguments[0].style.visibility='hidden'", el)
        forward_button[0].click()
        time.sleep(.5)
        forward_button = driver.find_elements(By.CSS_SELECTOR,"[aria-label='Next Page']")

    return post_data

#get the details for an Indeed posting
def scanTextIndeed(driver,job):
    job['level'] = ['entry']

    #try to get the job description elements
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "jobsearch-JobMetadataFooter")))
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        #go through job type and salary info on page
        details = soup.findAll('div', 'jobsearch-JobDescriptionSection-sectionItem')
        for det in details:
            if det.find('div', 'icl-u-textBold').text == 'Job Type':
                j_types = [d.text for d in det.findAll('div')[1:] if d.text != 'Remote']
                job['employment_type'] = j_types
            if det.find('div').text == 'Salary':
                j_salary = det.find('span').text
                job['salary'] = j_salary

        #try to get the date posted based on the Hiring Insights section
        try:
            for bullet in soup.find('h2', string='Hiring Insights').parent.find('li').children:
                if 'Posted' in bullet.text:
                    days_ago = bullet.text
            if 'today' in days_ago.lower() or 'just posted' in days_ago.lower():
                date = datetime.date.today()
            else:
                if '+' in days_ago:
                    days_ago = ' '.join(days_ago.split('+'))
                int_days_ago = [int(day) for day in days_ago.split() if day.isdigit()][0]
                date = datetime.date.today() - datetime.timedelta(days=int_days_ago)
            job['datePosted'] = date
        except:
            pass
        #get the main body description html and remove extra symbols if necessary
        html = soup.find('div', 'jobsearch-jobDescriptionText')
        if html:
            job['desc_html'] = removeSymbols(str(html))
        else:
            job['desc_html'] = ""
    #if we're unable to scrape the page just set desc_html to empty
    except TimeoutException:
        print('error scraping webpage (timed out) for',job['title'],job['company'],job['location'],job['url'])
        job['desc_html'] = ""
    return job

#go through dataframe and drop jobs that have already closed
def closeJobPostings(df):
    urls = df['url']
    driver = startDriver()
    for i,url in urls.items():
        if postIsClosed(url,driver):
            print(len(df))
            df = df.drop(i)
            print(len(df))
    return df

#check if a job posting is closed
def postIsClosed(url,driver):
    try:
        page = requests.get(url,headers={
        "User-Agent" : "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"})
        #closed depending of the redirected url
        if 'trk=expired_jd_redirect' in page.url or 'intsignup' in page.url:
            print(page.url)
            print('post is closed (redirect)')
            return True

        #closed if it's a linkedin post and has either a closed-job element or was not found (404 error)
        elif 'linkedin.com' in url:
            soup = BeautifulSoup(page.content, 'lxml')
            expired = soup.findAll("figure","closed-job") + soup.findAll("div","not-found-404")
            if len(expired) > 0:
                print(page.url)
                print('post is closed')
                return True

        #closed if it's a indeed post and either the page wasn't found or has an expired header/text
        elif 'indeed.com' in url:
            driver.get(url)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "li")))
            soup = BeautifulSoup(driver.page_source, 'lxml')
            if 'Page Not Found' in soup.title.text:
                print(page.url)
                print('post is closed (page not found)')
                return True
            expired = soup.findAll("div","jobsearch-JobInfoHeader-expiredHeader")
            if soup.find("div","css-jsuk8h ekqvxqv5"):
                if "This job has expired on Indeed" in soup.find("div","css-jsuk8h ekqvxqv5").text:
                    expired.append(soup.find("div","css-jsuk8h ekqvxqv5"))
            if len(expired) > 0:
                print(page.url)
                print('post is closed')
                return True
        #return false otherwise
        return False
    except:
        return False

#remove unwanted symbols in html text
def removeSymbols(text):
    no_emoj = re.compile("["
                         u"\U0001F600-\U0001F64F"  # emoticons
                         u"\U0001F300-\U0001F5FF"  # symbols/pictographs
                         u"\U0001F680-\U0001F6FF"  # transport and map
                         u"\U00002500-\U00002BEF"  # arrows
                         u"\U0001F780-\U0001F7FF"  # geometric shapes ext
                         u"\U0001D100-\U0001D1FF"  # music
                         u"\U0001F900-\U0001F9FF"  # supp symbols/pictographs
                         u"\U0001FA70-\U0001FAFF"  # sym/pictographs ext a
                         u"\U0001F800-\U0001F8FF"  # sup arrows-c
                         "]")
    return re.sub(no_emoj, ' ', text)

#clean html for text analysis
def cleanHtml(html):
    expand_text = []
    test = []
    #go through all words in the div text and clean them for analysis
    for word in html.find('div').get_text().split():
        words = cleanString(word)
        expand_text += words
        test.append(word)
    clean_text = ' '.join(expand_text)
    clean_text = re.sub(r'[Pp][Hh][\s\.][Dd]', 'PhD', clean_text)
    return clean_text

#return text analysis of the html
def getDescription(html):
    matcher = Matcher(nlp.vocab)
    if html is None:
        html = ''
    if html == '':
        doc = nlp(html)
        return cleanDescription(doc, matcher)

    html = BeautifulSoup(html, features="lxml")
    clean_text = cleanHtml(html)
    doc = nlp(clean_text)
    textData = cleanDescription(doc, matcher)
    return textData

#find specific patterns and words in doc text
def cleanDescription(doc,matcher):

    #list of words that will be counted
    field_words = [r'public health', r'epidemiology', r'research.*', r'develop.*', r'data science', r'analy.*',
                   r'software',r'programm.*']
    #regex for finding education words
    ed_words = [r"[Bb]achelor'?s?", r'\sB\.?A\s',r'\sb\.?a\s', r"[Mm]aster'?s?", "\sM\.?S\s", r'\s[Bb]\.?[Ss]\s',
                r'PhD', r'graduate',r'undergraduate','[Dd]octorate']
    #regex for finding experience
    exp_pattern = [[{'IS_DIGIT': True},{'TEXT': {'REGEX': r'.*'}, "OP": "{,2}"},{'LOWER': {'REGEX': r'year|years'}},
                    {'TEXT': {'REGEX': r'.*'}, "OP": "{,3}"}, {'LOWER': 'experience'}],
                   ]
    #regex for finding salary
    money_pattern = [
        [{'IS_CURRENCY': True}, {'IS_DIGIT': True}, {'TEXT': {'REGEX': r'to|-+'}}, {'IS_CURRENCY': True, 'OP': '?'}
            , {'IS_DIGIT': True}, {'TEXT': {'REGEX': 'per|/|annually|yearly|hourly'}, 'OP': '?'},
         {'TEXT': {'REGEX': r'year|hour|yr|hr'}, "OP": "?"}
         ]]

    #use Spacy's matcher to find all words/phrases that match the above regexes
    ed_patterns = [[{'TEXT': {'REGEX': pattern}}] for pattern in ed_words]
    field_patterns = [[{'LOWER': {'REGEX': word}} for word in field.split()] for field in field_words]
    findMatches(doc, exp_pattern, matcher, 'num_experience',remove=False)
    findMatches(doc, money_pattern, matcher, 'salary',remove=False)
    results = findMatches(doc, ed_patterns, matcher, 'education',remove=False)
    matcher.remove('num_experience')
    matcher.remove('salary')
    matcher.remove('education')

    search_words = []
    #count the frequency of noted words in text
    for i in range(len(field_words)):
        search_words = findMatches(doc, [field_patterns[i]], matcher, field_words[i], remove=False, phrase=True)
    count_fields = {key.split('.')[0]: len(search_words[key]) if key in search_words.keys() else 0 for key in
                    field_words}

    #get a standardized list of experience-related phrases ([0-9] [experience word])
    experience = []
    if 'num_experience' in results:
        for res in results['num_experience']:
            sublist = list(filter(None, re.split(r'(\d+)', res.lower(),maxsplit=1)))
            if sublist not in experience:
                experience.append(sublist)

    #get a standardized dictionary for job salary
    clean_salary = {}
    if 'salary' in results:
        clean_salary = cleanSalary(results['salary'])

    #get a cleaned set for education requirements
    clean_education = set()
    if 'education' in results:
        for res in results['education']:
            if 'b' in res.lower() or res.lower() == 'undergraduate':
                clean_education.add('bachelor')
            elif 'm' in res.lower():
                clean_education.add('master')
            elif 'graduate' in res.lower():
                clean_education.add('graduate')
            else:
                clean_education.add('doctorate')
    clean_education = list(clean_education)

    #get a list of skills found in the text and the associated skill groups
    phraseMatcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    found_skills = {}
    all_skills = []
    skill_patterns = []
    groups = []
    for group,skills in list(getSkills().items()):
        skill_patterns += [nlp.make_doc(skill) for skill in skills]
        all_skills += [skill for skill in skills]
        groups += [group]*len(skills)
    phraseMatcher.add("SkillList", skill_patterns)
    matches = phraseMatcher(doc)
    for match_id,start,end in matches:
        text = doc[start:end].text.title()
        if groups[all_skills.index(text)] not in found_skills:
            found_skills[groups[all_skills.index(text)]] = set()
        found_skills[groups[all_skills.index(text)]].add(text)

    return {'education': clean_education,  'experience': experience,  'salary': clean_salary,'fieldwords': count_fields,
            'skills':found_skills}

#clean scraped job salary
def cleanSalary(salary):
    #get all potential salaries and get the longest phrase (most likely correct)
    found_salaries = [list(filter(None, re.split(r'(\$)?([\d,.]+)',res))) for res in set(salary)]
    found_salaries.sort(key=len, reverse=True)
    sal = found_salaries[0]
    #salary should include a unit,min,max,and period
    clean_salary = {'unit': '', 'min_range': 0, 'max_range': 0, 'period': ''}
    #salary shouldnt go beyond 150,000 (likely an error) or below 0
    maxSal = 150000
    minSal = 0
    nums = []

    #go through first match
    for s in sal:
        #find the unit if possible
        if '$' in s or 'USD' in s:
            clean_salary['unit'] = s
        #after checking if a token is a digit and is within accepted range,add to list of found num with commas removed
        if s.replace(',','').replace('.','').isdigit() and float(s) < maxSal and float(s) > minSal:
            nums.append(float(s.replace(',','')))

    #if salary numbers were found
    if len(nums) > 0:
        #set the min and max salary
        if len(nums) == 1:
            clean_salary['max_range'] = nums[0]
        else:
            clean_salary['min_range'] = min(nums)
            clean_salary['max_range'] = max(nums)
        #if the max is small, assumes its per hour (otherwise by year)
        if clean_salary['max_range'] < 1000:
            clean_salary['period'] = 'per hour'
        else:
            clean_salary['period'] = 'per year'

    return clean_salary

#loads a json of skills and creates a dictionary of cleaned skills that can be searched for in a text
def getSkills():
    addSpace = ['PrioritizeWorkload', 'ITStrategy', 'ProductInnovation', 'WindEnergy','MedicalMicrobiology',
                'OutpatientOrthopedics', 'TechnicalPresentations', 'CancerTreatment','NeurologicalDisorders',
                'LegalAssistance', 'CommercialInsurance', 'InfectiousDiseases', 'CognitiveScience','FormattingDocuments'
                ,'EconomicResearch','CollaborativeEnvironment','ReceptionistDuties','SolutionFocused','DecisionMaking']
    requested_skills = {}

    with open('./skills.json', 'r') as file:
        skills = json.load(file)['SAMPLE DETAILED SKILLS']
        #go through detailed skills in each skill group
        for group in skills.keys():
            requested_skills[group] = set()
            #splits string at each comma and cleans each skill, including adding needed spaces
            for skill in skills[group].split(','):
                if skill in addSpace:
                    cleaned_skill = ' '.join(cleanString(skill,ignore_punct=True))
                else:
                    cleaned_skill = re.sub(r'[^\w\s\-\(\)]','',skill)
                requested_skills[group].add(cleaned_skill.strip().title())

    return requested_skills

#clean a string of text
def cleanString(string,ignore_punct=False):
    #split string into likely words
    split = re.sub(r"(?<=[a-z])(?=[A-Z:])|(?<=[0-9])(?=[A-Z\+])"," ", string).split()
    words = []
    #go through each found word
    for s in split:
        #replace punctuation with '' if we are ignoring punctuation
        if ignore_punct == True:
            s = re.sub(r'[^\w\s]','',s)
        #expand contractions
        fixed = contractions.fix(s, slang=False)
        #remove extra white spaces
        fixed = fixed.strip()
        fixed = re.sub(r"([(:)])",'',fixed).split()
        words += fixed

    return words

#find pattern matches in a nlp doc
def findMatches(doc,pattern,matcher,id,remove=True,phrase=False):
    #add pattern and pattern name to matcher
    matcher.add(id,pattern)
    matches = matcher(doc)
    found = {}
    #go through found matches
    for match_id,start,end in matches:
        #get the span + its label and text
        span = Span(doc, start, end, label=match_id)
        label = span.label_
        #if we aren't looking for phrases simply find text, otherwise we'll need to join the words in its subtree
        if phrase == False:
            text = span.text
        else:
            text = ' '.join([w.text for w in span.root.subtree])
        if label not in found:
            found[label] = []
        found[label].append(' '.join(cleanString(text)))

    #remove pattern from matcher if needed
    if remove == True:
        matcher.remove(id)

    return found

if __name__ == "__main__":
    home()