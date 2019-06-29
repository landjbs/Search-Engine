# Responsible for cleaning URL strings and fetching page contents using
# urllib.

import urllib.request
import re


class ParseError(Exception):
    """ Exception for errors while parsing a link """
    pass


# matcher for url denoted by https:// or http://
urlString = r'https://\S+|http://\S+'
urlMatcher = re.compile(urlString)


def parsable(url):
    """ Returns true if url follows urlMatcher pattern """
    # canParse = False if not urlMatcher.match(url) else False
    canParse = True if urlMatcher.fullmatch(url) else False
    return canParse


def fix_url(url):
    """ Add proper headings URLs for crawler analysis """
    # cast url to string
    urlString = str(url)
    if not parsable(urlString):
        # check starts
        if urlString.startswith('http'):
            pass
        elif urlString.startswith("www"):
            urlString = "https://" + urlString
        else:
            urlString = "http://www." + urlString
    return urlString


def url_to_pageString(url, timeout=5):
    """ Cleans and converts string of URL link to string of page contents """
    # add proper headers to url
    cleanedURL = fix_url(url)
    try:
        # get response object of url, failing after timeout seconds
        page = urllib.request.urlopen(cleanedURL, timeout=timeout)
    except:
        raise ParseError(f"Unable to access '{cleanedURL}'")
    pageString = page.read()
    page.close()
    return(pageString)
