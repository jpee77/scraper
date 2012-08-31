scraper
=======

scraper is a web crawler that gathers specific information
#hxs.select('//a[contains(@href, "image")]/text()').re(r'Name:\s*(.*)')
#reddit title selector
#hxs.select('//a[@class="title "]/text()').extract()

For time keeping: git commit -m "Remove some extra whitespace f:15"

TODO: Seperate run-time switching for internal url and external url grabbing

TODO: Create a breakdown of link hits and reporting and output to timestamped csv
  --output csv   [ searched url ] [ link on page ] [ number of times this link is shown  ] [ number of links containing domain ]

Depth should be the number of times a link is followed from the base set of urls gathered on the page


ADD: Database support (redis) for saving the matches on emails and passing it back to the main.py from contactinfo.py

BUG: When accessing invalid links the program stalls out - threading waits at the Q for seemingly nothing?

Depends:
sudo apt-get install python
sudo easy_install redis
sudo apt-get install redis-server
