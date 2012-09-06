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
        
    def blacklisted(self,url):
        extensions = ['bz2', 'gzip', 'tar', 'zip', 'rar', 'iso', 'avi', 'mov']
        for ex in extensions:
            if ex in url:
                return True
        return False

    def compare_domains(self, url1, url2):
        #url1 is the root
        try:
            if url1 == url2:
                return True
            if url1[-1] == url2[-1] and url1[-2] == url2[-2] and self.extrap:
                #f = open("subdomains.log", mode="a")
                #f.write(url2 + '\n')
                #f.close()
                return True
            else:
                return False
        except:
            return False
            pass
        
    def crawl(self):
        #Build up base/initial queue
        #TODO: fix this

        if self.verbose:
            print "[-] Opening Fetcher with root: " + self.root + " and host: " + self.host
        page = Fetcher(self.root, self.host, self.verbose)
        page.fetch()
        q = Queue()
        for url in page.urls:
            q.put(url)
        followed = [self.root]

        n = 0
        #Iterate and expand on the Q
        while True:
            try:
                url = q.get()
            except QueueEmpty:
                break

            #If depth is 30 then the Q is dug into 30 times - despite possible containing 3k urls. Depth is how 
            #much we dip into the Q
            
            n += 1 #run every time after self.urls.append(url) and the Q is added to

            #followed = list of whats been followed
            #urls = whats been placed in the Q    
            if url not in followed and not self.blacklisted(url):
                try:
                    host = urlparse.urlparse(url)[1]
                    if host is not None:
                        if len(host) == 0:
                            continue
                    if self.verbose: print "[-] host: " + host + " || self.host: " + self.host

                    #if self.locked and re.match(".*%s" % self.host, host):                 
                    if self.locked and self.compare_domains(self.host, host):
                        if self.verbose: print "[-] Enumerating " + host
                        followed.append(url)
                        self.followed += 1
                        page = Fetcher(url, self.host, self.verbose)
                        page.fetch()
                        for i, url in enumerate(page): #throw all the urls on the page crawled into the Q now 
                            if url not in self.urls: #check if url is already followed, if not put in Q
                                self.links += 1
                                q.put(url)
                                self.urls.append(url) 
                        if n > self.depth and self.depth > 0:
                            if self.verbose:
                                print "[-] Breaking based on depth limit ..."
                            break
                    else:
                        if self.verbose:
                            print "[-] Not following: " + urlparse.urlparse(url)[1]
                        
                except Exception, e:
                    print "ERROR: Can't process url '%s' (%s)" % (url, e)
                    print format_exc()
        return self.host

class Fetcher(object):

    def __init__(self, url, root, verbose):
        self.url = url
        self.urls = []
        self.root = root
        self.verbose = verbose

    def __getitem__(self, x):
        return self.urls[x]

    def _addHeaders(self, request):
        request.add_header("User-Agent", AGENT)

    def open(self):
        url = self.url
        try:
            if self.verbose: print "[-] Opening url: " + url
            request = urllib2.Request(url)
            handle = urllib2.build_opener()
        except IOError:
            return None
        return (request, handle)

    def fetch(self):
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
                    if url not in self:
                        self.urls.append(url)

def getLinks(url):
    page = Fetcher(url)
    page.fetch()
    for i, url in enumerate(page):
        print "%d. %s" % (i, url)

