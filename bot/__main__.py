import pywikibot
import sys
import calendar
import requests
from datetime import datetime
from datetime import date
from datetime import timedelta

site = pywikibot.Site('en', 'wikipedia')

today = date.today()
sunday = today - timedelta((today.weekday() + 1) % 7)
saturday = today - timedelta((today.weekday() + 1) % 7 - 6)

title = 'Wikipedia:Top 25 Report/'

def get_title(sunday, saturday):
	if sunday.month == 12 and saturday.month == 1:
		title = 'December ' + str(sunday.day) + ', ' + str(datetime.now().year - 1) + ' to January ' + str(saturday.day) + ', ' + str(datetime.now().year)
	elif sunday.day > saturday.day:
		title = calendar.month_name[(datetime.now().month - 1) % 12] + ' ' + str(sunday.day) + ' to ' + calendar.month_name[datetime.now().month] + ' ' + str(saturday.day) + ', ' + str(datetime.now().year)
	else:
		title = calendar.month_name[datetime.now().month] + ' ' + str(sunday.day) + ' to ' + str(saturday.day) + ', ' + str(datetime.now().year)
	return title

page = pywikibot.Page(site, title + get_title(sunday, saturday))
if len(page.text) != 0:
	sys.exit('Page exists, not running.')

date = sunday
data = []
simple_data = []
for i in range(6):
	date += timedelta(days=1)
	headers = {'User-Agent': 'Top25ReportBot/0.0 (business@elijahpepe.com)'}
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

fixed_data = []
blacklist = ['Main_Page', 'Special:Search', 'Cleopatra', 'YouTube', 'Microsoft_Office', 'Wikipedia:Featured_pictures', 'Bible']

for line in data:
	if line['article'] not in blacklist:
		fixed_data.append(line)

fixed_data = sorted(fixed_data, key=lambda d: d['views'], reverse=True)
del fixed_data[25:]

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

for i, line in enumerate(fixed_data):
	wikitext_line = '''
|-
| ''' + str(i + 1) + '''
| [[''' + line['article'].replace('_', ' ') + ''']]
| 
| ''' + str(line['views']) + '''
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

sys.exit('Finished!')