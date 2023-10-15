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


API_KEY = "FhVfzpADNNmu6UUyNaXRCZYI5bZyOjFkb3OWQNmx"
EMAIL = "stuart.baxley@gmail.com"
#BASE_URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-2-2-tmy-download.csv?"
#BASE_URL = "https://developer.nrel.gov/api/solar/nsrdb_data_query.csv?"
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
        #url = BASE_URL + urllib.parse.urlencode(input_data, True)+f"&wkt=POINTS({location.latitude} {location.longitude})"
        #url = BASE_URL + f"api_key={API_KEY}&wkt=POINT(91.287 23.832)"
        print(url)
        try:
            data = pd.read_csv(url)#, index_col=False)
        except:
            return input_data
        data = data.to_csv(index=False)
    else:
        headers = {
            'x-api-key': API_KEY
        }
        data = get_response_json_and_handle_errors(requests.post(BASE_URL, input_data, headers=headers))
        download_url = data['outputs']['downloadUrl']
        # You can do with what you will the download url
        print(data['outputs']['message'])
        print(f"Data can be downloaded from this url when ready: {download_url}")

        # Delay for 1 second to prevent rate limiting
        time.sleep(1)
    print(f'Processed')
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
