import datetime
import requests


class NOAAModel(object):

    def __init__(self, name, description, bottom_left, top_right, loc_res, time_res, max_alt=0.0, min_alt=0.0, alt_res=0.0):
        self.name = name
        self.description = description
        self.bottom_left = bottom_left
        self.top_right = top_right
        self.max_altitude = max_alt
        self.min_altitude = min_alt
        self.altitude_resolution = alt_res
        self.location_resolution = loc_res
        self.time_resolution = time_res

    @property
    def time_resolution_hours(self):
        return self.time_resolution * 24.0

    def contains_location(self, location):
        if location.latitude > self.bottom_left.latitude and location.latitude < self.top_right.latitude:
            if location.longitude > self.bottom_left.longitude and location.longitude < self.top_right.longitude:
                return True
        return False

    def location_index(self, location):
        if not self.contains_location(location):
            return -1, -1

        lat_offset = location.latitude - self.bottom_left.latitude
        lon_offset = location.longitude - self.bottom_left.longitude

        lat_index = int(lat_offset / self.location_resolution)
        lon_index = int(lon_offset / self.location_resolution)
        return lat_index, lon_index

    def altitude_index(self, altitude):
        if altitude > self.max_altitude or altitude < self.min_altitude:
            return -1

        return int(altitude / self.altitude_resolution)

    def latest_model_time(self):
        current_time = datetime.datetime.utcnow() + datetime.timedelta(hours=-5)
        latest_model_hour = current_time.hour - (current_time.hour % 6)
        current_time = current_time + datetime.timedelta(hours=-(current_time.hour-latest_model_hour))
        current_time = datetime.datetime(current_time.year, current_time.month, current_time.day, current_time.hour, 0)
        return current_time

    def time_index(self, desired_time):
        model_time = self.latest_model_time()
        diff = (desired_time - model_time).days * 24.0
        if diff < 1:
            return -1
        hours_res = self.time_resolution_hours
        return (diff + (hours_res - (diff % hours_res))) / hours_res

    def create_ascii_url(self, location, start_time_index, end_time_index):
        return ''

    def fetch_ascii_data(self, location, start_time_index, end_time_index):
        url = self.create_ascii_url(location, start_time_index, end_time_index)
        if len(url) < 1:
            return False

        response = requests.get(url)
        if not len(response.text):
            return False
        return self.parse_ascii_data(response.text)

    def parse_ascii_data(self, raw_data):
        if len(raw_data) < 1:
            return False

        split_data = raw_data.split('\n')

        self.data = {}
        current_var = ''

        for value in split_data:
            if len(value) < 1:
                continue
            elif value[0] == '[':
                datas = value.split(',')
                self.data[current_var].append(float(datas[1].strip()))
            elif value[0] >= '0' and value[0] <= '9':
                raw_timestamps = value.split(',')
                for timestamp in raw_timestamps:
                    self.data[current_var].append(float(timestamp.strip()))
            else:
                vars = value.split(',')
                current_var = vars[0]
                self.data[current_var] = []

        return True