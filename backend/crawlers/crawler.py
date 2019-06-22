# Responsible for building database of page data from list of URLs.
# Outsources URL processing to urlAnalyzer.py
# Outsources HTML processing to htmlAnalyzer.py
# Outsoucres database definitions to thicctable.py

import os
from queue import Queue
from threading import Thread
import crawlers.urlAnalyzer as urlAnalyzer
import crawlers.htmlAnalyzer as htmlAnalyzer
import models.knowledge.knowledgeBuilder as knowledgeBuilder
from dataStructures.simpleStructures import Simple_List, Metrics
from dataStructures.thicctable import Thicctable
from dataStructures.objectSaver import save, load
from models.binning.docVecs import load_model

import time

def scrape_urlList(urlList, queueDepth=10, workerNum=20, maxLen=100, outPath=""):
    """
    Builds wide column store of url data from urlList with recursive search
    Args: urlList to scrape, depth of url_queue, number of workers to spawn
    Returns: wide column store of data from each url
    """

    # load models and datasets
    knowledgeProcessor = load('data/outData/knowledge/knowledgeProcessor.sav')
    freqDict = load('data/outData/knowledge/freqDict.sav')
    d2vModel = load_model('data/outData/binning/d2vModel.sav')

    testSimple = Simple_List()

    # queue to hold urlList
    urlQueue = Queue(queueDepth)
    # set to hold , previously scraped URLs
    scrapedUrls = set()
    # struct to keep track of metrics
    scrapeMetrics = Metrics()

    def enqueue_urlList(urlList):
        """
        Cleans and enqueues URLs contained in urlList, checking if
        previously scraped
        """
        for url in urlList:
            if not url in scrapedUrls:
                scrapedUrls.add(url)
                urlQueue.put(url)

    def worker():
        """ Scrapes popped URL from urlQueue and stores data in database"""
        while True:
            # pop top url from queue
            url = urlQueue.get()
            try:
                pageList = htmlAnalyzer.scrape_url(url, knowledgeProcessor, freqDict, d2vModel)
                # database.bucket_page(pageList)
                testSimple.add(pageList)
                # pull list of links from pageDict and put in urlQueue
                # enqueue_urlList(pageList[3])
                # update scrape metrics
                scrapeMetrics.add(error=False)
            except Exception as e:
                print(e)
                # update scrape metrics
                scrapeMetrics.add(error=True)
            # log progress
            if (scrapeMetrics.count % 10 == 0):
                testSimple.save(f"data/thicctable/tempLists/{str(scrapeMetrics.count)}")
                testSimple.clear()
                os.system('clear')
                print(testSimple.data)
            print(f"\t{scrapeMetrics.count} URLs analyzed with {scrapeMetrics.errors} errors!", end="\r")
            # signal completion
            urlQueue.task_done()

    # spawn workerNum workers
    for _ in range(workerNum):
        t = Thread(target=worker)
        t.daemon = True
        t.start()

    # load cleaned initial urls into url_queue
    urlList = list(map(lambda url:urlAnalyzer.fix_url(url), urlList))
    enqueue_urlList(urlList)

    # ensure all urlQueue processes are complete before proceeding
    urlQueue.join()

    return True
