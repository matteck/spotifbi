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

	def __init__(self, prog_name):
		self.tracks = []
		self.playlist_tracks = set()
		session = spotify.Session()
		session.login(username, password)
		while session.connection.state is not spotify.ConnectionState.LOGGED_IN:
			session.process_events()
		self.session = session
		self.prog_name = prog_name

	def get_prog(self, prog_base_url="http://airnet.org.au/program/javascriptEmbed.php?station=3&view&rpid=", date_string=None):
		self.prog_html = requests.get(prog_base_url + self.prog_name).text
		if date_string:
			self.date_string = date_string
		else:
			match = re.search(r'<td class="trackShareUrl" style="display:none">http://2FBI.radiopages.info/\?an_page=(\d\d\d\d-\d\d-\d\d)__', self.prog_html)
			self.date_string = match.group(1)

	def make_playlist(self):
		self.list_name = "FBI-3 " + self.prog_name.replace('-', ' ').title() + " " + self.date_string
		container = self.session.playlist_container
		container.load()
		while not container.is_loaded:
			pass
		index = 0
		folder_index = 0
		for item in container:
			index += 1
			try:
				item.load()
				while item.is_loaded == False:
					pass
	 			if item.name == self.list_name:
					self.playlist = item
					return
			except AttributeError:
				if item.name == "FBI" and item.type == spotify.PlaylistType.START_FOLDER:
					folder_index = index
		self.playlist = container.add_new_playlist(self.list_name, folder_index)

	def get_playlist_tracks(self):
		self.playlist.load()
		while self.playlist.is_loaded == False:
			pass
		print "Existing tracks:"
		for t in self.playlist.tracks:
			print t.name

	def add_tracks(self):
		playlist_tracks = set()
		pattern = re.compile(r'<a href="http://2FBI.radiopages.info/\?an_page=%s__[^"]+" rel="nofollow">([^<]+?) - ([^<]+)</a>' % (self.date_string))
		for (artist, track) in re.findall(pattern, self.prog_html):
			orig_track = track
			orig_artist = artist
			track = re.sub(' (ft|featuring|feat|feat.|ft.)\s*\w.*$', '', track)
			track = re.sub('\([^)]+\)', '', track)
			artist = re.sub('\([^)]+\)', '', artist)
			artist = re.sub(' (&|and|with)\s*\w.*$', '', artist)
			query = ("%s %s" % (artist,track)).rstrip()
			search = self.session.search(query=query, track_count=1)
			search.load()
			while not search.is_loaded:
				pass
			if search.tracks:
				self.tracks.append(search.tracks[0])
			else:
				print ("Nothing found for %s / %s [%s]" % (orig_artist, orig_track, query))
		self.playlist.load()
		while self.playlist.is_loaded == False:
			pass
		for t in self.playlist.tracks:
			playlist_tracks.add(t)
		for t in self.tracks:
			if t not in playlist_tracks:
				print "Adding ", t.name
				self.playlist.add_tracks([t])
			else:
				# print "Skipping ", t.name
				pass
		while self.playlist.has_pending_changes:
			pass

p = program('utility-fog')
p.get_prog()
p.make_playlist()
p.get_playlist_tracks()
p.add_tracks()
p.get_playlist_tracks()
# print p.playlist
# print p.playlist.name
# print p.playlist.tracks
# for t in p.playlist.tracks:
# 	print t.name

