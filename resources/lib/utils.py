
import xbmc
import xbmcaddon


ADDON = xbmcaddon.Addon()
ADDONID = ADDON.getAddonInfo('id')
DEBUG = ADDON.getSetting('Debug')


def log(txt, level=xbmc.LOGDEBUG):
    """
    Log a message with a given log level.

    Source: https://github.com/randallspicher/weather.noaa/blob/master/resources/lib/utils.py
    """
    # if DEBUG:
    message = f'{ADDONID}: {txt}'
    xbmc.log(msg=message, level=level)
