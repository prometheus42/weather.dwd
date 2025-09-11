
DWD_ICON_MAPPING = {
    1: 'Sonne',
    2: 'Sonne, leicht bewölkt',
    3: 'Sonne, bewölkt',
    4: 'Wolken',
    5: 'Nebel',
    6: 'Nebel, Rutschgefahr',
    7: 'Leichter Regen',
    8: 'Regen',
    9: 'Starker Regen',
    10: 'Leichter Regen, Rutschgefahr',
    11: 'Starker Regen, Rutschgefahr',
    12: 'Regen, vereinzelt Schneefall',
    13: 'Regen, vermehrt Schneefall',
    14: 'Leichter Schneefall',
    15: 'Schneefall',
    16: 'Starker Schneefall',
    17: 'Wolken, (Hagel)',
    18: 'Sonne, leichter Regen',
    19: 'Sonne, starker Regen',
    20: 'Sonne, Regen, vereinzelter Schneefall',
    21: 'Sonne, Regen, vermehrter Schneefall',
    22: 'Sonne, vereinzelter Schneefall',
    23: 'Sonne, vermehrter Schneefall',
    24: 'Sonne, (Hagel)',
    25: 'Sonne, (starker Hagel)',
    26: 'Gewitter',
    27: 'Gewitter, Regen',
    28: 'Gewitter, starker Regen',
    29: 'Gewitter, (Hagel)',
    30: 'Gewitter, (starker Hagel)',
    31: 'Wind',
    32767: 'not available'
}


DWD_TO_KODI_ICON_MAPPING = {
    1: 32,  # Sonne -> clear (day)
    # 1: 31, # Sonne -> clear (night)
    # TODO: Choose correct icon depending on time of the day!
    2: 30,  # Sonne, leicht bewölkt -> 'partly cloudy (day)'
    # 2: 29,  # Sonne, leicht bewölkt -> 'partly cloudy (night)'
    # 2: 44,  # Sonne, leicht bewölkt -> partly cloudy
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


def get_icon_code_for_weather(icon_no, day=True):
    """
    Evaluates the icon number from the DWD and chooses the fitting icon code
    from the icons provided by Kodi.
    """
    if isinstance(icon_no, str):
        icon_no = int(icon_no)
    condition_icon_no = DWD_TO_KODI_ICON_MAPPING[icon_no]
    # correct icon if it is night
    if icon_no == 1 and not day:
        condition_icon_no = 31
    if icon_no == 2 and not day:
        condition_icon_no = 29
    if icon_no == 3 and not day:
        condition_icon_no = 27
    return condition_icon_no


def get_icon_path_for_weather(icon_no, day=True):
    """
    Evaluates the icon number from the DWD and gets the icon code and provides
    a file path to a fitting icon provided by Kodi.
    """
    condition_icon_no = get_icon_code_for_weather(icon_no, day=day)
    # condition_icon_file = xbmcvfs.translatePath(os.path.join(
    #    'resource://', 'resource.images.weathericons.default', f'{condition_icon_no}.png'))
    # condition_icon_file = xbmcvfs.translatePath(os.path.join(
    #    'special://home', 'addons', 'resource.images.weathericons.default', 'resources', f'{condition_icon_no}.png'))
    # WEATHER_ICON = xbmcvfs.translatePath('%s.png') % icon_no
    condition_icon_file = f'{condition_icon_no}.png'
    return condition_icon_file


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
