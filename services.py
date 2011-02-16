#
# Encapsulated 3rd party web services here.
#

try:
  from xml.etree import ElementTree # for Python 2.5 users
except ImportError:
  from elementtree import ElementTree
import gdata.calendar.service
import gdata.service
import atom.service
import gdata.calendar
import atom
import getopt
import sys
import string
import time

class GCalService(object):
	"""
	Encapsulates the Google Calendar Service integration.
	Taken from the Google Calendar Python library sample.
	"""
	
	def __init__(self, username, password, default_source):
		self.calendar_service = gdata.calendar.service.CalendarService()
		self.calendar_service.email = username
		self.calendar_service.password = password
		self.calendar_service.source = default_source
		self.calendar_service.ProgrammaticLogin()

	def create_calendar(self, title, description, location, time_zone):
		
		print 'Creating calendar %s' % title
				
		# Create the calendar
		calendar = gdata.calendar.CalendarListEntry()
		calendar.title = atom.Title(text=title)
		calendar.summary = atom.Summary(text=description)
		calendar.timezone = gdata.calendar.Timezone(value=time_zone)
		calendar.hidden = gdata.calendar.Hidden(value='false')
		calendar.where = gdata.calendar.Where(value_string=location)
		calendar.selected = gdata.calendar.Selected(value='true')

		#calendar.color = gdata.calendar.Color(value='#2952A3')
		
		new_calendar = self.calendar_service.InsertCalendar(new_calendar=calendar)
		
		return new_calendar
		
	def delete_calendar(self, edit_link):
		""" Deleting specified calendar. """
		#print 'Deleting calendar %s' % edit_link
		try:
			self.calendar_service.Delete(edit_link)
		except gdata.service.RequestError, msg:
			pass
			#if msg[0]['body'].startswith('Cannot remove primary calendar'):
				#print '\t%s' % msg[0]['body']
			#else:
				#print '\tUnexpected Error: %s' % msg[0]['body']


	def get_events(self, calendar_id='default'):
		""" Get events for specified calendar only """
		#print 'Getting events by user'
		query = gdata.calendar.service.CalendarEventQuery(calendar_id, 'private', 'full')
		query.start_min = '2010-06-01'
		query.start_max = '2010-06-01'
		query.alt = 'json-in-script'
		query.max_results = 9999
		query.singleevents = 'true'
		events =  self.calendar_service.CalendarQuery(query)
        
		return events        

	def get_event(self, uri):
		"""Get a google calendar event by its uri id."""
		event = self.calendar_service.GetCalendarEventEntry(uri)
		return event
		
	def create_event(self, 
		title, 
		content,
		where,
		start_time, 
		end_time=None, 
		all_day='false',
		notify='true', 
		):	
		""" Create calendar event. """
		
		event = gdata.calendar.CalendarEventEntry()
		event.title = atom.Title(text=title)
		event.content = atom.Content(text=content)
		event.where.append(gdata.calendar.Where(value_string=where))

		if start_time is None:
		  # Use current time for the start_time and have the event last 15 min
		  start_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
		  end_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(time.time() + 900))
		else:
			s = start_time
			start_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(s))
			end_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(s + 900) )
		  
		event.when.append(gdata.calendar.When(start_time=start_time, end_time=end_time))
			
		# Turn on notifications
		notification = gdata.calendar.SendEventNotifications(value=notify)
		event.send_event_notifications = notification
		
		print start_time
		print end_time
		uri = '/calendar/feeds/default/private/full'
		new_event = ''
		new_event = self.calendar_service.InsertEvent(event, uri)
		
		print 'New single event inserted: %s' % (new_event.id.text,)
		print '\tEvent edit URL: %s' % (new_event.GetEditLink().href,)
		print '\tEvent HTML URL: %s' % (new_event.GetHtmlLink().href,)
		
		return new_event
		
		
	def update_event(self, event_uri, new_title, notify='true'):
		""" Updates an existing event. """
		#print 'Update event'
		event = self.get_event(event_uri)
		
		previous_title = event.title.text
		event.title.text = new_title
		
		# Notify attendees that the event has changed
		notification = gdata.calendar.SendEventNotifications(value=notify)
		event.send_event_notifications = notification

		#print 'Updating title of event from:\'%s\' to:\'%s\'' % (previous_title, event.title.text,) 
		return self.calendar_service.UpdateEvent(event.GetEditLink().href, event)
		
	def delete_event(self, event_edit_link):
		""" Delete an event by edit link id. """
		self.calendar_service.DeleteEvent(event_edit_link)		
		
	def invite_people(self, event_uri, name, email, notifyByMail='true'):
		""" Invite additional people to an event."""
		event = self.get_event(event_uri)
		event.who.append(gdata.calendar.Who(name=name, email=email))
		notification = gdata.calendar.SendEventNotifications(value=notifyByMail)
		event.send_event_notifications = notification
		self.calendar_service.UpdateEvent(event.GetEditLink().href, event)
		
		return event

	def get_attendees(self, event_uri):
 		""" getAttendees: get all the Participants in a specific Event 
	    Returns:
	            who: List of who associated to the Event. See Google Api.
		"""
		who = None
		event = self.get_event(event_uri)
		return event.who

	def AddReminder(self, event, minutes=15):
	  for a_when in event.when:
	    if len(a_when.reminder) > 0:
	      a_when.reminder[0].minutes = minutes
	    else:
	      a_when.reminder.append(gdata.calendar.Reminder(minutes=minutes))

	  print 'Adding %d minute reminder to event' % (minutes,)
	  return self.calendar_service.UpdateEvent(event.GetEditLink().href, event)