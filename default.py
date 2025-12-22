"""
A Kodi Plugin for the German Weather Service (DWD) weather forecasts.
"""

import os
import sys
import shelve
from datetime import datetime
from datetime import timedelta

import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon

from resources.lib.utils import log
from resources.lib.weather import DWD_ICON_MAPPING, get_wind_direction, get_icon_code_for_weather, get_icon_path_for_weather, calc_feels_like_temperature
from resources.lib.dwd import fetch_forecast_data, get_station_names, find_station_by_name, get_coordinates_for_station, div10, calc_time, DWDException


WEATHER_WINDOW = xbmcgui.Window(12600)

ADDON = xbmcaddon.Addon()
ADDONID = ADDON.getAddonInfo('id')
LANGUAGE = ADDON.getLocalizedString
DEBUG = ADDON.getSetting('Debug')

CACHE_LIFETIME = 3  # time in hours after which cache content is discarded
SHELVE_PATH = xbmcvfs.translatePath(os.path.join(ADDON.getAddonInfo('profile')))
SHELVE_FILE = xbmcvfs.translatePath(os.path.join(ADDON.getAddonInfo('profile'), 'weather.data'))

TEMP_UNIT = '°C'  # set temperature unit manually to match DWD data
WIND_SPEED_UNIT = 'km/h'  # set wind speed unit manually to match DWD data
PRESSURE_UNIT = 'hPa'  # set pressure unit manually to match DWD data
DATE_SHORT_FORMAT = xbmc.getRegion('dateshort')
DATE_LONG_FORMAT = xbmc.getRegion('datelong')
TIME_FORMAT = xbmc.getRegion('time')
WEEKDAY_FORMAT = '%a'


def set_property(name, value):
    """Set a property on the weather window object."""
    WEATHER_WINDOW.setProperty(name, str(value))


def clear_property(name):
    """Clear all properties."""
    WEATHER_WINDOW.clearProperty(name)


def set_properties_for_weather_data(weather_data):
    """
    Set properties for a single weather station for today and the next days.

    List of all labels:
     - https://github.com/xbmc/repo-scripts/raw/jarvis/weather.openweathermap.extended/README.txt
     - https://github.com/vlmaksime/weather.gismeteo/raw/master/weather.gismeteo/README.txt
    """
    log(f'Marshal weather data for {weather_data["forecast1"]["stationId"]}')
    # get current hour on today to know which value to use
    current_hour = datetime.now().hour
    log(f'Current hour is: {current_hour}')
    # get values from forecast data (with 1 hour time step) and save it to the correct properties
    current_data = weather_data['forecast1']
    # first element of array for most metrics is the current hour,
    # there are some exceptions like 'isDay' were the array starts at hour 0
    is_day = current_data['isDay'][current_hour]
    set_property('Current.Condition', DWD_ICON_MAPPING[current_data['icon1h'][0]])
    set_property('Current.Temperature', div10(current_data['temperature'][current_hour]))
    set_property('Current.Humidity', div10(current_data['humidity'][0]))
    set_property('Current.DewPoint', div10(current_data['dewPoint2m'][0]))
    set_property('Current.OutlookIcon', get_icon_path_for_weather(current_data['icon1h'][0], is_day))
    # TODO: Check why wind and precipitation data is mostly empty?!
    set_property('Current.Pressure', div10(current_data['surfacePressure'][0]))
    sunrise = calc_time(weather_data['days'][0]['sunrise'], TIME_FORMAT)
    set_property('Today.Sunrise', sunrise)
    sunset = calc_time(weather_data['days'][0]['sunset'], TIME_FORMAT)
    set_property('Today.Sunset', sunset)
    set_property('Current.FanartCode', get_icon_code_for_weather(current_data['icon1h'][0], is_day))
    set_property('Current.ConditionIcon', get_icon_path_for_weather(current_data['icon1h'][0], is_day))
    # use wind information from first day (today!), because it is missing in the 'current' data
    set_property('Current.Wind', div10(weather_data['days'][0]['windSpeed']))
    wind_direction = div10(weather_data['days'][0]['windDirection'])
    set_property('Current.WindDirection', xbmc.getLocalizedString(get_wind_direction(wind_direction)))
    # TODO: 'precipitation' is not probability, it's amount in 10th of mm per day
    #       set_property('Current.Precipitation', weather_data['days'][0]['precipitation'])
    # calculate feels like temperature
    feelslike = calc_feels_like_temperature(div10(current_data['temperature'][current_hour]), div10(weather_data['days'][0]['windSpeed']))
    set_property('Current.FeelsLike', feelslike)

    # fill in the forecast for the next days
    for no, day in enumerate(weather_data['days']):
        dt = datetime.fromisoformat(day['dayDate'])
        # Day0.xxx - Day6.xxx
        if no < 7:
            set_property(f'Day{no}.Title', dt.strftime(DATE_SHORT_FORMAT))
            set_property(f'Day{no}.HighTemp', div10(day['temperatureMax']))
            set_property(f'Day{no}.LowTemp', div10(day['temperatureMin']))
            set_property(f'Day{no}.Outlook', DWD_ICON_MAPPING[day['icon']])
            set_property(f'Day{no}.OutlookIcon', get_icon_path_for_weather(day['icon']))
            set_property(f'Day{no}.FanartCode', get_icon_code_for_weather(day['icon']))
        # Daily.1.xxx - Daily.10.xxx
        set_property(f'Daily.{no+1}.ShortDay', dt.strftime(WEEKDAY_FORMAT))
        set_property(f'Daily.{no+1}.ShortDate', dt.strftime(DATE_SHORT_FORMAT))
        set_property(f'Daily.{no+1}.Outlook', DWD_ICON_MAPPING[day['icon']])
        set_property(f'Daily.{no+1}.OutlookIcon', get_icon_path_for_weather(day['icon']))
        set_property(f'Daily.{no+1}.FanartCode', get_icon_code_for_weather(day['icon']))
        set_property(f'Daily.{no+1}.WindSpeed', f'{div10(day["windSpeed"])} {WIND_SPEED_UNIT}')
        set_property(f'Daily.{no+1}.WindDirection', xbmc.getLocalizedString(get_wind_direction(day['windDirection'])))
        set_property(f'Daily.{no+1}.HighTemperature', f'{div10(day["temperatureMax"])} {TEMP_UNIT}')
        set_property(f'Daily.{no+1}.LowTemperature', f'{div10(day["temperatureMin"])} {TEMP_UNIT}')
        # TODO: 'precipitation' is not probability, it's amount in 10th of mm per day
        #       set_property(f'Daily.{no+1}.Precipitation', day['precipitation'])

    # Hourly.1.xxx - Hourly.24.xxx
    current_time = datetime.now()
    for no in range(24):
        temp_hour = current_time + timedelta(hours=no)
        weather_data_index = current_time.hour + no
        is_day = current_data['isDay'][weather_data_index]
        set_property(f'Hourly.{no+1}.Time', temp_hour.strftime('%H:00'))
        set_property(f'Hourly.{no+1}.LongDate', temp_hour.strftime(DATE_LONG_FORMAT))
        set_property(f'Hourly.{no+1}.ShortDate', temp_hour.strftime(DATE_SHORT_FORMAT))
        set_property(f'Hourly.{no+1}.Outlook', DWD_ICON_MAPPING[current_data['icon1h'][weather_data_index]])
        set_property(f'Hourly.{no+1}.OutlookIcon', get_icon_path_for_weather(current_data['icon1h'][weather_data_index], is_day))
        set_property(f'Hourly.{no+1}.FanartCode', get_icon_code_for_weather(current_data['icon1h'][weather_data_index], is_day))
        set_property(f'Hourly.{no+1}.Temperature', f'{div10(current_data["temperature"][weather_data_index])} {TEMP_UNIT}')
        set_property(f'Hourly.{no+1}.DewPoint', f'{div10(current_data["dewPoint2m"][weather_data_index])} {TEMP_UNIT}')
        set_property(f'Hourly.{no+1}.Humidity', div10(current_data['humidity'][weather_data_index]))
        set_property(f'Hourly.{no+1}.Rain', div10(current_data['precipitationTotal'][weather_data_index]))
        set_property(f'Hourly.{no+1}.Pressure', f'{div10(current_data["surfacePressure"][weather_data_index])} {PRESSURE_UNIT}')


def set_properties_for_alert_data(weather_data):
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


def start_find_location_dialog(location_no):
    """
    Find all locations from a station list of the DWD by searching for a keyword.
    """
    keyword = get_keyboard_text('', xbmc.getLocalizedString(14024), False)
    if keyword:
        log(f'Searching for location: {keyword}')
        found_stations = find_station_by_name(keyword)
        labels = [s[1] for s in found_stations]
        if labels:
            selected = dialog_select(xbmc.getLocalizedString(32345), labels)
            log(f'Selected: {selected}')
            if selected != -1:
                selected_location = found_stations[selected]
                log(f'Selected location: {selected_location}')
                ADDON.setSetting(f'Location{location_no}ID', selected_location[0])
                ADDON.setSetting(f'Location{location_no}', selected_location[1])
                ADDON.setSetting(f'Location{location_no}Name', selected_location[1])
        else:
            xbmcgui.Dialog().ok(LANGUAGE(32346), LANGUAGE(32347))


def dialog_select(heading, _list, **kwargs):
    """
    Show a dialog to select an item from a given list.
    """
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
    global CACHE_LIFETIME
    CACHE_LIFETIME = int(ADDON.getSetting('CacheLifetime'))
    log(f'Setting cache lifetime to {CACHE_LIFETIME} hours.')
    # create addon folder in profile if it doesn't exist
    os.makedirs(SHELVE_PATH, exist_ok=True)
    # read existing shelve or create a new one if it doesn't exist
    data_shelf = shelve.open(SHELVE_FILE, flag='c')
    # handle command line arguments for Kodi settings page
    if sys.argv[1] == 'find_location':
        log('find_location: ' + sys.argv[2])
        start_find_location_dialog(sys.argv[2])
    elif sys.argv[1] in ('1', '2', '3', '4'):
        location_no = int(sys.argv[1])
        log(f'Fetching weather for location no. {location_no}')
        try:
            lastupdatekey = 'dwd_lastupdate'
            weatherdatakey = 'dwd_weatherdata'
            # get weather data...
            if (weatherdatakey in data_shelf and location_no in data_shelf[weatherdatakey]
                    and (datetime.now() - data_shelf[lastupdatekey]) < timedelta(hours=CACHE_LIFETIME)):
                # ...from cache if there is data for the requested location and it is still fresh
                log(f'Getting weather data for location no. {location_no} from shelf.')
                weather_data = data_shelf[weatherdatakey]
            else:
                # ...from DWD API if shelved data is stale
                log(f'Stored weather data is older than {CACHE_LIFETIME} hours!')
                weather_data = fetch_forecast_data()
                log(f'Storing weather data at {datetime.now()} in shelf.')
                data_shelf[lastupdatekey] = datetime.now()
                data_shelf[weatherdatakey] = weather_data
            # evaluate weather data and set properties for Kodi
            set_properties_for_weather_data(weather_data[location_no])
            set_properties_for_alert_data(weather_data[location_no])
            set_property('WeatherProvider', 'DWD')
            set_property('WeatherProviderLogo',
                         xbmcvfs.translatePath(os.path.join(ADDON.getAddonInfo('path'), 'resources', 'media', 'logo.png')))
            # set location information
            set_property('Locations', len(get_station_names()))
            for count, name in enumerate(get_station_names(), start=1):
                set_property(f'Location{count}', name)
                if count == location_no:
                    current_station_name = get_station_names()[location_no-1]
                    set_property('Location', current_station_name)
                    set_property('Current.Location', current_station_name)
                    set_property('Forecast.City', current_station_name)
                    set_property('Forecast.Country', 'Germany')
                    lat, lon = get_coordinates_for_station(current_station_name)
                    set_property('Forecast.Latitude', lat)
                    set_property('Forecast.Longitude', lon)
            set_property('Locations', len(get_station_names()))
            # set flags
            set_property('DWD.IsFetched', True)
            set_property('Weather.IsFetched', True)
            set_property('Forecast.IsFetched', True)
            set_property('Current.IsFetched', True)
            set_property('Today.IsFetched', True)
            set_property('Hourly.IsFetched', True)
            set_property('Daily.IsFetched', True)
        except DWDException as e:
            log(f'Could not get weather information: {e}')
    else:
        log('Unsupported command line argument!', xbmc.LOGERROR)
    data_shelf.close()


main()
