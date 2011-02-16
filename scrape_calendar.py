#!/usr/bin/env python
# encoding: utf-8
"""
scrape_calendar.py

Created by Jared Knipp on 2011-02-13.
Copyright (c) 2011 All rights reserved.
"""

import sys
import os
import urllib
import mechanize
import cookielib
from BeautifulSoup import BeautifulSoup
from BeautifulSoup import BeautifulStoneSoup
import re
import cgi
from datetime import datetime
import time
from services import GCalService

url = 'http://water.com'
user = ''
pwd = ''
info_url = 'https://selfserve.water.com/OA_HTML/web/selfserve/dswhtml/dswCusVwHomePage.jsp'

# Google calendar 
GCAL_USER = ''
GCAL_PASSWORD = ''
GCAL_DEFAULT_LOCATION = ""
GCAL_DEFAULT_SOURCE = 'Water.com_Google-Calendar_Script'
GCAL_DEFAULT_TIME_ZONE = 'America/Chicago'

def main():
	br = mechanize.Browser()
	
	# cookie jar
	cj = cookielib.LWPCookieJar()
	br.set_cookiejar(cj)
	
	# Browser options
	br.set_handle_equiv(True)
	br.set_handle_gzip(True)
	br.set_handle_redirect(True)
	br.set_handle_referer(True)
	br.set_handle_robots(False)
	
	# Follows refresh 0 but not hangs on refresh > 0
	br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
	
	# User-Agent
	br.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8')]
	
	# Open site and select 1st form 
	br.open(url)
	br.select_form(nr=0)
	
	# enter credentials then login
	br.form['username'] = user
	br.form['password'] = pwd
	br.submit()
	
	# Go to calendar page & create the soup
	response = br.open(info_url)
	html = response.read()
	soup = BeautifulSoup(html, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)

	# Find the calendar table
	calendar_tbl = soup.find("div", {"id": "fDivDelCalCurrYear"})
	months = calendar_tbl.findChildren("tr", {"class": 'dswHV08SblueBold'})
	dates =  calendar_tbl.findChildren("tr", {"class": 'dswHV08LGrey'})
	
	# Extract months and dates from each cell, 1 list for each
	m_list = sum([[str(c.text) for c in m.findChildren("td", {"align": "center"})] for m in months], [])
	d_list = sum([[str(c.text.replace(u'\xa0', '')) for c in d.findChildren("td", {"align": "center", "height": "30"})] for d in dates], [])
	
	# Merge the lists as lists of tuples
	# Then make new list out of the list of tuples
	newList = [i[1] + ' ' + i[0] for i in zip(m_list, d_list)]
	
	# Create new dates based on format
	dates = make_dates(newList)
	gcal = GCalService(GCAL_USER, GCAL_PASSWORD, GCAL_DEFAULT_SOURCE)

	#gcalendar = gcal.create_calendar('Water Calendar', 'Water Delivery Calender', GCAL_DEFAULT_LOCATION, GCAL_DEFAULT_TIME_ZONE)
	
	for d in dates:
		# Add event to default calendar
		gcal_event = gcal.create_event('Water Delivery', 'Water Delivery Date', GCAL_DEFAULT_LOCATION, d)
		
		# Add reminder to event 60 minutes before, based on user's default reminder 
		# notification settings
		gcal.AddReminder(gcal_event, 60)
		
	

def make_dates(full_list):
	""" Parse out all dates since some months
		 	could have two. I think I could make this into a 1 liner instead of seperate function
	"""
	l = []
	for i in full_list:
		if len(i) > 18:
			p = re.compile(r'((?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)\s*\d{1,2})\s*')
			[l.append(time.mktime(time.strptime(d + ' ' + i[-6:]+' 08:00', '%A   %d %b %y %H:%M'))) for d in filter(None, p.split(i[:-6]))]
		else:
			l.append(time.mktime(time.strptime(i+' 08:00', '%A   %d %b %y %H:%M')))
			
	return l
		
if __name__ == '__main__':
	main()

