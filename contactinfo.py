import re
import string
import time
import db

#search for @domain
#wget the entire contact page and save it
#contact, contactus

class ContactInfo(object):
    def __init__(self, content, root, verbose=False):
        self.content = content
        self.verbose = verbose
        self.root = root
        self.matches = []

    def scanMail(self):
        mailsigs = ['\w+&#64;[a-z,A-Z,\.,0-9]+','\w+@[a-z,A-Z,0-9,\.]+\.\w+', '\w+ at \w+\.(com,net,org)', '\w+ \[.+\]\ \w+\.(com,net,org)', 'mailto:\w+@\w+.(com,net,org)']
        
        if self.verbose: print "[-] Scanning for mail information..."

        if self.content:
            for line in self.content:
                line = line.rstrip()
                #print str(type(line))
                if line is not None:
                    #expand the Beautify thing
                    for match_sig in mailsigs:
                        mail_regex = re.compile(r"" + match_sig)
                        matchObj = mail_regex.search(line)
                        if matchObj:
                            self.matches.append(matchObj.group())
                            if self.verbose:
                                print "[match] " + match_sig + " " + matchObj.group() #+ " line: " + line 
                        else:
                            pass
                            #print "No matches for @"
                else:
                    print "not a line or empty"
                    pass #print line
        else:
            "[v] soup_content was empty when passed to " + __name__
        
        if self.matches is not None: 
            r_server = db.open_db()
            for m in self.matches:
                r_server.sadd("emails:"+self.root, m)
                if self.verbose: print "[redis] Adding to set " + "emails:"+self.root
        else:
            return None
                
    
    def scanPhone(self, soup):
        pass