import re
import sys
import time
import math
import urllib2
import urlparse
import contactinfo
import db

from cgi import escape
from traceback import format_exc
from Queue import Queue, Empty as QueueEmpty
from BeautifulSoup import BeautifulSoup

#Define the user-agent host header
__version__ = "0.2"
__name__ = "Google Chrome"

AGENT = "%s/%s" % (__name__, __version__)

class Crawler(object):
#""" Crawler encompasses many pages """

    def __init__(self, root, depth, verbose, extrap, locked=True):
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
        
    def blacklisted(self,url):
        extensions = ['bz2', 'gzip', 'tar', 'zip', 'rar', 'iso', 'avi', 'mov', 'javascript']
        for ex in extensions:
            if ex in url:
                return True
        return False

    def isSameDomain(self, url1, url2):
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
        page.fetch(0)
        q = Queue()
        for url in page.urls:
            q.put(url) #TODO: Ensure this is unique
        followed = [self.root]


        while True:
            try:
                url = q.get(timeout=10)
                if q.qsize() == 0:
                    print "Size of the Q: " + str(q.qsize())
                time.sleep(2) #TODO: stopping here
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
                    
                    if self.verbose: 
                        print "[-] host: " + host + " || self.host: " + self.host
                                   
                    if self.extrap or not self.extrap and self.isSameDomain(self.host, host):

                        followed.append(theurl)
                        self.followed += 1
                        
                        page = Fetcher(theurl, self.host, self.depth, self.extrap, self.verbose)
                        page.fetch(url_depth)
                        
                        for i, depurl in enumerate(page): #this uses __get__item on Fetcher objects and returns fetcher.urls tuple 
                            if depurl not in self.urls: #check if url is already followed, if not put in Q
                                self.links += 1
                                q.put(depurl)
                                self.urls.append(depurl) 

                    else:
                        if self.verbose:
                            print "[-] Not following: " + urlparse.urlparse(theurl)[1]
                        
                except Exception, e:
                    print "ERROR: Can't process url '%s' (%s)" % (url, e)
                    print format_exc()
            else:
                print "[-] NOT FOLLOWING: " + theurl
        return True

class Fetcher(object):
#""" Remember Fetcher is per page """

    def __init__(self, url, root, depth, extrap, verbose):
        self.url = url
        self.urls = []
        self.root = root
        self.depth= depth
        self.extrap = extrap
        self.verbose = verbose

    def __getitem__(self, x):
        return self.urls[x]

    def _addHeaders(self, request):
        request.add_header("User-Agent", AGENT)
        
    def isSameDomain(self, url1, url2):
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
            if self.verbose: print "[-] Opening url: " + url
            request = urllib2.Request(url)
            handle = urllib2.build_opener()
        except IOError:
            return None
        return (request, handle)

    def fetch(self, depth): 
        request, handle = self.open()
        self._addHeaders(request)
        if handle:
            try:
                content = unicode(handle.open(request,timeout=10).read(), "utf-8",errors="replace")
                content_fd = handle.open(request,timeout=10)
                soup = BeautifulSoup(content)
                
                #Here we pass the soup off to the contact information scanner
                ci = contactinfo.ContactInfo(content_fd,self.root,self.verbose)
                #ret will be None or a list
                match_res = ci.scanMail()
                
                tags = soup('a')
            except urllib2.HTTPError, error:
                if error.code == 404:
                    print >> sys.stderr, "ERROR: %s -> %s" % (error, error.url)
                else:
                    print >> sys.stderr, "ERROR: %s" % error
                tags = []
            except urllib2.URLError, error:
                print >> sys.stderr, "ERROR: %s" % error
                tags = []
            for tag in tags:
                        
                href = tag.get("href")
                if href is not None:
                    
                    url = urlparse.urljoin(self.url, escape(href))

                    if url not in (url for depth, url in self.urls):
                        
                        if self.extrap or not self.extrap and self.isSameDomain(url, 'http://' + self.root):
                            
                            if self.isSameDomain(url, self.root):
                                if self.verbose: 
                                    print "[-] Adding " + url + " with depth: 0"
                                self.urls.append((0, url))
                                
                            else:
                                if depth < self.depth:
                                    if self.verbose: 
                                        print "[-] Adding " + url + " with depth: " + str(depth+1)
                                    self.urls.append((depth+1, url))
                                pass

                    else:
                        print "[D] Duplicate found: " + url

def getLinks(url):
    page = Fetcher(url)
    page.fetch(0)
    for i, url in enumerate(page):
        print "%d. %s" % (i, url)

