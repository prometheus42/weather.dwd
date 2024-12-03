
import math

import xbmc
import xbmcaddon

from resources.lib.utils import log


ADDON = xbmcaddon.Addon()
ADDONID = ADDON.getAddonInfo('id')
LANGUAGE = ADDON.getLocalizedString

DEBUG = ADDON.getSetting('Debug')
TEMPUNIT = xbmc.getRegion('tempunit')
SPEEDUNIT = xbmc.getRegion('speedunit')
DATEFORMAT = xbmc.getRegion('dateshort')
TIMEFORMAT = xbmc.getRegion('meridiem')


def SPEED(mps):
    try:
        val = float(mps)
    except:
        return ''

    if SPEEDUNIT == 'km/h':
        speed = mps * 3.6
    elif SPEEDUNIT == 'm/min':
        speed = mps * 60
    elif SPEEDUNIT == 'ft/h':
        speed = mps * 11810.88
    elif SPEEDUNIT == 'ft/min':
        speed = mps * 196.84
    elif SPEEDUNIT == 'ft/s':
        speed = mps * 3.281
    elif SPEEDUNIT == 'mph':
        speed = mps * 2.237
    elif SPEEDUNIT == 'knots':
        speed = mps * 1.944
    elif SPEEDUNIT == 'Beaufort':
        speed = KPHTOBFT(mps * 3.6)
    elif SPEEDUNIT == 'inch/s':
        speed = mps * 39.37
    elif SPEEDUNIT == 'yard/s':
        speed = mps * 1.094
    elif SPEEDUNIT == 'Furlong/Fortnight':
        speed = mps * 6012.886
    else:
        speed = mps
    return str(int(round(speed)))


def FtoC(Fahrenheit):
    try:
        Celsius = (float(Fahrenheit) - 32.0) * 5.0/9.0
        return str(int(round(Celsius)))
    except:
        return


def CtoF(Celsius):
    try:
        Fahrenheit = (float(Celsius) * 9.0/5.0) + 32.0
        return str(int(round(Fahrenheit)))
    except:
        return


def TEMP(deg):
    if TEMPUNIT == u'\N{DEGREE SIGN}'+'F':
        temp = deg * 1.8 + 32
    elif TEMPUNIT == u'K':
        temp = deg + 273.15
    elif TEMPUNIT == u'°Ré':
        temp = deg * 0.8
    elif TEMPUNIT == u'°Ra':
        temp = deg * 1.8 + 491.67
    elif TEMPUNIT == u'°Rø':
        temp = deg * 0.525 + 7.5
    elif TEMPUNIT == u'°D':
        temp = deg / -0.667 + 150
    elif TEMPUNIT == u'°N':
        temp = deg * 0.33
    else:
        temp = deg
    return str(int(round(temp)))


def KPHTOBFT(spd):
    if (spd < 1.0):
        bft = '0'
    elif (spd >= 1.0) and (spd < 5.6):
        bft = '1'
    elif (spd >= 5.6) and (spd < 12.0):
        bft = '2'
    elif (spd >= 12.0) and (spd < 20.0):
        bft = '3'
    elif (spd >= 20.0) and (spd < 29.0):
        bft = '4'
    elif (spd >= 29.0) and (spd < 39.0):
        bft = '5'
    elif (spd >= 39.0) and (spd < 50.0):
        bft = '6'
    elif (spd >= 50.0) and (spd < 62.0):
        bft = '7'
    elif (spd >= 62.0) and (spd < 75.0):
        bft = '8'
    elif (spd >= 75.0) and (spd < 89.0):
        bft = '9'
    elif (spd >= 89.0) and (spd < 103.0):
        bft = '10'
    elif (spd >= 103.0) and (spd < 118.0):
        bft = '11'
    elif (spd >= 118.0):
        bft = '12'
    else:
        bft = ''
    return bft


def FEELS_LIKE(Ts, Vs=0, Rs=0, ext=True):
    # thanks to FrostBox @ http://forum.kodi.tv/showthread.php?tid=114637&pid=937168#pid937168
    T = float(Ts)
    V = float(Vs)
    R = float(Rs)

    if T <= 10.0 and V >= 8.0:
        FeelsLike = WIND_CHILL(T, V)
    elif T >= 26.0:
        FeelsLike = HEAT_INDEX(T, R)
    else:
        FeelsLike = T
    if ext:
        return TEMP(FeelsLike)
    else:
        return str(int(round(FeelsLike)))


def WIND_CHILL(Ts, Vs):
    T = float(Ts)
    V = float(Vs)

    FeelsLike = (13.12 + (0.6215 * T) -
                 (11.37 * V**0.16) + (0.3965 * T * V**0.16))
    return FeelsLike


def HEAT_INDEX(Ts, Rs):
    # https://en.wikipedia.org/wiki/Heat_index
    T = float(Ts)
    R = float(Rs)
    T = T * 1.8 + 32.0  # calaculation is done in F
    FeelsLike = -42.379 + (2.04901523 * T) + (10.14333127 * R) + (-0.22475541 * T * R) + (-0.00683783 * T**2) + \
        (-0.05481717 * R**2) + (0.00122874 * T**2 * R) + \
        (0.00085282 * T * R**2) + (-0.00000199 * T**2 * R**2)
    FeelsLike = (FeelsLike - 32.0) / 1.8  # convert to C
    return FeelsLike


def DEW_POINT(Tc=0, RH=93.0, ext=True, minRH=(0, 0.075)[0]):
    # thanks to FrostBox @ http://forum.kodi.tv/showthread.php?tid=114637&pid=937168#pid937168
    Es = 6.11 * 10.0**(7.5 * Tc / (237.7 + Tc))
    RH = RH or minRH
    E = (RH * Es) / 100
    try:
        DewPoint = (-430.22 + 237.7 * math.log(E)) / (-math.log(E) + 19.08)
    except ValueError:
        DewPoint = 0
    if ext:
        return TEMP(DewPoint)
    else:
        return str(int(round(DewPoint)))
