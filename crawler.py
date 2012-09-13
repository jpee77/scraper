import re
import sys
import time
import math
import urllib2
import urlparse
import urllib
import contactinfo
import db
import logging
import redis

from cgi import escape
from traceback import format_exc
from Queue import Queue, Empty as QueueEmpty
from BeautifulSoup import BeautifulSoup

#Define the user-agent host header
__version__ = "0.2"
__name__ = "Google Chrome"

AGENT = "%s/%s" % (__name__, __version__)

class Crawler(object):
    '''
    Crawler creates a FIFO queue and a list called followed
    It uses Fetcher to retrive urls on a per page basis and adds them to the top of the Queue while 
    pulling from the bottom
    '''
    
    def __init__(self, root, depth, verbose, extrap, limit, locked=False):
        self.root = root
        self.extrap = extrap
        self.depth = depth
        self.verbose = verbose
        self.locked = locked
        self.host = urlparse.urlparse(root)[1]
        self.urls = []
        self.links = 0
        self.followed = 0
        self.rootdom = "" 
        self.limit = limit
        self.r = db.open_db()
    
    def increment_link_hits(self, url):
        url = urllib.quote(url)
        if self.r.exists("hits:%s" % url):
            self.r.incr("hits:%s" % url)
        else:
            self.r.set("hits:%s" % url, 1)
        
        return self.r.get("hits:%s" % url)
        
    def blacklisted(self,url):
        extensions = ['bz2', 'gzip', 'tar', 'zip', 'rar', 'iso', 'avi', 'mov', 'javascript']
        for ex in extensions:
            if ex in url:
                return True
        return False

    def is_same_domain(self, url1, url2):
        try:
            if url1 == url2:
                return True
            if urlparse.urlparse(url1).netloc == urlparse.urlparse(url2).netloc:
                return True
            else:
                return False
        except:
            raise

    def crawl(self):

        page = Fetcher(self.root, self.host, self.depth, self.extrap, self.verbose)
        page.fetch(0, self.root)
        
        self.increment_link_hits(self.root)
        self.urls.append((0, self.root, None))
        
        q = Queue(maxsize=self.limit)
        
        for i, url in enumerate(page.urls):
            myurl = url[1]
            self.increment_link_hits(myurl)
            
            if i < self.limit:
                self.urls.append(url)
                q.put(url, block=False) #TODO: Ensure this is unique
            if i == self.limit:
                self.locked = True
                
        followed = [self.root]

        while True:
            try:
                url = q.get(timeout=10)
                logging.debug("size of the Q: %d" % q.qsize() ) 
                if q.qsize() > self.limit:
                    break
            except QueueEmpty:
                break

            #url = (0, 'http://www.google.com')
            url_depth = url[0]
            theurl = url[1]
            
            if theurl not in followed and not self.blacklisted(theurl):
                try:
                    host = urlparse.urlparse(theurl)[1]
                    if host is not None:
                        if len(host) == 0:
                            continue
                    
                    logging.debug("host: %s self.host: %s" % (host, self.host) )
                                   
                    if self.extrap or not self.extrap and self.is_same_domain(self.host, host):

                        followed.append(theurl)
                        self.followed += 1
                        
                        page = Fetcher(theurl, self.host, self.depth, self.extrap, self.verbose)
                        page.fetch(url_depth, theurl)
                        
                        for i, depurl in enumerate(page): #this uses __get__item on Fetcher objects and returns fetcher.urls tuple 
                            
                            self.increment_link_hits(depurl[1])
                            
                            if depurl not in self.urls: #check if url is already followed, if not put in Q
                                self.links += 1
                                
                                if not self.locked:
                                    q.put(depurl, block=False)
                                    self.urls.append(depurl) 
                                    
                                    if q.qsize() == self.limit:
                                        self.locked = True
                

                    else:
                        logging.debug("not following %s" % urlparse.urlparse(theurl)[1])
                        
                except Exception, e:
                    logging.critical("ERROR: Can't process url '%s' (%s)" % (url, e))
                    logging.critical(format_exc())
            else:
                logging.debug("not following %s" % theurl)
        
        return self.host

class Fetcher(object):
    '''
    Fetcher is per page url retrival mechanism that is iterable and feeds links back to Crawler
    '''

    def __init__(self, url, root, depth, extrap, verbose):
        self.url = url
        self.urls = []
        self.root = root
        self.depth= depth
        self.extrap = extrap
        self.verbose = verbose
        self.thomas_count = 0

    def __getitem__(self, x):
        return self.urls[x]

    def _addHeaders(self, request):
        request.add_header("User-Agent", AGENT)
        
    def is_blacklisted(self,url):
        extensions = ['bz2', 'gzip', 'tar', 'zip', 'rar', 'iso', 'avi', 'mov', 'javascript']
        for ex in extensions:
            if ex in url:
                return True
        return False
        
    def is_same_domain(self, url1, url2):
        try:
            if url1 == url2:
                return True
            if urlparse.urlparse(url1).netloc == urlparse.urlparse(url2).netloc:
                return True
            else:
                return False
        except:
            raise
        
    def open(self):
        url = self.url
        try:
            logging.debug("opening url: %s" % url)
            request = urllib2.Request(url)
            handle = urllib2.build_opener()
        except IOError:
            return None
        return (request, handle)

    def fetch(self, depth, parent): 
        request, handle = self.open()
        self._addHeaders(request)
        
        content_cache = []
        
        if handle:
            try:

                #This function returns a file-like object with two additional methods
                content = handle.open(request,timeout=260)
                for line in content:
                    content_cache.append(line)
                
                soup = BeautifulSoup( unicode('\n'.join(content_cache), "utf-8",errors="replace") )
                
                #Could submit to redis from contact_info
                ci = contactinfo.ContactInfo(content_cache, self.root, self.url, self.verbose)
                thomas_count = ci.find_thomas()
                mail_ret = ci.scan_mail()
                
                tags = soup('a')
                
            except urllib2.HTTPError, error:
                if error.code == 404:
                    print '[HTTP Error] ' + self.url
                    #print >> sys.stderr, "ERROR: %s -> %s" % (error, error.url)
                else:
                    print '[timed out] ' + self.url
                    print >> sys.stderr, "ERROR: %s" % error
                tags = []
            except urllib2.URLError, error:
                print '[Url Error] ' + self.url
                #print >> sys.stderr, "ERROR: %s" % error
                tags = []
            except:
                raise
                print '[Timed Out] ' + self.url
                tags = []
                
            for tag in tags:
                        
                href = tag.get("href")
                
                if href is not None:
                    if href.startswith('/'):
                        href = 'http://' + self.root + href
                    
                    url = urlparse.urljoin(self.url, escape(href))

                    if url not in (url for depth, url, parent in self.urls) and not self.is_blacklisted(url):
                        
                        if self.extrap or not self.extrap and self.is_same_domain(url, 'http://' + self.root):
                            
                            if self.is_same_domain(url, 'http://' + self.root):
                                logging.debug("adding url: %s with depth 0 to self.urls" % url)
                                self.urls.append((0, url, parent))
                                
                            else:
                                if depth < self.depth:
                                    logging.debug("adding url: %s with depth: %d to self.urls" % (url, depth+1))
                                    self.urls.append((depth+1, url, parent))

                                pass
                        else:
                            logging.debug("not following %s for extrap reasons" % url[:50])

                    else:
                        logging.debug("duplicate or blacklist found for %s" % url[:50])

def getLinks(url):
    page = Fetcher(url)
    page.fetch(0)
    for i, url in enumerate(page):
        print "%d. %s" % (i, url)

