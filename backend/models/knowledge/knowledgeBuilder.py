"""
Generates set of knowledge tokens, which comprize the keys in the topDict of
the key-val store described in dataStructures.thicctable. These tokens
represent the extent of top-level lookup buckets avaiable to users and, as
such, follow the philosophy of comprehensive concision. There should be enough
knowledge tokens that any reasonable search can be answered by the contents of
a lookup bucket, but not so many as to take up redundant space.
Knowledge tokens are only permitted to be words and phrases; tokens comprised
soley of non-alpha chars will be mapped to the English representation of the
token (eg. & -> ampersand).
These tokens are then converted into a flashtext matcher for ~constant time,
greedy lookup of phrases and words. Flashtext is a great module based on this
paper: https://arxiv.org/pdf/1711.00046.pdf. The matcher is applied in
knowledgeFinder.
"""

import os
import re
from numpy import log
from tqdm import tqdm
from collections import Counter
from flashtext import KeywordProcessor
from scipy.spatial.distance import cosine

from dataStructures.objectSaver import save, load
from models.processing.cleaner import clean_text, clean_wiki
import models.knowledge.knowledgeFinder as knowledgeFinder

## Functions ##
def build_knowledgeSet(knowledgeFile, additionalTokens=None, numberRange=None, outPath=""):
    """
    Args: \n delimited knowledgeFile of phrases to treat as knowledge tokens
    (tokens for strict word search), additionalTokens set of tokens not in
    knowledgeFile, numberRange tuple of range of integer tokens to add, and
    outPath to which to save set
    Returns: set (for fast lookup) of cleaned tokens stripped from knowledgeData
    """
    # open base knowledgeFile
    with open(knowledgeFile) as knowledgeData:
        # build set of cleaned lines in knowledgeData
        knowledgeSet = {clean_wiki(token) for token in knowledgeData}

    # add tokens from additionalTokens set
    if additionalTokens:
        for token in additionalTokens:
            knowledgeSet.add(clean_wiki(token))

    # add integers between first and last elt of numberRange tuple
    if numberRange:
        assert isinstance(numberRange, tuple), "numberRange must be a tuple of integers"
        for num in range(numberRange[0], numberRange[1]):
            knowledgeSet.add(str(num))

    # remove empty token from knowledgeSet (only one because set)
    knowledgeSet.remove("")

    # save knowledge to outPath if specified
    if not (outPath==""):
        save(knowledgeSet, outPath)
    return knowledgeSet


def build_knowledgeProcessor(knowledgeSet, outPath=""):
    """ Builds flashtext matcher for words in knowledgeSet iterable """
    # initialize flashtext KeywordProcessor
    knowledgeProcessor = KeywordProcessor(case_sensitive=False)
    # add all items from knowledge set cast as list
    for i, keyword in enumerate(knowledgeSet):
        print(f"\tBuilding knowledgeProcessor: {i}", end="\r")
        knowledgeProcessor.add_keyword(keyword)
    print("\nknowledgeProcessor Built")
    # save knowledgeProcess to outPath if given
    if not (outPath==""):
        save(knowledgeProcessor, outPath)
    return knowledgeProcessor


def fredDict_from_wikiFile(filePath, knowledgeProcessor, outPath=""):
    """
    Args: filePath to wikiFile containing lines of articles from which to read,
    knowledgeProcessor for token extraction.
    Returns: dict mapping knowledge tokens to tuple of (termFreq, docFreq)
    observed in documents.
        termFreq = (number of times a token is used) / (number of words used)
        docFreq = log ((number of documents) / (number of documents in which a token appears))
    """
    # initialize counter to map knowledge tokens to raw number of occurences
    tokenCounts = Counter()
    # initialize counter to map knowledge tokens to number of docs they appear in
    tokenAppearances = Counter()
    # initialize variable to keep track of total number of words used
    totalLength = 0

    with open(filePath, 'r') as wikiFile:
        for i, line in enumerate(wikiFile):
            # get everything after the first comma
            commaLoc = line.find(',')
            rawText = line[(commaLoc+2):]
            # find the tokens
            tokensFound = knowledgeFinder.find_weighted_tokenCounts(rawText, knowledgeProcessor)
            tokenCounts.update(tokensFound)
            tokenAppearances.update(set(tokensFound))
            totalLength += len(rawText.split())
            print(f"\tBuilding freqDict: {i}", end='\r')

    # lambdas for calculating termFreq and docFreq
    calc_termFreq = lambda tokenCount : tokenCount / totalLength
    calc_docFreq = lambda tokenAppearance : log(float(i) / tokenAppearance)

    # use total num to normalize tokenCounts and find frequency for each token
    freqDict = {token: (calc_termFreq(tokenCounts[token]),
                        calc_docFreq(tokenAppearances[token]))
                for token in tokenCounts}

    if (outPath != ""):
        save(freqDict, outPath)

    return freqDict


def fredDict_from_folderPath(folderPath, knowledgeProcessor, outPath=None):
    """
    Args: folderPath to folder containing files from which to read,
    knowledgeProcessor for token extraction.
    Returns: dict mapping knowledge tokens to tuple of (termFreq, docFreq)
    observed in documents.
        termFreq = (number of times a token is used) / (number of words used)
        docFreq = log ((number of documents) / (number of documents in which a token appears))
    """
    # initialize counter to map knowledge tokens to raw number of occurences
    tokenCounts = Counter()
    # initialize counter to map knowledge tokens to number of docs they appear in
    tokenAppearances = Counter()
    # initialize variable to count total number of words used
    totalLength = 0

    # find and iterate over list of files within folderPath
    for i, file in enumerate(os.listdir(folderPath)):
        print(f"\tBuilding freqDict: {i}", end='\r')
        with open(f"{folderPath}/{file}") as FileObj:
            # read in the current file
            text = FileObj.read()
            # find both greedy and subtokens in text
            tokensFound = list(knowledgeFinder.find_rawTokens(text, knowledgeProcessor))
            # add tokens counts to tokenCounts counter
            tokenCounts.update(tokensFound)
            # add single appearance for each token found
            tokenAppearances.update(set(tokensFound))
            # find number of words in the current file
            textLen = len(text.split())
            # add number of words in current file to totalLength
            totalLength += textLen

    # lambdas for calculating termFreq and docFreq
    calc_termFreq = lambda tokenCount : tokenCount / totalLength
    calc_docFreq = lambda tokenAppearance : log(float(i) / tokenAppearance)

    # use total num to normalize tokenCounts and find frequency for each token
    freqDict = {token: (calc_termFreq(tokenCounts[token]),
                        calc_docFreq(tokenAppearances[token]))
                for token in tokenCounts}

    if outPath:
        save(freqDict, outPath)

    return freqDict


def build_corr_dict(filePath, knowledgeProcessor, freqDict, freqCutoff=0.0007,
                    bufferSize=40000, corrNum=5, outPath=None):
    """
    Builds dict mapping tokens to the ranked list of corrNum tokens with the
    highest normalized co-occurence in filePath.
    Args:
        -filePath:              Path to the csv file in which the wikipdia
                                    articles are stored
        -knowledgeProcessor:    Flashtext processor for knowledge tokens
        -freqDict:              Dictionary of frequency tuples for observed tokens
        -freqCutoff:            Upper frequency that a token can have and
                                    still be analyzed.
        -bufferSize:            Number of texts to analyze in RAM at one time.
                                    At bufferSize, the current tokenDict is saved
                                    under TEMP_FOLDER_PATH and deleted from RAM.
        -corrNum:               Max number of tokens to include in the ranked
                                    corrList of each token.
        -outPath:               Path to which to save the final corrDict. All
                                    temporary files created during run will
                                    be deleted.
    Returns:
        Dictionary mapping each qualifying token to scored and ranked list of
        corrNum relatedTokens where scores in range (0, 1] and are rounded
        to four decimal places.
    """

    TEMP_FOLDER_PATH = 'corrDictTablets'

    def corrable(token, freqTuple):
        """ Helper determines if token corr should be taken STILL NEED TO CHECK IF TOKEN """
        return False if (freqTuple[0]>freqCutoff) or (False) else True

    # dictionary mapping tokens with frequency below freqCutoff to empty counters
    # aways remains empty as a template for tablets, which will be saved and merged
    emptyTokenDict = {token:Counter() for token, freqTuple in freqDict.items()
                        if corrable(token, freqTuple)}
    print(emptyTokenDict)

    def norm_pageTokens(pageTokens, numWords):
        """
        Helper normalizes pageToken Counter() by dividing by token frequency
        and cuts those that are below freqCutoff
        """
        return {token : ((rawCount / numWords) / freqDict[token][0])
                for token, rawCount in pageTokens.items()
                if token in emptyTokenDict}

    def delete_temp_folder():
        """ Helper deletes TEMP_FOLDER_PATH and contents before and after run """
        if os.path.exists(TEMP_FOLDER_PATH):
            for file in os.listdir(TEMP_FOLDER_PATH):
                os.remove(f'{TEMP_FOLDER_PATH}/{file}')
            os.rmdir(TEMP_FOLDER_PATH)


    # create temp folder for to hold tablets of tokenDict
    delete_temp_folder()
    os.mkdir(TEMP_FOLDER_PATH)

    x = Counter()
    x.pop

    # iterate over each article in filePath
    curTokenDict = emptyTokenDict.copy()
    with open(filePath, 'r') as wikiFile:
        for i, page in enumerate(tqdm(wikiFile)):
            # build counter of token numbers on page and normalize counts by frequency
            pageTokens = Counter(knowledgeProcessor.extract_keywords(page))
            numWords = len(page.split())
            normedTokens = norm_pageTokens(pageTokens, numWords)
            # update the related tokens of each token on the page with all the others
            for token in normedTokens.keys():
                if token in curTokenDict:
                    curTokenCounter = normedTokens.copy()
                    curTokenVal = curTokenCounter.pop(token)
                    curTokenCounter = {otherToken : (otherVal * curTokenVal)
                                        for otherToken, otherVal
                                        in curTokenCounter.items()}
                    curTokenDict[token].update(curTokenCounter)
            # save to temp folder if i is at buffer size
            if (i % bufferSize == 0):
                if i > 0:
                    # clean empty tokens from curTokenDict
                    cleanTokenDict = {token : counts
                                    for token, counts in curTokenDict.items()
                                    if counts.values() != []}
                    del curTokenDict
                    # save cleaned token dict in temp folder and delete from ram
                    save(cleanTokenDict, f'{TEMP_FOLDER_PATH}/tokenDict{i}.sav')
                    del cleanTokenDict
                    # reinitialize curTokenDict
                    curTokenDict = emptyTokenDict.copy()

    # delete some big objects we won't need to conserve RAM
    del knowledgeProcessor
    del freqDict

    print('Folding tokenDict')
    # use last, unsaved curTokenDict as accumulator to fold saved tokenDicts together
    for file in tqdm(os.listdir(TEMP_FOLDER_PATH)):
        loadedTokenDict = load(f'{TEMP_FOLDER_PATH}/{file}')
        curTokenDict.update(tokenDict)
        del tokenDict


    print('Building topTokens')
    # minScore is min normed co-occurence score that tokens need to qualify for topTokens
    minScore = 0

    # build corrDict of top corrNum tokens for each token in tokenDict
    corrDict = {}
    for token, counter in tqdm(emptyTokenDict.items()):
        corrList = [(score, otherToken)
                    for otherToken, score in counter.items()]
        if corrList != []:
            corrList.sort(reverse=True)
            topTokens = [tokenTuple for tokenTuple in corrList[:corrNum]
                            if tokenTuple[0] > minScore]
            corrDict.update({token : topTokens})


    # delete the temporary folder and emptyTokenDict
    delete_temp_folder()
    del emptyTokenDict

    # save corrDict if prompted
    if outPath:
        save(corrDict, outPath)

    return corrDict


def vector_update_corrDict(filePath, corrDict, outPath=None):
    """
    Assuming all knowledge tokens are the title of real wikipedia articles
    and that a correlation dict has already been built, adds a layer of scoring
    onto the key-mapped list of (score, token) tuples for each tuple in corrDict
    using (weighted) cosine similarity between BERT vectors of page texts of which
    each token is the title.
        -filePath:      Path to csv of wiki texts
        -corrDict:      Dictionary mapping each token to a scored list of co-occurence tokens
        -outPath:       Path to which to save the wikiTitle
    """

    CORR_WEIGHT = 0.7
    VEC_WEIGHT = 0.3

    assert ((CORR_WEIGHT + VEC_WEIGHT) == 1), "Sum of weights must be equal to 1."

    # uses BERT client with default POOLING_STRATEGRY and MAX_LEN=400
    from bert_serving.client import BertClient
    bc = BertClient()

    def analyze_wiki_line(wikiLine):
        """
        Helper pulls title and text out of a line in the wikiFile csv and
        returns tuple of title and textVec if the title is a key in corrDict
        """
        # get everything after the first comma
        commaLoc = wikiLine.find(',')
        rawText = wikiLine[(commaLoc+2):]
        # pull out the title
        titleEnd = rawText.find('  ')
        title = rawText[:titleEnd]
        cleanTitle = clean_text(title)
        # title is cleaned for checking but text isn't for better vectorization
        if cleanTitle in corrDict:
            textVec = bc.encode([rawText])[0]
            return (cleanTitle, textVec)
        else:
            return None

    # iterate over wikiFile texts, vectorizing if title is in corrDict
    with open(filePath, 'r') as wikiFile:
        vecList = [analyze_wiki_line(line) for line in tqdm(wikiFile)]

    # convert vec list into dict mapping tokens from corrDict to thier article's text
    vecDict = {tokenTuple[0]:tokenTuple[1] for tokenTuple in vecList
                if not tokenTuple==None}
    del vecList


    def score_similarity(relatedToken, relatedScore, baseVec):
        """
        Helper returns updated score for related token based on vector
        similarity if relatedToken has associated vector, otherwise returns the
        same score
        Args:
            relatedToken:   Token from relatedTokens list of baseToken
            relatedScore:   Weighted co-occurence score of relatedToken to baseToken
            baseVec:        Vector of the base token
        Returns:
            scoreTuple:     (updatedScore, relatedToken)
        """
        # only update score if relatedToken has associated vector
        if relatedToken in vecDict:
            relatedVec = vecDict[relatedToken]
            similarityScore = 1 - cosine(relatedVec, baseVec)
            print(similarityScore)
            relatedScore += similarityScore

        return (relatedScore, relatedToken)

    # iterate over corrDict, updating the scores of each token's related tokens
    # by vector similarity
    for baseToken, relatedTokens in corrDict.items():
        if baseToken in vecDict:
            # cache vector of first para of current baseToken
            baseVec = vecDict[baseToken]
            # update the scores of related tokens using helper
            rescoredRelatedTokens = [score_similarity(relatedToken,
                                                        relatedScore,
                                                        baseVec)
                                        for relatedScore, relatedToken
                                        in relatedTokens]
            # rerank relatedTokens according to new scores and update corrDict
            rescoredRelatedTokens.sort(reverse=True)
            corrDict[baseToken] = rescoredRelatedTokens

    # save to outPath if prompted
    if outPath:
        save(corrDict, outPath)

    return corrDict


def build_token_relationships(filePath, outPath=None):
    """
    Wraps both build_corr_dict and vector_update_corrDict to create dictionary
    mapping each token to a ranked, scored list of related tokens in the form
    {baseToken : [(relationScore, relatedToken)]}
    """
    freqDict = load('data/outData/knowledge/freqDict.sav')
    # knowledgeProcessor = load('data/outData/knowledge/knowledgeProcessor.sav')
    knowledgeProcessor = build_knowledgeProcessor({'harvard', 'college', 'classes',
                                                    'montana', 'james joyce'})

    corrDict = build_corr_dict(filePath=filePath,
                                knowledgeProcessor=knowledgeProcessor,
                                freqDict=freqDict,
                                corrNum=20,
                                outPath=None)

    print(corrDict)

    vectoredCorrDict = vector_update_corrDict(filePath=filePath,
                                                corrDict=corrDict,
                                                outPath=outPath)

    if outPath:
        save(vectoredCorrDict, outPath)

    return vectoredCorrDict
