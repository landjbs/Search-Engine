# Script responsible for building database of page data from list of URLs.
# Outsources all HTML processing to htmlAnalyzer. Handels url requesting and
# Thread/Queue model for distributed parsing

import urllib.request
import crawlers.htmlAnalyzer as ha

class ParseError(Exception):
    """ Exception for errors while parsing a link """
    pass


def clean_url(url):
    """ Add proper headings URLs for crawler analysis """
    # cast url to string
    urlString = str(url)
    if not ha.parsable(urlString):
        # check starts
        if urlString.startswith('http'):
            pass
        elif urlString.startswith("www"):
            urlString = "http://" + urlString
        else:
            urlString = "http://www." + urlString
    return urlString


def url_to_pageString(url):
    """ Cleans and converts string of URL link to string of page contents """
    # add proper headers to url
    cleanedURL = clean_url(url)
    try:
        # get http.client.HTTPResponse object of url
        page = urllib.request.urlopen(cleanedURL)
    except:
        raise ParseError(f"Unable to access '{cleanedURL}''")
    pageString = page.read()
    page.close()
    return(pageString)


def urlList_to_stringList(urlList):
    errors = 0
    stringList = []
    for count, url in enumerate(urlList):
        try:
            urlString = url_to_string(url)
            stringList.append(url_to_string(url))
        except:
            stringList.append("ERROR")
            errors += 1
        print(f"\t{count} urls analyzed with {errors} errors", end="\r")
    return stringList
