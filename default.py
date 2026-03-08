"""
A Kodi Plugin for the German Weather Service (DWD) weather forecasts.
"""

import os
import sys
import shelve

import xbmc
import xbmcvfs
import xbmcaddon

from resources.lib.utils import log
from resources.lib.main import start_find_location_dialog, update_weather_for_location


ADDON = xbmcaddon.Addon()

SHELVE_PATH = xbmcvfs.translatePath(os.path.join(ADDON.getAddonInfo('profile')))
SHELVE_FILE = xbmcvfs.translatePath(os.path.join(ADDON.getAddonInfo('profile'), 'weather.data'))


def main():
    """
    Start the weather addon for Kodi.
    """
    log(f'{ADDON.getAddonInfo("name")} version {ADDON.getAddonInfo("version")} started with argv: {sys.argv}')
    # handle command line arguments for Kodi settings page
    if sys.argv[1] == 'find_location':
        query_string = sys.argv[2]
        log('Searching for location: ' + query_string)
        start_find_location_dialog(query_string)
    elif sys.argv[1] in ('1', '2', '3', '4'):
        location_no = int(sys.argv[1])
        log(f'Fetching weather for location no. {location_no}')
        # create addon folder in profile if it doesn't exist
        os.makedirs(SHELVE_PATH, exist_ok=True)
        # read existing shelve or create a new one if it doesn't exist
        data_shelf = shelve.open(SHELVE_FILE, flag='c')
        update_weather_for_location(location_no, data_shelf)
        data_shelf.close()
    else:
        log('Unsupported command line argument!', xbmc.LOGERROR)


main()
