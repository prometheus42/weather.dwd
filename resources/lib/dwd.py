
import os
import csv
from datetime import datetime

import requests

import xbmcvfs
import xbmcaddon

from resources.lib.utils import log


ADDON = xbmcaddon.Addon()

TIMEOUT = 10
API_URL = 'https://app-prod-ws.warnwetter.de/v30/stationOverviewExtended?stationIds={station}'


class DWDException(Exception):
    pass


def fetch_weather_data(no):
    """
    Fetches weather data from DWD for a given weather station identified by the
    location no.
    """
    log('Fetching weather info...')
    station_ids = get_station_ids()
    if not station_ids:
        raise DWDException('No weather station was selected.')
    r = requests.get(API_URL.format(
        station=','.join(station_ids)), timeout=TIMEOUT)
    weather_data = r.json()
    return weather_data[station_ids[no-1]]


def find_station_by_name(station_name):
    """
    Get the list of weather stations and filter for a given station name.
    """
    station_list = load_station_list()
    # TODO: Check whether to use SequenceMatcher from difflib or other algorithms like Levenshtein Distance.
    query = station_name.casefold().replace(
        'ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
    station_list = [
        s for s in station_list if query in s[1].casefold()]
    return check_station_list(station_list)


def check_station_list(station_list):
    """
    The official station list of the DWD [1] contains some stations for which
    no weather data is provided. So we check a station list by requesting data
    for each entry and reject it if the response is empty.

    [1] https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/mosmix_stationskatalog.cfg
    """
    new_station_list = []
    for s in station_list:
        r = requests.get(API_URL.format(station=s[0]), timeout=10)
        if r.json():
            new_station_list.append(s)
    return new_station_list


def load_station_list():
    """
    Load list of weather stations from a CSV file and return it.
    """
    filename = xbmcvfs.translatePath(os.path.join(
        ADDON.getAddonInfo('path'), 'resources', 'station_list.csv'))
    station_list = []
    with open(filename, newline='', encoding='utf8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            # TODO: Find a better station list without mojibake (65533)!
            station_name = row['NAME'].replace(chr(65533), '')
            station_list.append(
                (row['ID'], station_name.title(), row['LAT'], row['LON']))
    return station_list


def get_station_ids():
    """
    Get all station IDs from the Kodi settings.
    """
    station_ids = [ADDON.getSetting('Location1ID'), ADDON.getSetting(
        'Location2ID'), ADDON.getSetting('Location3ID'), ADDON.getSetting('Location4ID')]
    station_ids = list(filter(None, station_ids))
    log(f'Stations for which to fetch data: {station_ids}')
    return station_ids


def get_station_names():
    """
    Get all station names from the Kodi settings.
    """
    station_names = [ADDON.getSetting('Location1Name'), ADDON.getSetting(
        'Location2Name'), ADDON.getSetting('Location3Name'), ADDON.getSetting('Location4Name')]
    station_names = list(filter(None, station_names))
    log(f'Getting station names: {station_names}')
    return station_names


def get_coordinates_for_station(station_name):
    """
    Gets the coordinates for a weather station from the station list of the DWD.
    """
    l = load_station_list()
    for s in l:
        if station_name == s[1]:
            lat = s[2]
            lon = s[3]
            return (lat, lon)


def calc_time(timestamp):
    """
    Format the timestamp from DWD in the valid format for Kodi.
    """
    try:
        timestamp = int(timestamp) / 1000
        dt = datetime.fromtimestamp(timestamp)
        # TODO: Check whether the date format is correct.
        # iso_fmt = '%Y-%m-%dT%H:%M:%S%z'
        return str(dt)
    except ValueError:
        return ''


def div10(text):
    """
    Convert most values from DWD by dividing by 10 and returning it as a integer.
    """
    try:
        return int(text) / 10.
    except ValueError:
        return 0.0


def get_first_valid_value(value_list):
    """
    Get the first valid value in the list provided by DWD. Sometimes a value is
    not available and the number 32767 is delivered instead. In these cases the
    next valid number is returned.
    """
    for v in value_list:
        if v != 32767:
            return v
