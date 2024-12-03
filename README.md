# weather.dwd - A Kodi Plugin for the German weather service (DWD) weather forecasts

This Kodi addon fetches weather reports from the German weather service.

The weather data for this addon are provided by the Deutscher Wetterdienst
(DWD) for the use in the official WarnWetter app. It provides weather forecasts
mainly for Germany, other locations may be supported. All spatial data
including weather and climate information are provided under the Creative
Commons licence CC BY 4.0 as stated in the [legal notices](https://www.dwd.de/EN/service/legal_notice/legal_notice.html).
More information about the DWD can be found on their [homepage](https://www.dwd.de/).

All weather stations for which information can be obtained can be found in the [station list from the DWD](https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/mosmix_stationskatalog.cfg).

## Installation
Download the newest release from the [Github Releases page](https://github.com/prometheus42/weather.dwd/releases) and install it
manually in Kodi.

## Build
To build a new release, the version has to be changed in addon.xml and the
changelog has to be updated. After that the release archive can be created with
the following command:

    pipenv run python build.py 

## Links
* This plugin is based on the NOAA plugin: https://github.com/randallspicher/weather.noaa/
* Some code was taken from: https://github.com/vlmaksime/weather.gismeteo/
* All information about developing Kodi addons: https://kodi.wiki/view/Add-on_development
* Kodi wiki entry for developing weather plugins: https://kodi.wiki/view/Weather_addons
* Info for settings in Kodi addons: https://kodi.wiki/view/Add-on_settings
* OpenAPI for the weather API of the DWD: https://github.com/bundesAPI/dwd-api
