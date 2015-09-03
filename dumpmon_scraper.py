#!/usr/bin/env python

from StringIO import StringIO
from lxml import html
from time import sleep
from datetime import datetime
from dump_stats import Stats
import os
import re
import sys
import filecmp
import datetime
import logging
import requests

Stats = Stats()

requests_log = logging.getLogger("requests")  #Disables "Starting new HTTP Connection (1)" log message
requests_log.setLevel(logging.WARNING)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
fileHandler = logging.FileHandler('dumpmon.log')
fileHandler.setFormatter(formatter)
streamHandler = logging.StreamHandler(sys.stdout)
streamHandler.setFormatter(formatter)

logger = logging.getLogger('dumpmon')
logger.addHandler(streamHandler)
logger.addHandler(fileHandler)
logger.setLevel(logging.INFO)

logger.info('Starting...')

prev_links = []

while True:
    
    try:

        r = requests.get('https://www.twitter.com/dumpmon')
        tree = html.fromstring(r.text)
        links = tree.xpath("//a[@class='twitter-timeline-link']//@title")
        for link in links:
                if link not in prev_links:
                    if 'dumpmon.com' in link:
                        id = link.split('=')[1]
                    else:
                        id = None

                    if (id != None):
                        dump = requests.get(link).text.encode('utf-8', 'ignore')
                        if re.search('paste has been removed', dump, re.IGNORECASE):
                            logger.info('Dump id {} has been removed! skipping...'.format(id))
                            continue
 
                        dump_buffer = StringIO(dump)
                        dump_name = './dumps/' + id

                        if id in os.listdir('./dumps'):
                            logger.info('Dump id {} is present in directory'.format(id))
                            with open('./dumps/' + id, 'r') as file:
                                d_buffer = file.read(500) 
                                if d_buffer == dump_buffer.read(500):
                                    logger.info('Contents of dump id {} appear to be the same! skipping...'.format(id))
                                    continue
                                else:   
                                    logger.info('Contents of dump id {} differ! dumping...'.format(id))
                                    dump_name = './dumps/{}_{}'.format(id, datetime.strftime('%Y-%m-%d_%H:%M:%S:%s'))
  
                        Stats.text = dump
                        dump_type = Stats.match()

                        log_output = 'New dump detected: %s' % link

                        if dump_type == 'db_dump':
                            log_output += ' Emails: %s Hashes: %s Keywords: %s' % (Stats.num_emails, Stats.num_hashes, Stats.db_keywords)
                            if Stats.num_emails > 0 and Stats.num_hashes > 0:
                                log_output += ' E/H: %s' % str(round(Stats.num_emails / float(Stats.num_hashes), 2))

                        elif dump_type == 'cisco':
                            log_output += ' Possible Cisco configuration file'
                        elif dump_type == 'google_api':
                            log_output += ' Possible Google API key(s)'
                        elif dump_type == 'honeypot':
                            log_output += ' Possible Dionaea Honeypot Log'
                        elif dump_type == 'pgp_private':
                            log_output += ' Possible PGP private key'
                        elif dump_type == 'ssh_private':
                            log_output += ' Possible SSH private key'
                        elif dump_type == None:
                            continue

                        with open(dump_name, 'w') as file:
                            file.write(dump)
                            file.close()

                        logger.info(log_output)

    except Exception, e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.warning((str(e), exc_type, fname, exc_tb.tb_lineno))

    prev_links = links
    sleep(10)
