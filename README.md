scraper
=======

https://github.com/jpee77/scraper.git
http://208.113.228.200:8080/trac

scraper is a web crawler that gathers specific information

======================================

For time keeping: git commit -m "Remove some extra whitespace f:15"

TODO: Create a breakdown of link hits and reporting and output to timestamped csv
  --output csv   [ searched url ] [ link on page ] [ number of times this link is shown  ] [ number of links containing domain ]

TODO: Add remote error reporting for exceptions

TODO: Depth 3 takes ages

BUG: When accessing invalid links the program stalls out - threading waits at the Q for seemingly nothing? http://localhost/www.thomasnet.com


=======================

Depends:
sudo apt-get install python
sudo easy_install redis
sudo apt-get install redis-server
