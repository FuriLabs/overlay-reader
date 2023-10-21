#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
# Copyright (C) 2023 Bardia Moshiri <fakeshell@bardia.tech>

import os
import sys
import re
import json
import fnmatch
import subprocess
import argparse
from svg.path import Path, Line, Arc, CubicBezier, QuadraticBezier, parse_path

parser = argparse.ArgumentParser(description="Create JSON representation of device cutouts and border radius.")
parser.add_argument("-o", "--output", required=True, help="Path to the output JSON file")
args = parser.parse_args()

if os.getuid() != 0:
    print("must run as root, exiting")
    sys.exit(1)

def read_screen_size():
    height_file = '/var/lib/droidian/phosh-notch/height'
    width_file = '/var/lib/droidian/phosh-notch/width'

    try:
        with open(height_file, 'r') as f:
            height = int(f.read().strip())
    except Exception as e:
        print(f"Failed to read height from {height_file}, Error: {str(e)}")
        sys.exit(1)

    try:
        with open(width_file, 'r') as f:
            width = int(f.read().strip())
    except Exception as e:
        print(f"Failed to read width from {width_file}, Error: {str(e)}")
        sys.exit(1)

    return height, width

height, width = read_screen_size()

def parse_svg_string(svg_string, width):
    target_x = width / 2

    if '@right' in svg_string:
        target_x = width * 90 / 100
        svg_string = svg_string.replace('@right', '')
    elif '@left' in svg_string:
        target_x = width * 10 / 100
        svg_string = svg_string.replace('@left', '')

    return svg_string, target_x

def reposition_svg(svg_string, width):
    svg_string, target_x = parse_svg_string(svg_string, width)

    m_position = svg_string.find('M')
    if m_position == -1:
        m_position = svg_string.find('m')

    # If 'M' or 'm' is found, extract the substring from that position onwards
    if m_position != -1:
        svg_string = svg_string[m_position:]

    path_d_match = re.search('M(.*?)Z', svg_string, re.IGNORECASE)

    if path_d_match is None:
        print('No matching path found in SVG string')
        return None

    path_d = path_d_match.group(0)
    path = parse_path(path_d)

    x_coordinates = [point.real for segment in path for point in [segment.start, segment.end]]

    min_x, max_x = min(x_coordinates), max(x_coordinates)
    current_center_x = (min_x + max_x) / 2
    shift_distance = target_x - current_center_x
    new_path = Path()

    for segment in path:
        if isinstance(segment, Line):
            new_segment = Line(segment.start + complex(shift_distance, 0), segment.end + complex(shift_distance, 0))
        elif isinstance(segment, CubicBezier):
            new_segment = CubicBezier(segment.start + complex(shift_distance, 0), segment.control1 + complex(shift_distance, 0), segment.control2 + complex(shift_distance, 0), segment.end + complex(shift_distance, 0))
        elif isinstance(segment, QuadraticBezier):
            new_segment = QuadraticBezier(segment.start + complex(shift_distance, 0), segment.control + complex(shift_distance, 0), segment.end + complex(shift_distance, 0))
        elif isinstance(segment, Arc):
            new_segment = Arc(segment.start + complex(shift_distance, 0), segment.radius, segment.rotation, segment.large_arc, segment.sweep, segment.end + complex(shift_distance, 0))
        else:
            continue

        new_path.append(new_segment)

    return new_path.d()

def extract_value_from_prop(file, prop):
    with open(file, 'r') as f:
        for line in f:
            if line.startswith(prop):
                return line.split('=')[1].strip()

def get_cutout(rro_file):
    command = ['getoverlay', '-p', rro_file, '-c', 'config_mainBuiltInDisplayCutout']
    cutout_bytes = subprocess.check_output(command)
    cutout = cutout_bytes.decode('utf-8', 'ignore').strip()

    if "Failed to get value" in cutout:
        return None

    return cutout

def find_apk_with_properties(root_dir):
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if not 'emulation' in d.lower()]
        files = [f for f in files if not 'emulation' in f.lower()]
        for filename in files:
            if filename.endswith('.apk'):
                rro_file = os.path.join(root, filename)
                cutout_test = os.popen(f'getoverlay -p {rro_file} -c config_mainBuiltInDisplayCutout').read().strip()

                if "Failed to get value" in cutout_test:
                    continue

                # get the cutout again as the other function also cleans it
                cutout = get_cutout(rro_file)
                if cutout is None:
                    continue

                return rro_file

    return None

prop_files = [
    '/var/lib/lxc/android/rootfs/vendor/build.prop',
    '/android/vendor/build.prop',
    '/vendor/build.prop'
]

prop_file = None
for file in prop_files:
    if os.path.exists(file):
        prop_file = file
        break

if prop_file is None:
    print("no valid prop files found, exiting")
    sys.exit(0)

manufacturer = extract_value_from_prop(prop_file, 'ro.product.vendor.manufacturer')
model = extract_value_from_prop(prop_file, 'ro.product.vendor.model')
apiver = extract_value_from_prop(prop_file, 'ro.vendor.build.version.sdk')

rro_file = find_apk_with_properties('/vendor/overlay')

if rro_file is None:
    print("no valid files found, exiting")
    sys.exit(0)

if rro_file and os.path.exists(rro_file):
    radius = os.popen(f'getoverlay -p {rro_file} -c rounded_corner_radius_top').read().strip()
    if "Failed to get value" not in radius:
        radius = int(radius.rstrip('px').rstrip('dp'))
    else:
        radius = None

    if os.path.exists(rro_file):
        cutout = get_cutout(rro_file)
        if cutout is not None:
            cutout = reposition_svg(cutout, width)

    if radius is None and cutout is None:
        print("Device does not have a display cutout or a specified border radius.")
        sys.exit(0)

    json_obj = {
        "name": f"{manufacturer} {model}",
        "x-res": width,
        "y-res": height
    }

    if radius is not None:
        json_obj["border-radius"] = radius
    if cutout is not None:
        json_obj["cutouts"] = [{"name": "notch", "path": cutout}]

    with open(args.output, 'w') as json_file:
        json.dump(json_obj, json_file, indent=4)

else:
    print(f"{rro_file} does not exist, exiting")
    sys.exit(0)
