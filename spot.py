#!/usr/bin/python

import requests
import re
import json
import spotify
import threading
import sys

username='marmotmaster'
password='Qs4#^WTn^S'


class program:

	def __init__(self, prog, folder):
		self.tracks = []
		self.existing_tracks = set()
		session = spotify.Session()
		session.login(username, password)
		while session.connection.state is not spotify.ConnectionState.LOGGED_IN:
			session.process_events()
		self.session = session
		self.prog_name = prog
		self.folder_name = folder
		self.playlist = None

	def get_prog(self, date_string=''):
		missing = []
		self.tracks = []
		self.existing_tracks = set()
		# Calling with empty date string returns most recent episode
		prog_url = 'http://airnet.org.au/program/javascriptEmbed.php?station=3&view=272&rpid=%s&jspage=%s' % (self.prog_name, date_string)  
		self.prog_html = requests.get(prog_url).text
		if date_string:
			self.date_string = date_string
		else:
			match = re.search(r'<a href="http://fbiradio.com/programs/%s/(\d\d\d\d-\d\d-\d\d)/[^"]+" rel="nofollow">' % (self.prog_name), self.prog_html)
			self.date_string = match.group(1)
		pattern = re.compile(r'<a href="http://fbiradio.com/programs/%s/%s/[^"]+" rel="nofollow">([^-<]+) - ([^<]+)</a>' % (self.prog_name, self.date_string))
		for (artist, track) in re.findall(pattern, self.prog_html):
			orig_track = track
			orig_artist = artist
			# Get rid of multi-artist descriptions in FBI that confuse spotify
			track = re.sub(' (ft|featuring|feat|feat.|ft.)\s*\w.*$', '', track)
			track = re.sub('\([^)]+\)', '', track)
			artist = re.sub('\([^)]+\)', '', artist)
			artist = re.sub(' (&|and|with)\s*\w.*$', '', artist)
			# NB: advanced search doesn't seem to work via API
			query = ("%s %s" % (artist,track)).rstrip()
			search = self.session.search(query=query, track_count=1)
			search.load()
			while not search.is_loaded:
				pass
			if search.tracks:
				self.tracks.append(search.tracks[0])
			else:
				missing.append((orig_artist, orig_track, query))
		return missing

	def get_playlist(self, prefix = ""):
		self.list_name = ((prefix + " ") if prefix else "") + self.prog_name.replace('-', ' ').title() + " " + self.date_string
		container = self.session.playlist_container
		container.load()
		while not container.is_loaded:
			pass
		index_count = 0
		new_index = 0
		for item in container:
			index_count += 1
			try:
				item.load()
				while item.is_loaded == False:
					pass
	 			if item.name == self.list_name:
	 				item.set_in_ram(True)
	 				while not item.is_in_ram:
	 					pass
					for t in item.tracks:
						self.existing_tracks.add(t)
					self.playlist = item
					return
			except AttributeError:
				if item.name == self.folder_name and item.type == spotify.PlaylistType.START_FOLDER:
					new_index = index_count
		self.playlist = container.add_new_playlist(self.list_name, new_index)

	def get_dates(self):
		html = requests.post('http://ondemand.fbiradio.com/fbipulse/pulse.php', data = {'show': self.prog_name}).text
		pattern = re.compile(r'Program for (\d\d\d\d-\d\d-\d\d)')
		self.dates = re.findall(pattern, html)
		return self.dates

	def add_tracks(self):
		for t in self.tracks:
			if t not in self.existing_tracks:
				self.playlist.add_tracks([t])
		self.session.process_events()

p = program('loose-joints', folder="FBI")
p.get_prog('2015-03-08')
p.get_playlist()
p.add_tracks()
p.session.logout()
p.session.process_events()
