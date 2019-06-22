from dataStructures.objectSaver import save, load
import matplotlib.pyplot as plt
import numpy as np
import models.ranking.pageRanker as pageRanker
import json

class Thicctable():
    """
    Class to store indexed webdata as keys mapping to
    list of tuples of Page() objects and their score
    """

    def __init__(self, keys):
        """ Initialize branch as key-val store mapping keys to empty lists """
        self.topDict = {key:[] for key in keys}
        print(f"Table initialized with {len(keys)} buckets.")

    ### FUNCTIONS FOR MODIFYING KEYS ###
    def add_key(self, key):
        """ Adds key and corresponding empty list to topDict """
        self.topDict.update({key:[]})
        return True

    def remove_key(self, key):
        """ Removes key and associated list from topDict """
        del self.topDict[key]
        return True

    def kill_smalls(self, n):
        """ Removes keys with lists under length n. Use carefully! """
        # find keys that map to a list shorter than n
        smallKeys = [key for key in self.topDict if len(self.topDict[key]) < n]
        for key in smallKeys:
            del self.topDict[key]
        return True

    ### FUNCTIONS FOR MODIFYING KEY-MAPPED LISTS ###
    def clear_key(self, key):
        """
        Clears the list associated with a key in the topDict
        Same funcitonality as clip_key(key, 0).
        """
        self.topDict[key] = []
        return True

    def clip_key(self, key, n):
        """ Clips list mapped by key to n elements """
        self.topDict[key] = self.topDict[key][:n]
        return True

    def insert_pageTuple(self, key, pageTuple):
        """ Adds value to the list mapped by key in topDict """
        self.topDict[key].append(pageTuple)
        return True

    def remove_value(self, key, url):
        """
        Removes elements with given url from list mapped by key in topDict
        """
        # check url examines the url from a page obj (second elt of page tuple)
        check_url = lambda pageTuple : (pageTuple[1].url != url)
        self.topDict[key] = list(filter(check_url, self.topDict[key]))
        return True

    def sort_key(self, key):
        """ Sorts key list based on page scores (first elt of tuple) """
        # get_score gets the score from a page tuple (the first elt)
        get_score = lambda pageTuple : pageTuple[0]
        self.topDict[key].sort(key=get_score, reverse=True)
        return True

    def sort_all(self):
        """ Sorts list mapped by each key in topDict based on index """
        # iterate over keys and sort
        for key in self.topDict:
            self.sort_key(key)
        return True

    def bucket_page(self, pageObj):
        """
        Args: Page object to insert into relevent buckets and score.
        Wraps insert_value and calls models.ranking to score page and sort
        into all applicable buckets
        """
        # pull tokens from pageObj
        pageTokens = pageObj.knowledgeTokens
        for token in pageTokens:
            try:
                # get score of page from pageRanker
                pageScore = pageRanker.score_single(pageObj, token)
                # create bucket-specific pageTuple of score and pageObj
                pageTuple = (pageScore, pageObj)
                # insert tuple of score and pageObj into appropriate bin
                self.insert_pageTuple(key=token, pageTuple=pageTuple)
            except Exception as e:
                print(e)
        return True

    ### SEARCH FUNCTIONS ###
    def search_display(self, key, tokenList, n=20):
        """
        Returns display tuple from top n pages from (sorted) key with
        window text according to token list
        """
        display_pageTuple = lambda pageTuple : pageTuple[1].display(tokenList)
        return list(map(display_pageTuple, self.topDict[key][:n]))

    def search_full(self, key, n=20):
        """ Returns the top n pageTuples of the list mapped by key in topDict """
        return self.topDict[key][:n]

    ### SAVE/LOAD FUNCTIONS ###
    def save(self, outPath):
        """ Writes contents of Thicctable to json file in outPath.json """
        with open(f"{outPath}.json", 'w+') as FileObj:
            json.dump(self.topDict, FileObj)
        return True

    def load(self, inPath):
        """ Loads topDict saved in json file """
        with open(f"{inPath}.json", 'r') as FileObj:
            self.topDict = json.load(FileObj)
        return True

    ### METRICS FUNCTIONS ###
    def key_length(self, key):
        """
        Returns the length of the value list associated with a key.
        Useful metric for comparing importance of keys.
        """
        return len(self.topDict[key])

    def plot_lengths(self, outPath=""):
        """
        Plot bar chart of lengths of value lists associated with topDict
        keys and print length metrics across all lists.
        """
        # get list of all keys and list of length of values
        keyList, lengthList = self.topDict.keys(), list(map(lambda elt : len(elt), self.topDict.values()))
        # get metrics of lengthList
        meanLength = np.mean(lengthList)
        minLength, maxLength= min(lengthList), max(lengthList)
        print(f"Length Metrics:\n\tMean: {meanLength}\n\tMin: {minLength}\n\tMax: {maxLength}")
        # plot keyList against lengthLis
        plt.bar(keyList, lengthList)
        plt.title("Number of Pages Per Key")
        plt.xlabel("Keys")
        plt.ylabel("Number Pages")
        if not (outPath==""):
            plt.savefig(outPath)
        else:
            plt.show()
        return True

    def plot_key_metrics(self, key, indexLambda, outPath=""):
        """
        Print and plot metrics for data accessed  by index lambda across
        elements of list mapped by key. Only works for number values,
        such as score, length, time, etc.
        """
        # fetch list mapped by key
        valueList = self.topDict[key]
        # apply indexLambda to get data of interest
        mappedList = list(map(indexLambda, valueList))
        # get metrics of mappedList
        mappedMean = np.mean(mappedList)
        mappedMin, mappedMax = min(mappedList), max(mappedList)
        print(f"Metrics:\n\tMean: {mappedMean}\n\tMin: {mappedMin}\n\tMax: {mappedMax}")
        # plot mappedList from head to tail
        plt.plot(mappedList)
        plt.title(f"Indexed Metrics of {key} Key")
        plt.xlabel("Index in List")
        plt.ylabel("Value")
        if not (outPath==""):
            plt.savefig(outPath)
        else:
            plt.show()
        return True



# Testing

# import time
# import numpy as np
#
# NUM = 100000
#
# x = Thicctable(keys=['a','b','c'])
#
# keyList = np.random.choice(['a','b','c'], size=NUM)
# v1List = np.random.randint(0, 10000, size=NUM)
# v2List = np.random.choice(['a','b','c','d','e','f','g','c'], size=NUM)
#
# insertStart = time.time()
# for i, key in enumerate(keyList):
#     x.insert_value(key, (v1List[i], v2List[i]))
# insertEnd = time.time()
# print(f"Insertion: {insertEnd - insertStart}")
#
# sortStart = time.time()
# x.sort_all(index=0)
# sortEnd = time.time()
# print(f"Sorting: {sortEnd - sortStart}")
#
# start = time.time()
# print(x.search_index('a', indexLambda=(lambda x:x[1])))
# end  = time.time()
# iSearch = end - start
#
# start = time.time()
# print(x.search_full('a'))
# end  = time.time()
# aSearch = end - start
#
# print(f"Search:\n\ti:  {iSearch}\n\ta: {aSearch}")
#
# x.plot_lengths()

# saveStart = time.time()
# x.save("test.thicc")
# saveEnd = time.time()
# print(f"Save: {saveEnd - saveStart}")
