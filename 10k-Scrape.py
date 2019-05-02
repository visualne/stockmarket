import requests
from bs4 import BeautifulSoup
import time
import re
import argparse
from datetime import date


#  Need to loop through each page found and scrape the page appropriately.

#  Get the data associated with each filing
#  Check to see any of these dogs are making money
#  Populate a database or something that can keep track of the company list
#  over time.

class TenKClass:
    def __init__(self):
        # Opening the output file
        f = open(r'output.html')

        #  Creating soup object
        self.soup = BeautifulSoup(f.read())

        #  Company Information ex) 10-K for {10-K for Netflix: [DATE,CIK, SIC]}
        self.companyInformation = {}

    def totalResults(self):

        #  Pull elements in table id of 'header'
        table = self.soup.find("table", {"id": "header"})

        #  Gettings all the rows from the table
        rows = []
        for row in table.findAll("tr"):
            rows.append(row)

        # For loop to look through rows.
        for val in rows:
            #  Getting all td elements in the row.
            tdElements = val.findAll("td")

            #  Getting first td element
            tdElement = tdElements[0]

            #  Getting the third piece of text. (num results) in this element
            totalResults = tdElement.findAll("font")[2].text

            #  Returning total results
            return int(totalResults)

    #  Determing how many page of results there are.
    def pageResults(self):

        #  Assume 100 results a page are displayed
        totalResults = self.totalResults()

        totalPages = self.totalResults() / 100
        pagesLeftOver = self.totalResults() % 100


        #  If pagesLeftOver > 0 there is one extra page of results.
        if pagesLeftOver > 0:
            totalPages = totalPages + 1
            return totalPages
        else:
            return totalPages

    def getNextPageLink(self):

        #  Getting link object
        link = self.soup.find("a", {"title": "Next Page"})

        #  Returning href link
        return 'https://searchwww.sec.gov' + link['href']


    def getSoupPage(self,link):

            #  Getting page
            result = requests.get(link)

            #  Getting page
            htmlPage = result.content

            # Creating soup object
            self.soup = BeautifulSoup(htmlPage)


    def getCompanyInformation(self):

        #  Function to pull out date out of tr element
        #  Function to pull out href link from each tr element.
        #  From the href elements you will be able to pull the companyTenK,
        #  sicSearch,cikSearch

        #  This is a list that holds information about the company scraped f
        # rom the page.
        #  [date,cikCode,sicCode]

        tempCompanyInfoList = []

        #  Creating dictionary that will hold company 10-K link text as key and
        #  date, CIK and SIC values as elements in a list
        #  ex) companyInformation['company'] = ['date','cikCode','sicCode']
        #  Going to remove these later
        self.companyInformation = {}
        tempCompanyInfoList = []

        #  Get all <a> elements
        trElements = self.soup.find_all('tr')

        for trElement in trElements:

            # 03/01/201810 - K for CDW Corp
            # 03/01/2018
            # COMPANY NAME(s) - [CDW Corp(CIK - 1402057 /SIC - 5961)]
            # print trElement.text.strip()


            #  Grab the date and 10-K string
            companyNameAndDate = re.search('(\d\d\/\d\d\/\d\d\d\d)(10-K for (.+))',trElement.text.strip())
            # companyCIKandSIC = re.search('COMPANY NAME\(s\) \- \[(\w|\s)+\(CIK \- (\d+) \/ SIC \- (\d+)',trElement.text.strip())
            companyCIKandSIC = re.search('COMPANY NAME\(s\) \- \[(\w|\s)+\(CIK \- (\d+) \/SIC - (\d+)',trElement.text.strip())


            if companyNameAndDate:
                # print companyNameAndDate.group(1) + ' ' + companyNameAndDate.group(3)
                date = companyNameAndDate.group(1)
                companyName = companyNameAndDate.group(3)
                self.companyInformation[companyName] = []
                self.companyInformation[companyName].append(date)

            if companyCIKandSIC and self.companyInformation:
                # print companyCIKandSIC.group(2) + ' ' + companyCIKandSIC.group(3)
                cik = companyCIKandSIC.group(2)
                sic = companyCIKandSIC.group(3)
                companyName = self.companyInformation.keys()[0]
                # self.companyInformation[companyName].append(cik)
                # self.companyInformation[companyName].append(sic)


                #  Appending type of industry to companyInformation list.
                self.companyInformation[companyName].append(\
                    'BusinessType: ' + self.sicClassifications[sic])

                #  Calling print function
                # self.printCompanyInformation()
                print self.companyInformation

                tempCompanyInfoList = []
                self.companyInformation = {}


    def printCompanyInformation(self):
        #  Printing everything found
        for k,v in self.companyInformation.iteritems():
            print k + ' ' + str(v)


    def sicList(self):
        '''This function fills a dictionary with the sic classficiations \
        currently on results page'''

        # Creating SIC regular expression
        # ex) 7600Services-Miscellaneous Repair Services
        sicNumberRegEx = '(\d+)(.+)'

        #  Get select elements with name of sic_select
        sicSelectElements = self.soup.find_all('select',{"name": "sic_select"})

        #  Getting all option elements in sicSelect
        optionElements = sicSelectElements[0].find_all('option')

        #  Creating dictionary holding SIC[Classification]
        self.sicClassifications = {}

        for classification in optionElements:
            match = re.search(sicNumberRegEx,classification.text)

            if match:
                #  Filling dictionary appropriately
                self.sicClassifications[match.group(1)] = match.group(2)


def main():

    parser = argparse.ArgumentParser(description='Get SEC filing information')

    #  Adding the keyword argument this will be the search term.
    parser.add_argument('--keyword',
                        nargs='+',
                        help='Keyword to search for in SEC filing.')

    #  Adding the previousYears argument this will be the previous number
    #  of years.
    parser.add_argument('--previous_years',
                        type=int,
                        help='previous number of years to search')


    #  Getting the arguments
    args = parser.parse_args()

    #  Putting if search term is multiple words I am adding a +
    #  in place of each of the spaces. Also adding double quotes
    #  around the word.
    keyword = " ".join(args.keyword)
    keyword = "\"" + keyword.replace(" ", '+') + "\""


    #  Getting current Date
    currentDate = date.today()

    #  Getting date that is one year prior to the date above.
    # fiveYearAgo = date(currentDate.year - 5, currentDate.month,
    # currentDate.day)

    #  Getting the number of years back to check.
    numberOfYearsBack = date(currentDate.year - args.previous_years, \
                             currentDate.month, currentDate.day)


    #  Creatin url
    url = 'https://searchwww.sec.gov/EDGARFSClient/jsp/EDGAR_MainAccess.jsp'
    url += '?search_text='
    url += keyword
    url += '&sort=Date'
    url += '&formType=Form10K'
    url += '&isAdv=true'
    url += '&stemming=true'
    url += '&numResults=100'
    url += '&fromDate='
    url += str(numberOfYearsBack.strftime("%m/%d/%Y"))
    url += '&toDate=' + str(currentDate.strftime("%m/%d/%Y"))
    url += '&numResults=100'

     # Creating tenKobj
    tenKobj = TenKClass()

    #  Converting the html page into a soup object that is easier to parse.
    tenKobj.getSoupPage(url)

    #  Getting sicList
    tenKobj.sicList()

    #  Getting tr elements
    tenKobj.getCompanyInformation()

    #  Getting total results.
    totalResults = tenKobj.totalResults()
    pageResults = tenKobj.pageResults()

    if pageResults > 1:

        #  For loop tp create urls
        for pageResult in range(pageResults - 1):
            pageStart = str(((pageResult + 1) * 100) + 1)

            #  Left off here creating the link.
            #  Creating url
            url = 'https://searchwww.sec.gov/EDGARFSClient/jsp/EDGAR_MainAccess.jsp?'
            url += 'search_text='
            url += keyword
            url += '&sort=Date'
            url += '&startDoc='+str(pageStart)
            url += '&numResults=100'
            url += '&isAdv=true'
            url += '&formType=Form10K'
            url += '&fromDate=' + str(numberOfYearsBack.strftime("%m/%d/%Y"))
            url += '&toDate=' + str(currentDate.strftime("%m/%d/%Y"))
            url += '&stemming=true'

            #  Converting the html page into a soup object that is easier to parse.
            tenKobj.getSoupPage(url)

            #  Getting tr elements
            tenKobj.getCompanyInformation()

            print url

main()
