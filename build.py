#!/usr/bin/env python3

import os
from zipfile import ZipFile
from xml.dom.minidom import parse

import build_station_list


included_files = [
    'addon.xml',
    'changelog.txt',
    'LICENSE',
    'README.md',
    'resources',
    'default.py'
]

# get version from addon.xml
with open('addon.xml', 'r') as addonxml:
    dom = parse(addonxml)
    addon_id = dom.getElementsByTagName('addon')[0].getAttribute('id')
    addon_version = dom.getElementsByTagName('addon')[0].getAttribute('version')

# create release directory if it doesn't exist
release_dir = 'releases'
os.makedirs(release_dir, exist_ok=True)

# build station list for addon
# build_station_list.build_station_list()

# build ZIP file with all the resources
print(f'Creating {addon_id}-{addon_version}.zip file...')
with ZipFile(os.path.join(f'{release_dir}', f'{addon_id}-{addon_version}.zip'), 'w') as releasezip:
    for file in included_files:
        if os.path.isfile(file):
            releasezip.write(file, os.path.join(addon_id, file))
        elif os.path.isdir(file):
            for root, dirs, files in os.walk(file):
                for name in files:
                    releasezip.write(os.path.join(root, name), os.path.join(addon_id, root, name))
