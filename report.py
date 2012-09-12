import db
import redis
import datetime
import urllib
import logging

class Report:
    def __init__(self, root, urls):
        self.r = db.open_db()
        self.root = root
        self.urls = urls
        self.hash_name = ""
    
    def send_emails(self):
        ctr = 0
        print "[-] Generating report ..."
        #Get a count of gathered emails
        for em in self.r.smembers("emails:"+self.root):
            ctr += 1
        print "[1] " + str(ctr) + " emails gathered"
        return self.r.smembers("emails:"+self.root)
    
    def send_redis_relations(self):
        print "[redis] Using redis index 0"
        
        for u in self.urls:
            
            logging.debug("[redis] storing url: %s and parent: %s at depth: %d" % (str(u[1])[:40], str(u[2])[:20], u[0]) )

            depth = str(u[0])
            url = urllib.quote(str(u[1]))
            parent = str(u[2])
            
            self.hash_name = url
            
            self.r.hset(self.hash_name, "url", url)
            self.r.hset(self.hash_name, "parent", parent)
            self.r.hset(self.hash_name, "depth", depth)
            self.r.hset(self.hash_name, "date", datetime.date.today())
            
        return True
            
            