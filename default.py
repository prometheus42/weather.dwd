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
from resources.lib.dwd import fetch_weather_data, get_station_names, find_station_by_name, get_coordinates_for_station, div10, calc_time


WEATHER_WINDOW = xbmcgui.Window(12600)

ADDON = xbmcaddon.Addon()
ADDONID = ADDON.getAddonInfo('id')
LANGUAGE = ADDON.getLocalizedString
DEBUG = ADDON.getSetting('Debug')

MAXDAYS = 10
SHELVE_FILE = xbmcvfs.translatePath(os.path.join(ADDON.getAddonInfo('profile'), 'weather.data'))


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
    # get values from forecast data and save it to the correct properties
    current_data = weather_data['forecast1']
    set_property('Current.Condition',
                 DWD_ICON_MAPPING[current_data['icon1h'][current_hour]])
    set_property('Current.Temperature', div10(
        current_data['temperature'][current_hour]))
    set_property('Current.Humidity', div10(
        current_data['humidity'][current_hour]))
    set_property('Current.ChancePrecipitation',
                 current_data['precipitationProbablity'])  # precipitationTotal
    set_property('Current.DewPoint', div10(
        current_data['dewPoint2m'][current_hour]))
    # TODO: Use isDay[]
    set_property('Current.OutlookIcon',
                 get_icon_path_for_weather(current_data['icon1h'][current_hour]))
    # TODO: Check why wind and precipitation data is mostly empty?!
    set_property('Current.WindGust', current_data['windGust'])
    set_property('Current.Pressure', div10(
        current_data['surfacePressure'][current_hour]))
    set_property('Current.Precipitation',
                 current_data['precipitationTotal'][current_hour])
    sunrise = calc_time(weather_data['days'][0]['sunrise'])
    set_property('Today.Sunrise', sunrise)
    sunset = calc_time(weather_data['days'][0]['sunset'])
    set_property('Today.Sunset', sunset)
    set_property('Today.HighTemp', weather_data['days'][0]['temperatureMax'])
    set_property('Today.LowTemp', weather_data['days'][0]['temperatureMin'])
    set_property('Current.FanartCode', get_icon_code_for_weather(
        current_data['icon1h'][current_hour]))
    set_property('Current.ConditionIcon',
                 get_icon_path_for_weather(current_data['icon1h'][current_hour]))
    # TODO: Check were to put: sunshine.
    # use wind information from first day (today!), because it is missing in the 'current' data
    set_property('Current.Wind', div10(weather_data['days'][0]['windSpeed']))
    wind_direction = div10(weather_data['days'][0]['windDirection'])
    set_property('Current.WindDirection', xbmc.getLocalizedString(
        get_wind_direction(wind_direction)))
    # calculate feels like temperature
    set_property('Current.FeelsLike',  calc_feels_like_temperature(div10(
        current_data['temperature'][current_hour]), div10(weather_data['days'][0]['windSpeed'])))
    # fill in the forecast for the next days
    for no, day in enumerate(weather_data['days']):
        # Day0.xxx - Day6.xxx
        set_property(f'Day{no}.Title', day['dayDate'])
        set_property(f'Day{no}.HighTemp', div10(day['temperatureMax']))
        set_property(f'Day{no}.LowTemp', div10(day['temperatureMin']))
        set_property(f'Day{no}.Outlook', DWD_ICON_MAPPING[day['icon']])
        set_property(f'Day{no}.OutlookIcon',
                     get_icon_path_for_weather(day['icon']))
        set_property(f'Day{no}.FanartCode', 'na')
        # Daily.1.xxx - Daily.10.xxx
        dt = datetime.fromisoformat(day['dayDate'])
        set_property(f'Daily.{no}.LongDay', dt.strftime('%A'))
        set_property(f'Daily.{no}.ShortDay', dt.strftime('%a'))
        set_property(f'Daily.{no}.LongDate', dt.strftime('%d. %B'))
        set_property(f'Daily.{no}.ShortDate', dt.strftime('%d. %b'))
        set_property(f'Daily.{no}.Outlook', DWD_ICON_MAPPING[day['icon']])
        set_property(f'Daily.{no}.ShortOutlook', DWD_ICON_MAPPING[day['icon']])
        set_property(f'Daily.{no}.OutlookIcon',
                     get_icon_path_for_weather(day['icon']))
        set_property(f'Daily.{no}.FanartCode',
                     get_icon_code_for_weather(day['icon']))
        set_property(f'Daily.{no}.WindSpeed', div10(day['windSpeed']))
        set_property(f'Daily.{no}.WindDirection', xbmc.getLocalizedString(
            get_wind_direction(day['windDirection'])))
        set_property(f'Daily.{no}.WindDegree', day['windDirection'])
        set_property(f'Daily.{no}.WindGust', div10(day['windGust']))
        set_property(f'Daily.{no}.HighTemperature',
                     div10(day['temperatureMin']))
        set_property(f'Daily.{no}.LowTemperature',
                     div10(day['temperatureMax']))
        set_property(f'Daily.{no}.Precipitation', day['precipitation'])
        # set_property(f'Daily.{no}.TempMorn', )
        # set_property(f'Daily.{no}.TempDay', )
        # set_property(f'Daily.{no}.TempEve', )
        # set_property(f'Daily.{no}.TempNight', )
        # set_property(f'Daily.{no}.Humidity', )
        # set_property(f'Daily.{no}.DewPoint', )
        # set_property(f'Daily.{no}.FeelsLike', )
        # set_property(f'Daily.{no}.Pressure', )
        # set_property(f'Daily.{no}.Cloudiness', )
        # set_property(f'Daily.{no}.Rain', )
        # set_property(f'Daily.{no}.Snow', )
    # TODO: Check more extended labels.
    # Hourly.1.xxx - Hourly.24.xxx, 36Hour.1.xxx - 36Hour.3.xxx, Weekend.1.xxx - Weekend.2.xxx


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
                ADDON.setSetting(
                    f'Location{location_no}ID', selected_location[0])
                ADDON.setSetting(
                    f'Location{location_no}', selected_location[1])
                ADDON.setSetting(
                    f'Location{location_no}Name', selected_location[1])
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
    data_shelf = shelve.open(SHELVE_FILE)
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
            if lastupdatekey not in data_shelf or (datetime.now() - data_shelf[lastupdatekey]) > timedelta(hours=1):
                # ...from DWD API if shelved data is stale
                log('Stored weather data is older than 1 hours!')
                weather_data = fetch_weather_data(location_no)
                log(f'Storing weather data at {datetime.now()} in shelf.')
                data_shelf[lastupdatekey] = datetime.now()
                data_shelf[weatherdatakey] = weather_data
            else:
                # ...from stored data otherwise
                log('Getting weather data from shelf.')
                weather_data = data_shelf[weatherdatakey]
            # evaluate weather data and set properties for Kodi
    else:
        log('Unsupported command line argument!', xbmc.LOGERROR)
    data_shelf.close()


main()
