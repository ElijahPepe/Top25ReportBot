import pywikibot
import sys
import calendar
import requests
import locale
from datetime import datetime
from datetime import date
from datetime import timedelta

locale.setlocale(locale.LC_ALL, 'en_US')

site = pywikibot.Site('en', 'wikipedia')

today = date.today()
sunday = today - timedelta((today.weekday() + 1) % 7)
saturday = today - timedelta((today.weekday() + 1) % 7 - 6)

title = 'Wikipedia:Top 25 Report/'

headers = {'User-Agent': 'Top25ReportBot/0.0 (business@elijahpepe.com)'}

def get_title(sunday, saturday):
	if sunday.month == 12 and saturday.month == 1:
		title = 'December ' + str(sunday.day) + ', ' + str(datetime.now().year - 1) + ' to January ' + str(saturday.day) + ', ' + str(datetime.now().year)
	elif sunday.day > saturday.day:
		title = calendar.month_name[(sunday.month - 1) % 12] + ' ' + str(sunday.day) + ' to ' + calendar.month_name[sunday.month] + ' ' + str(saturday.day) + ', ' + str(datetime.now().year)
	else:
		title = calendar.month_name[sunday.month] + ' ' + str(sunday.day) + ' to ' + str(saturday.day) + ', ' + str(datetime.now().year)
	return title

def get_article_quality(title):
	r = requests.get('https://pageviews.wmcloud.org/pageviews/api.php?pages=' + title + '&project=en.wikipedia.org&start=2015-01-01&end=2015-01-01&totals=true', headers=headers)
	assessment = r.json()['pages'][title.replace('_', ' ')]['assessment']

	if type(assessment) == type(None):
		return 'None'
	else:
		return r.json()['pages'][title.replace('_', ' ')]['assessment']

page = pywikibot.Page(site, title + get_title(sunday, saturday))
if len(page.text) != 0:
	sys.exit('Page exists, not running.')

date = sunday
data = []
simple_data = []
for i in range(7):
	r = requests.get('https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/' + str(date.year) + '/' + str(date.month).zfill(2) + '/' + str(date.day).zfill(2), headers=headers)

	page_data = r.json()
	for entry in page_data['items'][0]['articles']:
		if entry['article'] not in simple_data:
			simple_data.append(entry['article'])
			data.append(entry)
		else:
			for line in data:
				if line['article'] == entry['article']:
					line['views'] = line['views'] + entry['views']
	date += timedelta(days=1)

fixed_data = []
blacklist = ['Main_Page', 'Special:Search', 'Cleopatra', 'YouTube', 'Microsoft_Office', 'Wikipedia:Featured_pictures', 'Bible']

for line in data:
	if 'File:' in line['article']:
		print(line['article'])
	elif line['article'] in blacklist:
		print(line['article'])
	else:
		fixed_data.append(line)

fixed_data = sorted(fixed_data, key=lambda d: d['views'], reverse=True)

for line in fixed_data[:50]:
	if sunday.month == 12 and saturday.month == 1:
		time_range = str(datetime.now().year - 1) + '12' + str(sunday.day).zfill(2) + '00/' + str(datetime.now().year - 1) + '01' + str(saturday.day).zfill(2) + '00'
	elif sunday.day > saturday.day:
		time_range = str(datetime.now().year) + str((datetime.now().month - 1) % 12).zfill(2) + str(sunday.day).zfill(2) + '00/' + str(datetime.now().year) + str(datetime.now().month).zfill(2) + str(saturday.day).zfill(2) + '00'
	else:
		time_range = str(datetime.now().year) + str(datetime.now().month).zfill(2) + str(sunday.day).zfill(2) + '00/' + str(datetime.now().year) + str(datetime.now().month).zfill(2) + str(saturday.day).zfill(2) + '00'
	r = requests.get('https://en.wikipedia.org/w/api.php?action=query&format=json&formatversion=2&prop=redirects&rdprop=title|fragment&rdlimit=500&titles=' + line['article'], headers=headers)

	try:
		for page in r.json()['query']['pages'][0]['redirects']:
			r = requests.get('https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/' + page['title'] + '/daily/' + time_range, headers=headers)

			for pageviews in r.json()['items']:
				line['views'] += pageviews['views']
	except:
		print('Failed to get data for ' + page['title'])

fixed_data = sorted(fixed_data, key=lambda d: d['views'], reverse=True)

for line in fixed_data[:50]:
	r = requests.get('https://en.wikipedia.org/w/api.php?titles=' + line['article'] + '&redirects&action=query&format=json', headers=headers)

	try:
		for second_line in fixed_data:
			if second_line['article'].replace('_', ' ') == r.json()['query']['redirects'][0]['to']:
				fixed_data.remove(line)
	except:
		print('No redirect possible')

fixed_data = sorted(fixed_data, key=lambda d: d['views'], reverse=True)

this_week = title + get_title(sunday, saturday)

last_week = today - timedelta(days=7)
last_sunday = last_week - timedelta((last_week.weekday() + 1) % 7)
last_saturday = last_week - timedelta((last_week.weekday() + 1) % 7 - 6)

wikitext = '''{{Short description|Weekly report of the most popular Wikipedia articles}}
{{Wikipedia:Top 25 Report/Template:Header}}
__NOTOC__
<div style="height:10px;clear:both;"></div>
{{Humor}}
<onlyinclude>

==Most Popular Wikipedia Articles of the Week (''' + get_title(sunday, saturday) + ') ==' + '''
''Prepared with commentary by''

{{clickable button 2|Wikipedia:Top 25 Report/''' + get_title(last_sunday, last_saturday) + '|⭠ Last week\'s report}}\n' + '''
::{| class="wikitable"
|-
! Rank
! Article
! Class
! Views
! Image
! Notes/about'''

for i, line in enumerate(fixed_data[:25]):
	wikitext_line = '''
|-
| ''' + str(i + 1) + '''
| [[''' + line['article'].replace('_', ' ') + ''']]
| {{icon|''' + get_article_quality(line['article']) + '''}}
| ''' + locale.format("%d", line['views'], grouping=True) + '''
| 
| '''
	wikitext += wikitext_line

wikitext += '''
|-
|}

{{notelist}}
</onlyinclude>

=== Exclusions ===

* This list excludes the Wikipedia main page, non-article pages (such as [[Wikipedia:Red link|redlinks]]), and anomalous entries (such as DDoS attacks or likely automated views). Since mobile view data became available to the Report in October 2014, we exclude articles that have almost no mobile views (5–6% or less) or almost all mobile views (94–95% or more) because they are very likely to be automated views based on our experience and research of the issue.  Please feel free to discuss any removal on the talk page if you wish.'''

page.text = wikitext
page.save('Updating the Top 25 Report for ' + get_title(sunday, saturday))

page = pywikibot.Page(site, 'User talk:Top25ReportBot')

wikitext = '''

==Most Popular Wikipedia Articles of the Week (''' + get_title(sunday, saturday) + ') ==''' + '''
::{| class="wikitable"
|-
! Rank
! Article
! Class
! Views
! Image
! Notes/about'''

for i, line in enumerate(fixed_data[:50]):
	wikitext_line = '''
|-
| ''' + str(i + 1) + '''
| [[''' + line['article'].replace('_', ' ') + ''']]
| {{icon|''' + get_article_quality(line['article']) + '''}}
| ''' + locale.format("%d", line['views'], grouping=True) + '''
| 
| '''
	wikitext += wikitext_line

wikitext += '''
|-
|}'''

page.text += wikitext
page.save(get_title(sunday, saturday))

sys.exit('Finished!')