import db
import redis
import datetime
import urllib
import csv
import logging

class Report:
    def __init__(self, root, urls):
        self.r = db.open_db()
        self.root = root
        self.urls = urls
        self.hash_name = ""
    
    def send_redis_relations(self):
        print "[redis] Using redis index 0"
        
        try:
            for u in self.urls:
                
                logging.debug("[redis] storing url: %s and parent: %s at depth: %d" % (str(u[1])[:40], str(u[2])[:20], u[0]) )
    
                depth = str(u[0])
                url = urllib.quote(str(u[1]))
                parent = str(u[2])
                
                self.hash_name = url 
                
                if self.r.sadd("%s::urls" % self.root, url):
                    self.r.hset(self.hash_name, "url", url)
                    self.r.hset(self.hash_name, "parent", parent)
                    self.r.hset(self.hash_name, "depth", depth)
                    self.r.hset(self.hash_name, "date", datetime.date.today())
                
            return True
        
        except UnicodeEncodeError:
            pass
        
        except:
            raise
    
    def output_csv_relations(self):

        emails = None
        
        with open("%s.csv" % self.root, 'wb') as f:
            
            seo_writer = csv.writer(f, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            seo_writer.writerow(["Scraper Report On: %s" % self.root])
            seo_writer.writerow(['Url', 'Degree of Separation from ' + self.root, 'Links to Thomasnet.com', 'Emails' ])
            
            try:
                for u in self.r.smembers("%s::urls" % self.root):
                    
                    if self.r.hexists(u, 'url'):
                        udict = self.r.hgetall(u)
                        #print u + ' ' + str(udict)
                        tcount = str(self.r.get("tcount:%s" % u) )
                    
                        if self.r.exists("emails::%s" % u):
                            emails = self.r.smembers("emails::%s" % u)
                        
                        if emails is not None:
                            seo_writer.writerow([u, udict['depth'], tcount, ' '.join(emails)  ])
                        else:
                            seo_writer.writerow([u, udict['depth'], tcount, "None"  ])
                
                        
                seo_writer.writerow(["[All emails]"])
                for em in self.r.smembers("emails::%s" % self.root):
                    seo_writer.writerow([em])
            except:
                raise
        
            