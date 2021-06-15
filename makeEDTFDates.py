#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# makeEDTFDates

import csv
import re
import requests
import shutil
from tempfile import NamedTemporaryFile

_FILES = [
    "letters"
]
_ONLYADD = False


def getISODate(datestring):
    ''' Try to detect/transform date strings to ISO dates using pdr webservice
        Dates-Tool (ISO-Date) - Dates Detection Tool
        https://pdrprod.bbaw.de/pdrws/dates?doc=api
    '''
    service_url = 'https://pdrprod.bbaw.de/pdrws/dates'
    service_params = {
        'text': prepareDate(datestring),
        'lang': 'de',
        'output': 'json'
    }
    r = session.get(service_url, params=service_params, verify=True)
    ret = []
    if r.ok:
        # sometimes non well formed json is returned
        try:
            js = r.json()
            if 'results' in js:
                for isodate in js['results']:
                    ret.append(isodate['isodate'])
        except Exception:
            ret = 'Error: ' + r.url
    else:
        ret = 'Error: ' + r.url
    return ret


def prepareDate(datestring):
    replacements = [
        (r'\[', ''),  # wont be interpreted by webservice
        (r'\]', ''),  # wont be interpreted by webservice
        (r'\?', ''),  # wont be interpreted by webservice
        (r'1\. Advent 1682', '29. November 1682'),
        (r'Spätsommer/Frühherbst 1684', 'nach Juli 1684 und vor Oktober 1684'),
        (r'Frühjahr/Frühsommer 1685', 'nach März 1685 und vor Juli 1685'),
        (r'Frühjahr', 'Frühling'),
        (r'vor dem oder am', 'vor'),
        (r'am oder nach dem', 'nach'),
        (r'dem ', ''),
        (r'Jahresende', 'Ende'),
        (r'Jahreshälfte', 'Hälfte'),
        (r'Erstes Drittel', 'Januar bis April'),
        (r'Zweites Drittel', 'Mai bis August'),
        (r'Letztes Drittel', 'September bis Dezember'),
        (r'erstes Drittel', 'Januar bis April'),
        (r'zweites Drittel', 'Mai bis August'),
        (r'letztes Drittel', 'September bis Dezember'),
        (r'erstes', '1.'),
        (r'Erstes', '1.'),
        (r'zweites', '2.'),
        (r'Zweites', '2.'),
        (r'Halbjahr', 'Hälfte'),
        (r'\(', ''),  # wont be interpreted by webservice
        (r'\)', ''),  # wont be interpreted by webservice
        (r'zweite Maihälfte', 'Mitte bis Ende Mai'),  # special case for Spener Vol.1 68-91 Letter 96
        (r'\s?(-|–)\s?', ' bis ')
    ]
    for repl in replacements:
        datestring = re.sub(repl[0], repl[1], datestring)

    datestring = re.sub(r'\s{2,}', ' ', datestring)  # normalize whitespace

    def normalizeWhitespaceInFullDate(matchobj):
        return str(matchobj.group(1)) + str(matchobj.group(2))
    datestring = re.sub(r'(\d\.)\s+(\d)', normalizeWhitespaceInFullDate, datestring)
    # the slash has many faces
    if "/" in datestring:
        # sometimes it makes a difference because the webservice we use does
        # not interpret well.
        end_of_year = re.search(r'Herbst\/Winter\]?\s(\d{4})', datestring)
        if end_of_year:
            datestring = 'Herbst ' + end_of_year.group(1)
        # Sometimes it is a year fallow a year or diffence or counting of conjunction words
        if not re.search(r'\d{4}\/\d{2}', datestring) and not re.search(r'und\/oder', datestring):
            # but most of the time is an or
            datestring = datestring.replace('/', ' oder ')

    if 'oder später' in datestring:
        datestring = 'nach ' + re.search('^(.*) oder später', datestring).group(1)
    elif 'oder früher' in datestring:
        datestring = 'vor ' + re.search('^(.*) oder früher', datestring).group(1)
    elif ' bis ' in datestring or ' oder ' in datestring or 'zwischen' in datestring:
        matches = []
        for match in re.findall(r'(Anfang |Mitte |Ende |\d{1,2}\. )?([A-Z]\w+ )?(\d{4})?',
                                datestring):
            if match != ('', '', ''):
                matches.append(list(map(str.strip, match)))
        # add year of second part to first part
        if matches[1][2] and not matches[0][2]:
            matches[0][2] = matches[1][2]
            # also add month if not given in first but in second part
            if matches[1][1] and not matches[0][1]:
                matches[0][1] = matches[1][1]
        # Remove empties
        fm = list(filter(None, matches[0]))
        to = list(filter(None, matches[1]))
        if ' bis ' in datestring:
            datestring = ' '.join(fm) + ' bis ' + ' '.join(to)
        elif 'zwischen' in datestring:
            datestring = 'zwischen ' + ' '.join(fm) + ' und ' + ' '.join(to)
        else:
            datestring = ' '.join(fm) + ' oder ' + ' '.join(to)

    # < Winter 1767/1768
    # > Ende Dezember 1767 bis Mitte März 1768
    wintermatch = re.search(r'Winter\s(\d{4})/(\d{4})', datestring)
    if wintermatch:
        datestring = 'Ende Dezember {} bis Mitte März {}'.format(
            wintermatch.group(1), wintermatch.group(2))
    print(datestring)
    return datestring


def getEDTF(datetext, datecollection, letter_key=None):
    print(datecollection)
    # TODO: check if datecollection is a collection and not a string, latter
    # means error from webservice
    # Add information about qualification of the date
    quality_fulldate = ''
    # qualification for approximate date
    if '?' not in datetext and '[' in datetext and ']' in datetext:
        quality_fulldate = '~'
    # qualification for uncertain date
    elif '?' in datetext and '[' not in datetext and ']' in datetext:
        quality_fulldate = '?'
    # qualification for uncertain and approcimate date
    elif '?' in datetext and '[' in datetext and ']' in datetext:
        quality_fulldate = '%'

    date = ''
    if len(datecollection) == 1:
        dates = datecollection[0]
        for key, isodate in dates.items():
            if key == 'when':
                date = isodate + quality_fulldate
#            elif key == 'notBefore' and len(dates.items()) > 1:
#                date = isodate + quality_fulldate + '..,'
            elif key == 'notBefore':
                date = isodate + '..'
#            elif key == 'notAfter' and len(dates.items()) > 1:
#                date += '..' + isodate + quality_fulldate + ''
            elif key == 'notAfter':
                date += '..' + isodate
            elif key == 'from':
                date = isodate + quality_fulldate + '/'
            elif key == 'to':
                date += '/' + isodate + quality_fulldate
            else:
                print('WARN: Unexpected date key found.')
    elif len(datecollection) == 2:
        # lowest from first, highest from last
        for key, isodate in datecollection[0].items():
            if key in ('when', 'notBefore', 'from'):
                if ' und ' in prepareDate(datetext):
                    date = isodate + '..'
                else:
                    date = isodate + ','
        for key, isodate in datecollection[1].items():
            if key in ('when', 'notAfter', 'to'):
                date += isodate
    else:
        print('ERROR: Got more than 2 date occurences.')
    # Cleanup
    date = date.replace('//', '/')
    date = date.replace('....', '..')
    # mark sets
    if ',' in date or '..' in date:
        date = '[{}]'.format(date)
    return date


# Start session for pdr webservice
session = requests.Session()

for input_filename in _FILES:
    filename = input_filename + '.csv'
    tempfile = NamedTemporaryFile(mode='w+t', delete=False)

    with open(filename, 'r') as csvfile, tempfile:
        dictreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        dictwriter = csv.DictWriter(tempfile,
                                    fieldnames=dictreader.fieldnames,
                                    delimiter=',',
                                    quoting=csv.QUOTE_ALL)
        dictwriter.writeheader()
        for row in dictreader:
            for type in ('senderDate', 'addresseeDate'):
                if type + 'Text' in row and type in row and row[type + 'Text'] and (not row[type] or not _ONLYADD):
                    row[type] = getEDTF(
                        row[type + 'Text'],
                        getISODate(row[type + 'Text']),
                        row['key'])
            dictwriter.writerow(row)

    shutil.move(tempfile.name, filename)


# Close webservice session
session.close()
