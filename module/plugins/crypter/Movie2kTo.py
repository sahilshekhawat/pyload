#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter
from collections import defaultdict

class Movie2kTo(Crypter):
	__name__ = 'Movie2kTo'
	__type__ = 'container'
	__pattern__ = r'http://(?:www\.)?movie2k\.to/(.*)\.html'
	__version__ = '0.3'
	__config__ = [('accepted_hosters', 'str', 'List of accepted hosters', 'Xvidstage, '),
				('whole_season', 'bool', 'Download whole season', 'False'),
				('everything', 'bool', 'Download everything', 'False'),
				('firstN', 'int', 'Download the first N files for each episode. The first file is probably all you will need.', '1')]
	__description__ = """Movie2k.to Container Plugin"""
	__author_name__ = ('4Christopher')
	__author_mail__ = ('4Christopher@gmx.de')
	BASE_URL_PATTERN = r'http://(?:www\.)?movie2k\.to/'
	TVSHOW_URL_PATH_PATTERN = r'tvshows-(?P<id>\d+?)-(?P<name>.+)'
	FILM_URL_PATH_PATTERN = r'(?P<name>.+?)-(?:online-film|watch-movie)-(?P<id>\d+)'
	SEASON_PATTERN = r'<div id="episodediv(\d+?)" style="display:(inline|none)">(.*?)</div>'
	EP_PATTERN = r'<option value="(.+?)"( selected)?>Episode\s*?(\d+?)</option>'
	BASE_URL = 'http://www.movie2k.to'

	def decrypt(self, pyfile):
		self.package = pyfile.package()
		self.folder = self.package.folder
		whole_season = self.getConfig('whole_season')
		everything = self.getConfig('everything')
		self.getInfo(pyfile.url)

		if (whole_season or everything) and self.format == 'tvshow':
			self.logDebug('Downloading the whole season')
			for season, season_sel, html in re.findall(self.SEASON_PATTERN, self.html, re.DOTALL | re.I):
				if (season_sel == 'inline') or everything:
					season_links = []
					for url_path, ep_sel, ep in re.findall(self.EP_PATTERN, html, re.I):
						season_name = self.name_tvshow(season, ep)
						self.logDebug('%s: %s' % (season_name, url_path))
						if ep_sel and (season_sel == 'inline'):
							self.logDebug('%s selected (in the start URL: %s)' % (season_name, pyfile.url))
							season_links += self.getInfoAndLinks('%s/%s' % (self.BASE_URL, url_path))
						elif (whole_season and (season_sel == 'inline')) or everything:
							season_links += self.getInfoAndLinks('%s/%s' % (self.BASE_URL, url_path))

					self.logDebug(season_links)
					self.packages.append(('%s: Season %s' % (self.name, season), season_links, 'Season %s' % season))
		else:
			self.packages.append((self.package.name, self.getLinks(), self.package.folder))

	def tvshow_number(self, number):
		if int(number) < 10:
			return '0%s' % number
		else:
			return number

	def name_tvshow(self, season, ep):
		return '%s S%sE%s' % (self.name, self.tvshow_number(season), self.tvshow_number(ep))

	def getInfo(self, url):
		self.html = self.load(url)
		self.url_path = re.match(self.__pattern__, url).group(1)
		self.format = pattern_re = None
		if re.match(r'tvshows', self.url_path):
			self.format = 'tvshow'
			pattern_re = re.search(self.TVSHOW_URL_PATH_PATTERN, self.url_path)
		elif re.search(self.FILM_URL_PATH_PATTERN, self.url_path):
			self.format = 'film'
			pattern_re = re.search(self.FILM_URL_PATH_PATTERN, self.url_path)


		self.name = pattern_re.group('name')
		self.id = pattern_re.group('id')
		self.logDebug('URL Path: %s (ID: %s, Name: %s, Format: %s)'
			% (self.url_path, self.id, self.name, self.format))

	def getInfoAndLinks(self, url):
		self.getInfo(url)
		return self.getLinks()

	## This function returns the links for one episode as list
	def getLinks(self):
		accepted_hosters = re.findall(r'\b(\w+?)\b', self.getConfig('accepted_hosters'))
		firstN = self.getConfig('firstN')
		links = []
		## h_id: hoster_id of a possible hoster
		re_hoster_id_js = re.compile(r'links\[(\d+?)\].+&nbsp;(.+?)</a>')
		re_hoster_id_html = re.compile(r'</td><td.*?<a href=".*?(\d{7}).*?".+?&nbsp;(.+?)</a>')
		## I assume that the ID is 7 digits longs
		if re_hoster_id_js.search(self.html):
			re_hoster_id = re_hoster_id_js
			self.logDebug('Assuming that the ID can be found in a JavaScript section.')
		elif re_hoster_id_html.search(self.html):
			re_hoster_id = re_hoster_id_html
			self.logDebug('Assuming that the ID can be found in a HTML section.')
		count = defaultdict(int)
		for h_id, hoster in re_hoster_id.findall(self.html):
			# self.logDebug('Hoster %s' % hoster)
			if hoster in accepted_hosters:
				# self.logDebug('Accepted %s' % hoster)
				count[hoster] += 1
				if count[hoster] <= firstN:
					if h_id != self.id:
						self.html = self.load('%s/tvshows-%s-%s.html' % (self.BASE_URL, h_id, self.name))
					else:
						self.logDebug('This is already the right ID')
					try:
						url = re.search(r'<a target="_blank" href="(http://.*?)"', self.html).group(1)
						self.logDebug('id: %s, %s: %s' % (h_id, hoster, url))
						links.append(url)
					except:
						self.logDebug('Failed to find the URL')

		self.logDebug(links)
		return links