"""
Functions for all text processing involding knowledgeSet and knowledgeProcessor
built in models.knowledge.knowledgeBuilder.
"""

import re
from flashtext import KeywordProcessor

knowledgeProcessor = KeywordProcessor(case_sensitive=False)
knowledgeProcessor.add_keyword('foo')


# def score_token(token, div):
#     """
#     Args: single knowledge token and html division where it occurred
#     Returns: score of token weighted by
#     """


def find_tokens(pageText, knowledgeProcessor):
    """
    Returns dict mapping knowledge tokens to score assigned by score_token
    """
    # use knowledgeProcessor to extract tokens from page text
    keywordsFound = knowledgeProcessor.extract_keywords(pageText)
    # create dict mapping keywords to number of times used in pageText using re.findall()
    keywordDict = {keyword:(len(re.findall(keyword, pageText, re.IGNORECASE))) for keyword in keywordsFound}
    return keywordDict


def find_weighted_knowledge(divDict):
    """
    Args:
        divDict- Dict generated by crawlers.htmlAnalyzer mapping from
                 html divisions to the string of their contents.

    Returns: Single dict mapping from knowledgeTokens found to score assigned
    by weight

    Sample input: {'title':'foo bar', 'h1':'foo', 'p':'hello world'}
    """
    for div in divDict:
        divText = divDict[div]
        divLen = len(divText.split())
        weightedTokens =

        # tokenDict = (find_tokens(divDict[div], knowledgeProcessor))
        # tokenDict = dict(map(lambda k : (k[0], k[1]/2), tokenDict.items()))
        # print(tokenDict)





find_weighted_knowledge({'title':'foo bar', 'h1':'foo', 'p':'hello world'})










pass
