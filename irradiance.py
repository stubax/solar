#!/usr/bin/env python

import argparse
import datetime
import matplotlib.pyplot as plt
import pandas as pd

import pvlib
from pvlib.pvsystem import PVSystem, Array, FixedMount
from pvlib.modelchain import ModelChain

from user_cfg import config


def parse_args ():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--filepath", dest="filepath", type=str, default="./",
                        help = "Filepath for output")
    parser.add_argument("--year", dest="year", type=str,
                        help = "The year for which to pull data")
    parser.add_argument("--api-key", dest="api_key", type=str, default=None,
                        help = "User's API key from NSRDB")
    parser.add_argument("--email", dest="email", type=str, default=None,
                        help = "User's email address, associated with NSRDB API key")
    parser.add_argument("--latitude", dest="latitude", type=float,
                        help = "latitude of location")
    parser.add_argument("--longitude", dest="longitude", type=float,
                        help = "longitude of location")
    parser.add_argument("--altitude", dest="altitude", type=float, default=None,
                        help = "longitude of location")
#    parser.add_argument("--place_holder", dest="place_holder", action="store_true", default=False,
#                        help = "Boolean syntax placeholder")
    return parser.parse_args()


API_KEY = config["API_KEY"]
EMAIL = config["EMAIL"]
USERNAME = config["NAME"]
BASE_URL = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-download.csv?"


def pull_nsrdb_data(location, year = None):
    if not year:
        raise Exception("Must include year")
    input_data = {
        'attributes': 'ghi,dhi,dni,wind_speed,air_temperature,solar_zenith_angle',
        'interval': '60',
        'wkt' : f'POINT({location.latitude} {location.longitude})',
        'api_key': API_KEY,
        'email': EMAIL,
        'mailing_list' : 'false',
        'utc' : 'true',
        'year' : year,
        'name' : USERNAME
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


def get_generic_components():
    sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
    module = sandia_modules['Canadian_Solar_CS5P_220M___2009_']
    sapm_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')
    inverter = sapm_inverters['ABB__MICRO_0_25_I_OUTD_US_208__208V_']
    temperature_model_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
    return inverter, module, temperature_model_parameters


def generic_pv_system():
    inverter, module, temperature_model_parameters = get_generic_components()

    mount = FixedMount(surface_tilt=location.latitude, surface_azimuth=180)
    array = Array(
            mount=mount,
            module_parameters=module,
            temperature_model_parameters=temperature_model_parameters,
        )
    return PVSystem(arrays=[array], inverter_parameters=inverter)


def run_energy_model(location, weather, pv_system):
    mc = ModelChain(pv_system, location)
    mc.run_model(weather)
    return mc


def get_file_lines(filename):
    with open(filename, "r") as f:
        lines = f.readlines()
    return lines


def tuple_to_datetime(time_tpl, tz=None):
    year, month, day, hour, minute = time_tpl
    dt = datetime.datetime(int(year), 
                           int(month), 
                           int(day), 
                           hour=int(hour), 
                           minute=int(minute), 
                           tzinfo=tz)
    return dt


def clean_data_row(data):
    data = data.split(",")
    clean_data = [tuple_to_datetime(tuple(data[0:5]))]
    dataline = []
    for datum in [x.strip() for x in data[5:]]:
        if datum:
            dataline.append(float(datum.strip()))
    clean_data.extend(dataline)
    return clean_data


def clean_column_names(old_cols, column_count=None):
    old_cols = old_cols.split(",")
    if not column_count:
        column_count = len(old_cols)
    column_names = ["timestamp"]
    column_names.extend([x.strip().lower() for x in old_cols[5:column_count+4]])
    return column_names


def csv_lines_to_df(lines):
    data = [clean_data_row(row) for row in lines[3:] if row]
    column_count = len(data[0])
    columns = clean_column_names(lines[2], column_count=column_count)

    data = pd.DataFrame(data, columns=columns)
    time_idx = pd.to_datetime(data.iloc[:,0].values, format='%Y%m%d:%H%M', utc=True)
    data = data.drop("timestamp", axis=1)
    data = pd.DataFrame(data, dtype=float)
    data.index = time_idx
    return data


def csv_file_to_df(filename):
    lines = get_file_lines(filename)
    return csv_lines_to_df(lines)


if __name__ == "__main__":
    opts = parse_args()

    location = pvlib.location.Location(opts.latitude, opts.longitude, altitude=opts.altitude, name="generic-name")
    data = pull_nsrdb_data(location, year="2020")

    #df = csv_file_to_df()
    weather = csv_lines_to_df(data.split("\n"))

    pv_system = generic_pv_system()

    irradiance_model = run_energy_model(location, weather, pv_system)
