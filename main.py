import os
import hashlib
import csv
import optparse
import time
import report
import db
from crawler import *
import redis
import logging

USAGE = "%prog [options] <url>"
VERSION = "%prog v0.1"

logging.basicConfig(level=logging.DEBUG) 

def writeOutSeo(self):
    """    import csv
    with open('some.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(someiterable)
    """
    pass

def pull_info(self, file='linkpart.csv'):
    """This function will be removed it's used to pull urls from the csv file"""
    ifile  = open(file, "rb")
    reader = csv.reader(ifile)
    domains = []
    
    rownum = 0
    for row in reader:
        if rownum == 0:
            header = row
        else:
            domains.append(row[3]) #linking form column, column 1 is the domain name column
            #colnum = 0
            #for col in row:
                #if colnum == 0:
                #    print '%s' % (col)
            #    colnum += 1
                
        rownum += 1
    
    ifile.close()
    domains = set(domains)
    return domains

def parse_options():
    """parse_options() -> opts, args

    Parse any command-line options given returning both
    the parsed options and arguments.
    """

    parser = optparse.OptionParser(usage=USAGE, version=VERSION)

    parser.add_option("-u", "--url",
            action="store", dest="url",
            help="a single url to crawl")
    
    parser.add_option("-q", "--quiet",
            action="store_true", default=False, dest="quiet",
            help="Enable quiet mode")
    
    parser.add_option("-l", "--limit",
            action="store", type="int", default=30, dest="limit",
            help="Limit the depth of the Queue")
    
    parser.add_option("-e", "--extrap",
        action="store_true", default=False, dest="extrap",
        help="Extrapolate url crawling to other domains")

    parser.add_option("-v", "--verbose",
            action="store_true", default=False, dest="verbose",
            help="Enable verbose mode")

    parser.add_option("-d", "--depth",
            action="store", type="int", default=30, dest="depth",
            help="Maximum depth to traverse")
    
    parser.add_option("-f", "--file",
            action="store", dest="file",
            help="File to pull links from")

    opts, args = parser.parse_args()

    if not opts.url and not opts.file:
        print "[e] Must select a file or a single url option"
        raise SystemExit, 1
    if opts.url and opts.file:
        print "[e] Cannot select both file and single url options"
        raise SystemExit, 1
       
    return opts, args

def main():
    opts, args = parse_options()
    
    verbose = opts.verbose
    depth = opts.depth
    infile = opts.file
    url = opts.url
    extrap = opts.extrap
    limit = opts.limit
    rootdom = ""
    

    #open file reader here
    if infile:
        with open(infile,mode="r") as f:
            for myurl in f:
                myurl = myurl.strip()
    
                sTime = time.time()
            
                print "Crawling %s (Max Depth: %d)" % (myurl, depth)
                crawler = Crawler(myurl, depth, verbose, extrap, limit)
                crawler.crawl()
            
                eTime = time.time()
                tTime = eTime - sTime #start time minus end time
            
                print "Found:    %d" % crawler.links
                print "Followed: %d" % crawler.followed
                print "Stats:    (%d/s after %0.2fs)" % (int(math.ceil(float(crawler.links) / tTime)), tTime)
                
                rep = report.Report(crawler.host, crawler.urls) #crawler.urls is a tuple
                rep.send_redis_relations()
                rep.output_csv_relations()

    elif url:
        sTime = time.time()

        print "Crawling %s (Max Depth: %d)" % (url, depth)
        crawler = Crawler(url, depth, verbose, extrap, limit)
        crawler.crawl()
    
        eTime = time.time()
        tTime = eTime - sTime 
    
        print "Found:    %d" % crawler.links #TODO: This number is crawler.self.links and is not correct
        print "Followed: %d" % crawler.followed
        print "Stats:    (%d/s after %0.2fs)" % (int(math.ceil(float(crawler.links) / tTime)), tTime)
        
        rep = report.Report(crawler.host, crawler.urls) #crawler.urls is a tuple
        rep.send_redis_relations()
        rep.output_csv_relations()

if __name__ == "__main__":
    #for x in pull_info("linkpart.csv"): print x
    red_serv = db.open_db()
    if db.test_redis_open():
        main()
    else:
        logging.debug("redis server not running")
    