from time import time
from termcolor import colored

from dataStructures.objectSaver import load
from dataStructures.pageObj import Page
from dataStructures.thicctable import Thicctable
from searchers.searchLexer import topSearch
from models.knowledge.knowledgeFinder import score_divDict
from models.knowledge.knowledgeBuilder import build_knowledgeProcessor


print(colored('Loading Knowledge Set', 'red'), end='\r')
knowledgeSet = load('data/outData/knowledge/knowledgeSet.sav')
print(colored('Complete: Loading Knowledge Set', 'cyan'))

database = Thicctable(knowledgeSet)
del knowledgeSet

print(colored('Loading Knowledge Processor', 'red'), end='\r')
knowledgeProcessor = load('data/outData/knowledge/knowledgeProcessor.sav')
print(colored('Complete: Loading Knowledge Processor', 'cyan'))

print(colored('Loading Freq Dict', 'red'), end='\r')
freqDict = load('data/outData/knowledge/freqDict.sav')
print(colored('Complete: Loading Freq Dict', 'cyan'))

filePath = 'data/inData/wikipedia_utf8_filtered_20pageviews.csv'


def make_wiki_url(title):
    """ Converts wikipedia title to url for the page """
    urlTitle = '_'.join(word for word in title.split())
    url = f'https://en.wikipedia.org/wiki/{urlTitle}'
    return url


with open(filePath, 'r') as wikiCsv:
    for i, line in enumerate(wikiCsv):
        if i < 100:
            # number of days since June 29 2019 when page was loaded
            loadDate = int(time() / (86400)) - 18076
            # get everything after the first comma
            rawText = line[21:]
            # pull out the title
            titleEnd = rawText.find('  ')
            title = rawText[:titleEnd]
            # get the article text and strip whitespace
            articleText = rawText[(titleEnd+2):]
            articleText = articleText.strip()
            # build link of the webpage
            url = make_wiki_url(title)
            # build divDict and analyze for knowledgeTokens
            divDict = {'url':       url,
                        'title':    title,
                        'all':      articleText}
            knowledgeTokens = score_divDict(divDict, knowledgeProcessor, freqDict)
            # determine text to show for the window
            windowText = articleText
            # build page object of article attributes
            pageObj = Page({'url':              url,
                            'title':            title,
                            'knowledgeTokens':  knowledgeTokens,
                            'pageVec':          {},
                            'linkList':         [],
                            'loadTime':         0.5,
                            'loadDate':         loadDate,
                            'imageScore':       0,
                            'videoScore':       0,
                            'windowText':       windowText})
            # bucket page object
            database.bucket_page(pageObj)
            print(colored(f'Crawling Wikipedia: {i}', 'red'), end='\r')
print(colored('Complete: Crawling Wikipedia', 'cyan'))

print(colored('Cleaning Database', 'red'), end='\r')
database.kill_empties()
print(colored('Complete: Cleaning Database', 'cyan'))

# sort the database
print(colored('Sorting Database', 'red'), end='\r')
database.sort_all()
print(colored('Complete: Sorting Database', 'cyan'))

# get dict mapping token to length of posting list
print(colored('Finding Posting Lengths', 'red'), end='\r')
WORDS = database.all_lengths()
print(colored('Complete: Finding Posting Lengths', 'cyan'))

print(f"\n{'-'*80}\nWelcome to Boogle Wikipedia DeNerf!")
while True:
    # get search text from user
    search = input('Search: ')
    # pass search, databse, and word info to topSearch
    try:
        start = time()
        correctionDisplay, resultsList = topSearch(search, database, WORDS)
        end = time()
        # display formated results
        displayString = "<u>Boogle Wikipedia DeNerf</u><br>"
        displayString += f"{round(len(resultsList), 2)} results found in {end - start} seconds.<br>"
        if correctionDisplay:
            displayString += f"Showing results for <u>{correctionDisplay}</u>. Search instead for <a>{search}</a>.<br>"
        for result in resultsList:
            displayString += f'<br><strong>{result[1]}</strong><br><i>{result[0]}</i><br>{result[2]}'
        print(displayString)
    except Exception as e:
        print(colored(f'ERROR: {e}', 'red'))









pass
