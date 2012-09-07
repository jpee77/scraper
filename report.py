import db
import redis

class Report:
    def __init__(self, root, lurls):
        self.r = db.open_db()
        self.root = root
        self.urls = lurls
    
    def getEmails(self):
        ctr = 0
        print "[-] Generating report ..."
        #Get a count of gathered emails
        for em in self.r.smembers("emails:"+self.root):
            ctr += 1
        print "[1] " + str(ctr) + " emails gathered"
        return self.r.smembers("emails:"+self.root)
    
    def getRelations(self):
        print "nigger"
        print self.urls