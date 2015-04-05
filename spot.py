#!/usr/bin/python

import requests
import re
import json
import spotify
import sys

username='marmotmaster'
password='Qs4#^WTn^S'
folder_name = 'FBI'
prefix = ""

if len(sys.argv) < 2:
	sys.argv = ['','sunday-lunch']
prog_name = sys.argv[1]

# Get dates of recent shows
html = requests.post('http://ondemand.fbiradio.com/fbipulse/pulse.php', data = {'show': prog_name}).text
pattern = re.compile(r'Program for (\d\d\d\d-\d\d-\d\d)')
dates = [''] + re.findall(pattern, html)


session = spotify.Session()
session.login(username, password)
while session.connection.state is not spotify.ConnectionState.LOGGED_IN:
	session.process_events()

# Get folder index to add new playlists, add at end if there is none
folder_index = 0
container = session.playlist_container
container.load()
while not container.is_loaded:
	pass
for item in container:
	folder_index += 1
	try:
		if item.name == folder_name and item.type == spotify.PlaylistType.START_FOLDER:
			break
	except AttributeError:
		# It's a playlist
		pass

for date_string in dates:

	# Get episode html (site will send latest if date_string is empty)
	prog_url = 'http://airnet.org.au/program/javascriptEmbed.php?station=3&view=272&rpid=%s&jspage=%s' % (prog_name, date_string)
	prog_html = requests.get(prog_url).text

	if not date_string:
		match = re.search(r'<a href="http://fbiradio.com/programs/%s/(\d\d\d\d-\d\d-\d\d)/[^"]+"' % (prog_name), prog_html)
		try:
			date_string = match.group(1)
		except AttributeError:
			# HTML doesn't match pattern, give up on this episode
			continue

	# Get existing playlist or create new one
	existing_tracks = set()
	missing = []
	list_name = ((prefix + " ") if prefix else "") + prog_name.replace('-', ' ').title() + " " + date_string
	container = session.playlist_container
	container.load()
	while not container.is_loaded:
		pass
	playlist = None
	for item in container:
		try:
			item.load()
			while item.is_loaded == False:
				pass
			if item.name == list_name:
				playlist = item
				playlist.set_in_ram(True)
				while not playlist.is_in_ram:
					pass
				for t in playlist.tracks:
					existing_tracks.add(t)
				break
		except AttributeError:
			# it's a folder
			pass
	if playlist == None:
		playlist = container.add_new_playlist(list_name, folder_index)

	# Get song details
	pattern = re.compile(r'<a href="http://fbiradio.com/programs/%s/%s/[^"]+" rel="nofollow">([^-<]+) - ([^<]+)</a>' % (prog_name, date_string))
	for (artist, track) in re.findall(pattern, prog_html):
		orig_track = track
		orig_artist = artist
		# Get rid of multi-artist descriptions in FBI that confuse spotify
		track = re.sub(' (ft|featuring|feat|feat.|ft.)\s*\w.*$', '', track)
		track = re.sub('\([^)]+\)', '', track)
		artist = re.sub('\([^)]+\)', '', artist)
		artist = re.sub(' (&|and|with)\s*\w.*$', '', artist)
		artist = re.sub(r'[\'"]', '', artist)
		track = re.sub(r'[\'"]', '', track)
		# NB: advanced search doesn't seem to work via API
		query = ("%s %s" % (artist,track)).rstrip()
		search = session.search(query=query, track_count=1)
		try:
			search.load()
			while not search.is_loaded:
				pass
			if search.tracks:
				track = search.tracks[0]
				if track not in existing_tracks:
					playlist.add_tracks(track)
			else:
				missing.append((orig_artist, orig_track, query, "not found"))
		except spotify.error.Timeout:
			missing.append((orig_artist, orig_track, query, "timeout"))
			if session.connection.state is not spotify.ConnectionState.LOGGED_IN:
				session.login(username, password)
				while session.connection.state is not spotify.ConnectionState.LOGGED_IN:
					session.process_events()

	# call process_events or changes to playlist may not get saved
	session.process_events()

	if missing:
		print list_name
		for m in missing:
			print "%s - %s [%s]" % (m[0], m[1], m[3])
		print

session.logout()



