import os
import hashlib
import csv
import optparse
import time
import report
import db
import redis
import logging
from crawler import *

from sqlite3 import dbapi2 as sqlite3
from contextlib import closing
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

# configuration for flask
DATABASE = 'flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

USAGE = "%prog [options] <url>"
VERSION = "%prog v0.1"

if DEBUG:
    logging.basicConfig(level=logging.DEBUG) 

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

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

def connect_db():
    """Returns a new connection to the database."""
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    """Creates the database tables."""
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()
        
@app.before_request
def before_request():
    """Make sure we are connected to the database each request."""
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db'):
        g.db.close()

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

@app.route('/')
def show_entries():
    #cur = g.db.execute('select title, text from entries order by id desc')
    #entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
    return render_template('index.html')

if __name__ == "__main__":
    #for x in pull_info("linkpart.csv"): print x
    #red_serv = db.open_db()
    #if not db.test_redis_open():
    #    sys.exit(1)

    app.run()
    