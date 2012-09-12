import re
import string
import time
import db
import logging
import urlparse
import urllib
import sys
from BeautifulSoup import BeautifulSoup
from cgi import escape

#search for @domain
#wget the entire contact page and save it
#contact, contactus

class ContactInfo(object):
    def __init__(self, content, root, url, verbose=False):
        self.content = content
        self.verbose = verbose
        self.url = urllib.quote(url)
        self.root = root
        self.matches = []
        self.r = db.open_db()
    
    def find_thomas(self):
        if self.content:
            
            logging.debug("scanning for thomasnet.com...")
            
            soup = BeautifulSoup( unicode('\n'.join(self.content), "utf-8",errors="replace") )
            tags = soup('a')
            
            thomas_ctr = 0
            
            for tag in tags:
                href = tag.get("href")
                
                if href is not None:           
                    url = urlparse.urljoin(self.url, escape(href))
                    
                    thomas_regex = re.compile('thomasnet.com')
                    matchObj = thomas_regex.search(url)
                    if matchObj:
                        thomas_ctr += 1
                        print "[THOMASNET MATCH] " + matchObj.group()
                
            self.r.sadd('tcount::'+self.url ,thomas_ctr)
                

    def scan_mail(self):
        
        #\w+@[a-z,A-Z,0-9,\.]+\.\w+ 
        mailsigs = ['\w+&#64;[a-z,A-Z,\.,0-9]+','[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}', '\w+ at \w+\.(com,net,org)', '\w+ \[.+\]\ \w+\.(com,net,org)', 'mailto:\w+@\w+.(com,net,org)']
        
        logging.debug("Scanning for mail information...")

        if self.content:

            for line in self.content:
                
                line = line.rstrip()

                if line is not None:

                    for match_sig in mailsigs:
                        mail_regex = re.compile(r"" + match_sig)
                        matchObj = mail_regex.search(line)
                        if matchObj:
                            self.matches.append(matchObj.group())
                            logging.debug(match_sig + " " + matchObj.group())

                else:
                    pass
        else:
            logging.debug("soup content was empty")
        
        if self.matches is not None: 
            for e in self.matches:
                logging.debug("[redis] pushing email: %s" % e)
                self.r.rpush('email::' + self.url, e)
                
            for e in self.matches:
                logging.debug("[redis] pushing emails to one list: %s" % e)
                self.r.rpush('email:' +urllib.quote(self.root), e)

            
        else:
            return "None"
                
    
    def scanPhone(self, soup):
        pass