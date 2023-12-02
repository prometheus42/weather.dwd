
import os
import sys
import csv
import json
from datetime import datetime

import requests

import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon


WEATHER_WINDOW = xbmcgui.Window(12600)
WEATHER_ICON = xbmcvfs.translatePath('%s.png')

ADDON = xbmcaddon.Addon()
ADDONID = ADDON.getAddonInfo('id')
LANGUAGE = ADDON.getLocalizedString
DEBUG = ADDON.getSetting('Debug')

DATEFORMAT = xbmc.getRegion('dateshort')
TIMEFORMAT = xbmc.getRegion('meridiem')
TEMPUNIT = xbmc.getRegion('tempunit')
SPEEDUNIT = xbmc.getRegion('speedunit')
DATEFORMAT = xbmc.getRegion('dateshort')
TIMEFORMAT = xbmc.getRegion('meridiem')

MAXDAYS = 10
TIMEOUT = 10
API_URL = 'https://app-prod-ws.warnwetter.de/v30/stationOverviewExtended?stationIds={station}'

DWD_ICON_MAPPING = {
    1: 'Sonne',
    2: 'Sonne, leicht bewölkt',
    3: 'Sonne, bewölkt',
    4: 'Wolken',
    5: 'Nebel',
    6: 'Nebel, rutschgefahr',
    7: 'leichter Regen',
    8: 'Regen',
    9: 'starker Regen',
    10: 'leichter Regen, rutschgefahr',
    11: 'starker Regen, rutschgefahr',
    12: 'Regen, vereinzelt Schneefall',
    13: 'Regen, vermehrt Schneefall',
    14: 'leichter Schneefall',
    15: 'Schneefall',
    16: 'starker Schneefall',
    17: 'Wolken, (Hagel)',
    18: 'Sonne, leichter Regen',
    19: 'Sonne, starker Regen',
    20: 'Sonne, Regen, vereinzelter Schneefall',
    21: 'Sonne, Regen, vermehrter Schneefall',
    22: 'Sonne, vereinzelter Schneefall',
    23: 'Sonne, vermehrter Schneefall',
    24: 'Sonne, (Hagel)',
    25: 'Sonne, (staker Hagel)',
    26: 'Gewitter',
    27: 'Gewitter, Regen',
    28: 'Gewitter, starker Regen',
    29: 'Gewitter, (Hagel)',
    30: 'Gewitter, (starker Hagel)',
    31: '(Wind)',
    32767: 'not available'
}

DWD_TO_KODI_ICON_MAPPING = {
    1: 32,  # Sonne -> clear (day)
    # 1: 31, # Sonne -> clear (night)
    # TODO: Choose correct icon depending on time of the day!
    2: 44,  # Sonne, leicht bewölkt -> partly cloudy
    # 2: 29,  # Sonne, leicht bewölkt -> 'partly cloudy (night)'
    # 2: 30,  # Sonne, leicht bewölkt -> 'partly cloudy (day)'
    3: 28,  # Sonne, bewölkt -> 'mostly cloudy (day)',
    # 3: 27,  # Sonne, bewölkt -> 'mostly cloudy (night)',
    4: 26,  # : 'cloudy',
    5: 20,  # 'foggy',
    6: 20,  # Nebel und Rutschgefahr
    7: 9,  # Leichter Regen -> drizzle
    8: 11,  # Regen -> showers
    9: 12,  # Starker Regen -> showers
    10: 8,  # leichter Regen, Rutschgefahr -> freezing drizzle
    11: 10,  # Starker Regen, Rutschgefahr -> freezing rain
    12: 6,  # 'Regen, vereinzelt Schneefall' -> mixed rain and sleet
    13: 5,  # Regen, vermehrt Schneefall -> mixed rain and snow
    14: 14,  # 'leichter Schneefall -> light snow showers
    15: 16,  # Schneefall -> snow
    16: 41,  # starker Schneefall -> heavy snow
    17: 17,  # Wolken, (Hagel) -> hail
    18: 9,  # Sonne, leichter Regen -> drizzle
    19: 12,  # Sonne, starker Regen -> showers
    20: 6,  # Sonne, Regen, vereinzelter Schneefall -> mixed rain and sleet
    21: 5,  # Sonne, Regen, vermehrter Schneefall -> mixed rain and snow
    24: 17,  # Sonne, (Hagel) -> hail
    25: 17,  # Sonne, (staker Hagel) -> hail
    26: 4,  # Gewitter -> thunderstorm
    # 26: 37,  # Gewitter -> isolated thunderstorms
    27: 47,  # Gewitter, Regen -> isolated thundershowers
    28: 45,  # Gewitter, starker Regen -> thundershowers
    29: 35,  # Gewitter, (Hagel) -> mixed rain and hail
    30: 35,  # Gewitter, (starker Hagel) -> mixed rain and hail
    31: 24,  # Wind -> windy
    # 0:  'tornado',
    # 1:  'tropical storm',
    # 2:  'hurricane',
    # 3:  'severe thunderstorms',
    # 7:  'mixed snow and sleet',
    # 13: 'snow flurries',
    # 15: 'blowing snow',
    # 18: 'sleet',
    # 19: 'dust',
    # 21: 'haze',
    # 22: 'smoky',
    # 23: 'blustery',
    # 25: 'cold',
    # 33: 'fair (night)',
    # 34: 'fair (day)',
    # 36: 'hot',
    # 38: 'scattered thunderstorms',
    # 39: 'scattered thunderstorms',
    # 40: 'scattered showers',
    # 42: 'scattered snow showers',
    # 43: 'heavy snow',
    # 46: 'snow showers',
    # 47: 'isolated thundershowers',
    # "na": 'not available',
}


def get_wind_direction(deg):
    """
    Convert degrees on the compass to the correct label.

    Source: https://github.com/randallspicher/weather.noaa/blob/master/resources/lib/utils.py
    """
    if deg >= 349 or deg <= 11:
        return 71
    elif deg >= 12 and deg <= 33:
        return 72
    elif deg >= 34 and deg <= 56:
        return 73
    elif deg >= 57 and deg <= 78:
        return 74
    elif deg >= 79 and deg <= 101:
        return 75
    elif deg >= 102 and deg <= 123:
        return 76
    elif deg >= 124 and deg <= 146:
        return 77
    elif deg >= 147 and deg <= 168:
        return 78
    elif deg >= 169 and deg <= 191:
        return 79
    elif deg >= 192 and deg <= 213:
        return 80
    elif deg >= 214 and deg <= 236:
        return 81
    elif deg >= 237 and deg <= 258:
        return 82
    elif deg >= 259 and deg <= 281:
        return 83
    elif deg >= 282 and deg <= 303:
        return 84
    elif deg >= 304 and deg <= 326:
        return 85
    elif deg >= 327 and deg <= 348:
        return 86


def log(txt, level=xbmc.LOGDEBUG):
    """
    Log a message with a given log level.

    Source: https://github.com/randallspicher/weather.noaa/blob/master/resources/lib/utils.py
    """
    if True:
        message = f'{ADDONID}: {txt}'
        xbmc.log(msg=message, level=level)


def set_property(name, value):
    """Set a property on the weather window object."""
    WEATHER_WINDOW.setProperty(name, str(value))


def clear_property(name):
    """Clear all properties."""
    WEATHER_WINDOW.clearProperty(name)


def clear():
    """Reset all properties to default values."""
    set_property('Current.Condition', 'N/A')
    set_property('Current.Temperature', '0')
    set_property('Current.Wind', '0')
    set_property('Current.WindDirection', 'N/A')
    set_property('Current.Humidity', '0')
    set_property('Current.FeelsLike', '0')
    set_property('Current.UVIndex', '0')
    set_property('Current.DewPoint', '0')
    set_property('Current.OutlookIcon', 'na.png')
    set_property('Current.FanartCode', 'na')
    for i in range(0, MAXDAYS+1):
        set_property(f'Day{i}.Title', 'N/A')
        set_property(f'Day{i}.HighTemp', '0')
        set_property(f'Day{i}.LowTemp', '0')
        set_property(f'Day{i}.Outlook', 'N/A')
        set_property(f'Day{i}.OutlookIcon', 'na.png')
        set_property(f'Day{i}.FanartCode', 'na')


def div10(text):
    """
    Convert most values from DWD by dividing by 10 and returning it as a integer.
    """
    try:
        return int(text) / 10.
    except ValueError:
        return 0.0


def get_first_valid_value(value_list):
    for v in value_list:
        log(f'Probing value: {v}')
        if v != 32767:
            log(f'Returning value: {v}')
            return v


def calc_feels_like_temperature(T=10, V=25):
    """ 
    The formula to calculate the equivalent temperature related to the wind chill is:
        T(REF) = 13.12 + 0.6215 * T - 11.37 * V**0.16 + 0.3965 * T * V**0.16
    Or:
        T(REF): is the equivalent temperature in degrees Celsius
    V: is the wind speed in km/h measured at 10m height
    T: is the temperature of the air in degrees Celsius

    Source: http://zpag.tripod.com/Meteo/eolien.htm
    Source: https://forum.kodi.tv/showthread.php?tid=114637&pid=937168#pid937168
    """
    feels_like = T
    # Wind speeds of 4 mph or less, the wind chill temperature is the same as
    # the actual air temperature.
    if round((V + .0) / 1.609344) > 4:
        feels_like = (13.12 + (0.6215 * T) -
                      (11.37 * V**0.16) + (0.3965 * T * V**0.16))
    return str(round(feels_like))


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


def fetch_weather_data(no):
    """
    Fetches weather data from DWD for all given station IDs.
    """
    log('Fetching weather info...')
    station_ids = get_station_ids()
    r = requests.get(API_URL.format(
        station=','.join(station_ids)), timeout=TIMEOUT)
    weather_data = r.json()
    marshal_weather_data(weather_data[station_ids[no-1]])
    marshal_alert_data(weather_data[station_ids[no-1]])


def get_icon_for_weather(icon_no):
    """
    Evaluates the icon number from the DWD and chooses the fitting icon from Kodi.
    """
    condition_icon_no = DWD_TO_KODI_ICON_MAPPING[icon_no]
    condition_icon_file = xbmcvfs.translatePath(os.path.join(
        'resource://', 'resource.images.weathericons.default', f'{condition_icon_no}.png'))
    # condition_icon_file = xbmcvfs.translatePath(os.path.join(
    #    'special://home', 'addons', 'resource.images.weathericons.default', 'resources', f'{condition_icon_no}.png'))
    return condition_icon_file


def calc_time(timestamp):
    """
    Format the timestamp from DWD in the valid format for Kodi.
    """
    # value = "%d-%d-%dT%02d:%02d:00.088Z" % (d.year, d.month, d.day, h, m)
    try:
        timestamp = int(timestamp) / 1000
        dt = datetime.fromtimestamp(timestamp)
        return str(dt)
        # return dt.strftime("%y-%m-%dT%H:%M%:z")
    except ValueError:
        return ''


def marshal_weather_data(weather_data):
    """
    Set properties for a single weather station for today and the next days.

    List of all labels:
     - https://github.com/xbmc/repo-scripts/raw/jarvis/weather.openweathermap.extended/README.txt
     - https://github.com/vlmaksime/weather.gismeteo/raw/master/weather.gismeteo/README.txt
    """
    log(f'Marshal weather data for {weather_data["forecast1"]["stationId"]}')
    current_data = weather_data['forecast1']
    set_property('Current.Condition',
                 DWD_ICON_MAPPING[current_data['icon1h'][0]])
    set_property('Current.Temperature', div10(
        get_first_valid_value(current_data['temperature'])))
    set_property('Current.Humidity', div10(
        get_first_valid_value(current_data['humidity'])))
    set_property('Current.ChancePrecipitation',
                 current_data['precipitationProbablity'])  # precipitationTotal
    set_property('Current.DewPoint', div10(
        get_first_valid_value(current_data['dewPoint2m'])))
    set_property('Current.OutlookIcon', 'na.png')
    # TODO: Check why wind and precipitation data is mostly empty?!
    set_property('Current.WindGust', current_data['windGust'])
    set_property('Current.Pressure', div10(
        get_first_valid_value(current_data['surfacePressure'])))
    # set_property('Current.SeaLevel', 'true')  # pressure at sealevel
    set_property('Current.Precipitation',
                 get_first_valid_value(current_data['precipitationTotal']))
    sunrise = calc_time(weather_data['days'][0]['sunrise'])
    set_property('Today.Sunrise', sunrise)
    sunset = calc_time(weather_data['days'][0]['sunset'])
    set_property('Today.Sunset', sunset)
    set_property('Today.HighTemp', weather_data['days'][0]['temperatureMax'])
    set_property('Today.LowTemp', weather_data['days'][0]['temperatureMin'])
    set_property('Current.FanartCode', 'na')
    set_property('Current.ConditionIcon',
                 get_icon_for_weather(current_data['icon1h'][0]))
    # TODO: Check whether to include: sunshine, surfacePressure, isDay.
    # use wind information from first day (today!), because it is missing in the 'current' data
    set_property('Current.Wind', div10(weather_data['days'][0]['windSpeed']))
    wind_direction = div10(weather_data['days'][0]['windDirection'])
    set_property('Current.WindDirection', xbmc.getLocalizedString(
        get_wind_direction(wind_direction)))
    # calculate feels like temperature
    set_property('Current.FeelsLike',  calc_feels_like_temperature(
        div10(get_first_valid_value(current_data["temperature"])), div10(weather_data['days'][0]['windSpeed'])))
    #
    for no, day in enumerate(weather_data['days'][1:]):
        # Day0.xxx - Day6.xxx
        set_property(f'Day{no}.Title', day['dayDate'])
        set_property(f'Day{no}.HighTemp', day['temperatureMax'])
        set_property(f'Day{no}.LowTemp', day['temperatureMin'])
        set_property(f'Day{no}.Outlook', DWD_ICON_MAPPING[day['icon']])
        set_property(f'Day{no}.OutlookIcon', get_icon_for_weather(day['icon']))
        set_property(f'Day{no}.FanartCode', 'na')
        # fill extended labels
        set_property(f'Daily.{no}.Precipitation', day['precipitation'])
        set_property(f'Daily.{no}.WindDirection', xbmc.getLocalizedString(
            get_wind_direction(day['windDirection'])))
        set_property(f'Daily.{no}.WindSpeed', day['windSpeed'])
        # set_property('Daily.%i.TempDay' % (count+1), u'%s%s' % (FtoC(item['temperature']), TEMPUNIT))
        # set_property('Daily.%i.TempNight'	% (count+1), '')
        # set_property('Daily.%i.ShortOutlook'	% (count+1), item['shortForecast'])
        # set_property('Daily.%i.DetailedOutlook'	% (count+1), item['detailedForecast'])
        # set_property('Daily.%i.LongDay'		% (count+1), item['name'])
        # set_property('Daily.%i.ShortDay'	% (count+1), get_weekday(startstamp,'s')+" (d)")
    # TODO: Check more extended labels.
    # Hourly.1.xxx - Hourly.24.xxx, Daily.1.xxx - Daily.10.xxx


def marshal_alert_data(weather_data):
    """
    Marshal any weather alerts for a given location.
    """
    log(f'Marshal alert data for {weather_data["forecast1"]["stationId"]}')
    warning_data = weather_data['warnings']
    if warning_data:
        set_property('Alerts.IsFetched', 'true')
        for no, w in enumerate(warning_data, start=1):
            # warn_id = w["warnId"]
            # warn_type = w["type"]
            # level = w["level"]
            # "start": 1701010800000,
            # "end": 1701075600000,
            # "bn": false,
            # "descriptionText": "Es tritt leichter Frost zwischen -2 °C und -4 °C auf.",
            set_property(f'Alerts.{no}.headline', w['headline'])
            set_property(f'Alerts.{no}.instruction', w['instruction'])
            set_property(f'Alerts.{no}.description', w['description'])
            set_property(f'Alerts.{no}.event', w['event'])
            # set_property('Alerts.%i.status'		% (count+1), str(thisdata['status']))
            # set_property('Alerts.%i.messageType'	% (count+1), str(thisdata['messageType']))
            # set_property('Alerts.%i.category'	% (count+1), str(thisdata['category']))
            # set_property('Alerts.%i.severity'	% (count+1), str(thisdata['severity']))
            # set_property('Alerts.%i.certainty'	% (count+1), str(thisdata['certainty']))
            # set_property('Alerts.%i.urgency'	% (count+1), str(thisdata['urgency']))
            # set_property('Alerts.%i.response'	% (count+1), str(thisdata['response']))
    else:
        clear_property('Alerts.IsFetched')
        log('No current weather alerts.', level=xbmc.LOGDEBUG)


def check_station_list(station_list):
    new_station_list = []
    for s in station_list:
        r = requests.get(API_URL.format(station=s[0]), timeout=10)
        if r.json():
            new_station_list.append(s)
    return new_station_list


def load_station_list():
    filename = xbmcvfs.translatePath(os.path.join(
        ADDON.getAddonInfo('path'), 'resources', 'station_list.csv'))
    station_list = []
    with open(filename, newline='', encoding='utf8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            # TODO: Find a better station list without mojibake! -----v
            station_list.append(
                (row['ID'], row['NAME'].replace(chr(65533), '').title()))
    return station_list


def find_station_by_name(station_name):
    station_list = load_station_list()
    # TODO: Check whether to use SequenceMatcher from difflib or other algorithms like Levenshtein Distance.
    station_list = [s for s in station_list if station_name in s[1]]
    return check_station_list(station_list)


def find_location(location_no):
    """
    Find all locations from a station list of the DWD by searching for a keyword.
    """
    keyword = get_keyboard_text('', xbmc.getLocalizedString(14024), False)
    if keyword:
        log(f'Searching for location: {keyword}')
        found_stations = find_station_by_name(keyword)
        labels = [s[1] for s in found_stations]
        if labels:
            selected = dialog_select('Choose a location...', labels)
            log(f'Selected: {selected}')
            if selected != -1:
                selected_location = found_stations[selected]
                log(f'Selected location: {selected_location}')
                ADDON.setSetting('Location{0}'.format(
                    location_no), selected_location[1])
                ADDON.setSetting('Location{0}ID'.format(
                    location_no), selected_location[0])
                ADDON.setSetting('Location{0}Name'.format(
                    location_no), selected_location[1])
        else:
            xbmcgui.Dialog().ok('Station not found', 'Could not find a station like that')


def dialog_select(heading, _list, **kwargs):
    return xbmcgui.Dialog().select(heading, _list, **kwargs)


def get_keyboard_text(line='', heading='', hidden=False):
    """
    Get a text input from on-screen keyboard in Kodi or return a empty text if
    the user aborts the dialog.

    Source: https://github.com/vlmaksime/weather.gismeteo/blob/master/weather.gismeteo/resources/libs/__init__.py
    """
    kbd = xbmc.Keyboard(line, heading, hidden)
    kbd.doModal()
    if kbd.isConfirmed():
        return kbd.getText()
    return ''


def main():
    """
    Start the weather addon for Kodi.
    """
    log(f'{ADDON.getAddonInfo("name")} version {ADDON.getAddonInfo("version")} started with argv: {sys.argv}')
    if sys.argv[1] == 'find_location':
        log('find_location: ' + sys.argv[2])
        find_location(sys.argv[2])
    elif sys.argv[1] in ('1', '2', '3', '4'):
        location_no = int(sys.argv[1])
        log(f'Fetching weather for location no. {location_no}')
        fetch_weather_data(location_no)
        set_property('WeatherProvider', 'DWD')
        set_property('WeatherProviderLogo', xbmcvfs.translatePath(os.path.join(
            ADDON.getAddonInfo('path'), 'resources', 'media', 'dwd-logo-png.png')))
        # set location information
        for count, name in enumerate(get_station_names(), start=1):
            set_property(f'Location{count}', name)
            if count == location_no:
                current_station_name = get_station_names()[location_no-1]
                set_property('Current.Location', current_station_name)
                set_property('Forecast.City', current_station_name)
                set_property('Forecast.Country', 'Germany')
                # set_property('Forecast.State', 'true')
                # TODO: Get coordinates from station list.
                # set_property('Forecast.Latitude', '')
                # set_property('Forecast.Longitude', '')
        set_property('Locations', len(get_station_names()))
        # set flags
        set_property('DWD.IsFetched', 'true')
        set_property('Forecast.IsFetched', 'true')
        set_property('Current.IsFetched', 'true')
        set_property('Today.IsFetched', 'true')
        set_property('Detailed.IsFetched', 'true')
        set_property('Daily.IsFetched', 'false')
        set_property('Weekend.IsFetched', 'false')
        set_property('36Hour.IsFetched', 'false')
        set_property('Hourly.IsFetched', 'false')
    else:
        log('Unsupported command line argument!', xbmc.LOGERROR)


main()
