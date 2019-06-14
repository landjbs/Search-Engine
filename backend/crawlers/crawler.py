# Responsible for building database of page data from list of URLs.
# Outsources URL processing to urlAnalyzer.py
# Outsources HTML processing to htmlAnalyzer.py
# Outsoucres database definitions to thicctable.py

import sys, os
from queue import Queue
from threading import Thread
import urlAnalyzer as urlAnalyzer
import htmlAnalyzer as htmlAnalyzer

sys.path.append(os.path.abspath(os.path.join('..')))
from dataStructures.impleStructures import Simple_List, Metrics
from dataStructures.objectSaver import save

def scrape_urlList(urlList, queueDepth=10, workerNum=20, maxLen=100, outPath=""):
    """
    Builds wide column store of url data from urlList with recursive search
    Args: urlList to scrape, depth of url_queue, number of workers to spawn
    Returns: wide column store of data from each url
    """
    # queue to hold urlList
    urlQueue = Queue(queueDepth)
    # set to hold unclean, previously scraped URLs
    scrapedSet = set()
    # struct to hold scraped data
    outStore = Simple_List()
    # struct to keep track of metrics
    scrapeMetrics = Metrics()

    def enqueue_urlList(urlList):
        """
        Cleans and enqueues URLs contained in urlList, checking if
        previously scraped
        """
        for url in urlList:
            if not url in scrapedSet:
                # add unclean url to set of scraped urls
                scrapedSet.add(url)
                # clean url and add to urlQueue
                urlQueue.put(url)

    def worker():
        """ Scrapes popped URL from urlQueue and stores data in outStore()"""
        while True:
            # pop top url from queue
            url = urlQueue.get()
            try:
                pageList = htmlAnalyzer.scrape_url(url)
                # add pageDict to outStore
                outStore.add(pageDict)
                # pull list of links from pageDict and enqueue
                enqueue_urlList(pageDict['linkList'])
                # update scrape metrics
                scrapeMetrics.add(error=False)
            except:
                # update scrape metrics
                scrapeMetrics.add(error=True)
            # log progress
            print(f"\t{scrapeMetrics.count} URLs analyzed with {scrapeMetrics.errors} errors!", end="\r")
            # signal completion
            urlQueue.task_done()

    # spawn workerNum workers
    for _ in range(workerNum):
        t = Thread(target=worker)
        t.daemon = True
        t.start()

    # load cleaned initial urls into url_queue
    urlList = list(map(lambda url:urlAnalyzer.clean_url(url), urlList))
    enqueue_urlList(urlList)

    # ensure all urlQueue processes are complete before proceeding
    urlQueue.join()

    return outStore
