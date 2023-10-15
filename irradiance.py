#!/usr/bin/env python

import argparse
import pvlib
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import numpy
import urllib.parse
import time
import requests

from user_cfg import config


def parse_args ():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--filepath", dest="filepath", type=str, default="./",
                        help = "Filepath for output")
    parser.add_argument("--api-key", dest="api_key", type=str, default=None,
                        help = "User's API key from NSRDB")
    parser.add_argument("--email", dest="email", type=str, default=None,
                        help = "User's email address, associated with NSRDB API key")
    parser.add_argument("--latitude", dest="latitude", type=float,
                        help = "latitude of location")
    parser.add_argument("--longitude", dest="longitude", type=float,
                        help = "longitude of location")
    parser.add_argument("--altitude", dest="altitude", type=float,
                        help = "longitude of location")
    parser.add_argument("--place_holder", dest="place_holder", action="store_true", default=False,
                        help = "Boolean syntax placeholder")
    return parser.parse_args()


#API_KEY = "FhVfzpADNNmu6UUyNaXRCZYI5bZyOjFkb3OWQNmx"
#EMAIL = "stuart.baxley@gmail.com"
API_KEY = config["Stuart"]["API_KEY"]
EMAIL = config["Stuart"]["EMAIL"]
BASE_URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv?"


def pull_nsrdb_data(location, year = None):
    input_data = {
        'attributes': 'ghi,dhi,dni,wind_speed,air_temperature,solar_zenith_angle',
        'interval': '60',
        'wkt' : f'POINT({location.latitude} {location.longitude})',
        'api_key': API_KEY,
        'email': EMAIL,
        'mailing_list' : 'false',
        'utc' : 'true',
        'year' : '2010',
        'name' : 'Stu+Baxley'
    }

    if '.csv' in BASE_URL:
        info = [
                f"wkt=POINT({location.longitude}%20{location.latitude})",
                f"names={input_data['year']}",
                "leap_day=false",
                f"interval={input_data['interval']}",
                f"utc={input_data['utc']}",
                f"full_name'={input_data['name']}",
                f"email={input_data['email']}",
                f"api_key={API_KEY}",
                "affiliation=myself",
                "mailing_list=false",
                f"attributes={input_data['attributes']}"
               ]

        url = BASE_URL + '&'.join(info)
        # some error handling would be nice...
        data = pd.read_csv(url)
        data = data.to_csv(index=False)
    else:
        raise Exception("Only CSV supported at this time...")
    return data


def get_response_json_and_handle_errors(response: requests.Response) -> dict:
    if response.status_code != 200:
        print(f"An error has occurred with the server or the request. The request response code/status: {response.status_code} {response.reason}")
        print(f"The response body: {response.text}")
        exit(1)

    try:
        response_json = response.json()
    except:
        print(f"The response couldn't be parsed as JSON, likely an issue with the server, here is the text: {response.text}")
        exit(1)

    if len(response_json['errors']) > 0:
        errors = '\n'.join(response_json['errors'])
        print(f"The request errored out, here are the errors: {errors}")
        exit(1)
    return response_json


if __name__ == "__main__":
    opts = parse_args()

    location = pvlib.location.Location(opts.latitude, opts.longitude, altitude=opts.altitude, name="tmy")
    data = pull_nsrdb_data(location)
