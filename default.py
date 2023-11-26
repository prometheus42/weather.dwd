
import os
import sys

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
STATION_ID = 'E626'
API_URL = 'https://app-prod-ws.warnwetter.de/v30/stationOverviewExtended?stationIds={station}'

ICON_MAPPING = {
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
    32767: 'keine Angabe???'
}

WEATHER_ICON_MAPPING = {
    0: 	'tornado',
    1: 	'tropical storm',
    2: 	'hurricane',
    3: 	'severe thunderstorms',
    4: 	'thunderstorms',
    5: 	'mixed rain and snow',
    6: 	'mixed rain and sleet',
    7: 	'mixed snow and sleet',
    8: 	'freezing drizzle',
    9: 	'drizzle',
    10: 'freezing rain',
    11: 'showers',
    12: 'showers',
    13: 'snow flurries',
    14: 'light snow showers',
    15: 'blowing snow',
    16: 'snow',
    17: 'hail',
    18: 'sleet',
    19: 'dust',
    20: 'foggy',
    21: 'haze',
    22: 'smoky',
    23: 'blustery',
    24: 'windy',
    25: 'cold',
    26: 'cloudy',
    27: 'mostly cloudy (night)',
    28: 'mostly cloudy (day)',
    29: 'partly cloudy (night)',
    30: 'partly cloudy (day)',
    31: 'clear (night)',
    32: 'sunny',
    33: 'fair (night)',
    34: 'fair (day)',
    35: 'mixed rain and hail',
    36: 'hot',
    37: 'isolated thunderstorms',
    38: 'scattered thunderstorms',
    39: 'scattered thunderstorms',
    40: 'scattered showers',
    41: 'heavy snow',
    42: 'scattered snow showers',
    43: 'heavy snow',
    44: 'partly cloudy',
    45: 'thundershowers',
    46: 'snow showers',
    47: 'isolated thundershowers',
    "na": 'not available',
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
    if DEBUG:
        message = f'{ADDONID}: {txt}'
        xbmc.log(msg=message, level=level)


def fetch_location(num):
    """Fetch list of stations and set station name from ID."""
    log(f'Fetching Location name for ID: {num}')
    list_of_stations = {
        8040: 'Woanders',
        8041: 'Bramsche',
        8042: 'Keine-Ahnung',
    }
    prefix = "Location"+num
    station_id = ADDON.getSetting(prefix+'ID')
    location_name = list_of_stations[station_id]
    ADDON.setSetting(prefix, location_name)


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
    for count in range(0, MAXDAYS+1):
        set_property(f'Day{count}.Title', 'N/A')
        set_property(f'Day{count}.HighTemp', '0')
        set_property(f'Day{count}.LowTemp', '0')
        set_property(f'Day{count}.Outlook', 'N/A')
        set_property(f'Day{count}.OutlookIcon', 'na.png')
        set_property(f'Day{count}.FanartCode', 'na')


def fetch_weather_data():
    """
    Fetches weather data from DWD and sets properties for next 10 days???.
    """
    r = requests.get(API_URL.format(station=STATION_ID), timeout=10)
    weather_data, = r.json().values()
    current_data = weather_data["forecast1"]
    set_property('Current.Condition',
                 ICON_MAPPING[current_data["icon"][0]])  # 'icon1h'
    # if temperatur == 32767: pass
    set_property('Current.Temperature', current_data["temperature"][0])
    set_property('Current.Wind', '0')  # 'windSpeed'
    set_property('Current.WindDirection', 'N/A')  # 'windDirection'
    set_property('Current.Humidity', int(current_data['humidity'][0])/10)
    set_property('Current.ChancePrecipitation',
                 current_data['precipitationProbablity'])  # precipitationTotal
    set_property('Current.FeelsLike', '0')
    set_property('Current.UVIndex', '0')
    set_property('Current.DewPoint', int(current_data['dewPoint2m'][0])/10)
    set_property('Current.OutlookIcon', 'na.png')
    set_property('Current.WindGust', current_data['windGust'])
    # set_property('Current.SeaLevel'	, '')
    # set_property('Current.GroundLevel'	, '')
    set_property('Current.FanartCode', 'na')
    # TODO: Check whether to include: sunshine, surfacePressure, isDay.
    # use wind information from first day (today!), because it is missing in the 'current' data
    set_property('Current.Wind', weather_data['days'][0]['windSpeed'])
    wind_direction = int(weather_data['days'][0]['windDirection']) / 10
    set_property('Current.WindDirection', xbmc.getLocalizedString(get_wind_direction(wind_direction)))
    #
    for count, day in enumerate(weather_data['days'][1:]):
        set_property(f'Day{count}.Title', day['dayDate'])
        set_property(f'Day{count}.HighTemp', day['temperatureMax'])
        set_property(f'Day{count}.LowTemp', day['temperatureMin'])
        # set_property('Daily.%i.TempDay' % (count+1), u'%s%s' % (FtoC(item['temperature']), TEMPUNIT))
        # set_property('Daily.%i.TempNight'	% (count+1), '')
        set_property(f'Day{count}.Outlook', ICON_MAPPING[day['icon']])
        # set_property('Daily.%i.WindDirection'	% (count+1), item['windDirection'])
        # set_property('Daily.%i.WindSpeed'	% (count+1), item['windSpeed'])
        # set_property('Daily.%i.ShortOutlook'	% (count+1), item['shortForecast'])
        # set_property('Daily.%i.DetailedOutlook'	% (count+1), item['detailedForecast'])
        # 		code, rain=code_from_icon(icon)
        # 		weathercode = WEATHER_CODES.get(code)
        # TODO: WEATHER_ICON % weathercode
        set_property(f'Day{count}.OutlookIcon', 'na.png')
        set_property(f'Day{count}.FanartCode', 'na')  # TODO: weathercode
        # set_property('Day%i.isDaytime'		% (count),str(item['isDaytime']))
        # set_property('Day%i.Title'		% (count), item['name'])
        # set_property('Daily.%i.LongDay'		% (count+1), item['name'])
        # set_property('Daily.%i.ShortDay'	% (count+1), get_weekday(startstamp,'s')+" (d)")
        set_property(f'Daily.{count+1}.Precipitation', day['precipitation'])


def fetch_weather_alerts():
    """
    Fetches any weather alerts for location.
    """
    r = requests.get(API_URL.format(station=STATION_ID), timeout=10)
    weather_data, = r.json().values()
    warning_data = weather_data['warnings']
    if warning_data:
        set_property('Alerts.IsFetched', 'true')
        for count, w in enumerate(warning_data, start=1):
            # warn_id = w["warnId"]
            # warn_type = w["type"]
            # level = w["level"]
            # "start": 1701010800000,
            # "end": 1701075600000,
            # "bn": false,
            # "descriptionText": "Es tritt leichter Frost zwischen -2 °C und -4 °C auf.",
            set_property(f'Alerts.{count}.headline', w['headline'])
            set_property(f'Alerts.{count}.instruction', w['instruction'])
            set_property(f'Alerts.{count}.description', w['description'])
            set_property(f'Alerts.{count}.event', w['event'])
            # set_property('Alerts.%i.status'		% (count+1), str(thisdata['status']))
            # set_property('Alerts.%i.messageType'	% (count+1), str(thisdata['messageType']))
            # set_property('Alerts.%i.category'	% (count+1), str(thisdata['category']))
            # set_property('Alerts.%i.severity'	% (count+1), str(thisdata['severity']))
            # set_property('Alerts.%i.certainty'	% (count+1), str(thisdata['certainty']))
            # set_property('Alerts.%i.urgency'	% (count+1), str(thisdata['urgency']))
            # set_property('Alerts.%i.response'	% (count+1), str(thisdata['response']))
    else:
        clear_property('Alerts.IsFetched')
        xbmc.log('No current weather alerts.', level=xbmc.LOGDEBUG)


########################################################################################
# Main Kodi entry point
########################################################################################
log(
    f'version {ADDON.getAddonInfo("version")} started with argv: {sys.argv[1]}')

fetch_weather_data()
fetch_weather_alerts()

set_property('Location1', 'Bramsche')
set_property('Locations', 1)
set_property('Forecast.IsFetched', 'true')
set_property('Current.IsFetched', 'true')
# set_property('Today.IsFetched', '')
# set_property('Daily.IsFetched', 'true')
# set_property('Detailed.IsFetched', 'true')
# set_property('Weekend.IsFetched', '')
# set_property('36Hour.IsFetched', '')
# set_property('Hourly.IsFetched', 'true')
set_property('DWD.IsFetched', 'true')
set_property('WeatherProvider', 'DWD')
set_property('WeatherProviderLogo', xbmcvfs.translatePath(os.path.join(
    ADDON.getAddonInfo('path'), 'resources', 'media', 'dwd-logo-png.png')))
