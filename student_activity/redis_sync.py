import json

import redis
import zlib
from student_activity.settings import REDIS_HOST, REDIS_PORT, REDIS_DB


class RedisSync:
    """
    Created this class to store aggregate data points of mongo to redis.
    """
    def __init__(self, name_space):
        self.host = REDIS_HOST
        self.port = REDIS_PORT
        self.db = REDIS_DB
        self.name_space = name_space

    @staticmethod
    def compress_data(data):
        """
        This method serialize given data in json format and then after compress the that data.
        """
        serializer = lambda x: json.dumps(x)

        # Below code compress given value using zlib
        compressor = lambda x: zlib.compress(serializer(x).encode('utf-8'))

        # Compress direct if data is not dict
        if not isinstance(data, dict):
            return compressor(data)

        for key, value in data.items():
            data[key] = compressor(value)

        return data

    @staticmethod
    def decompress_data(data):
        """
        This method decompress given data
        """
        if data:
            return zlib.decompress(data).decode('utf-8')
        return

    def upload_data(self, name=None, key=None, value=None, mapping=None, compress=True, **kwargs):
        name = name or self.name_space
        try:
            # Compress given data
            mapping = mapping and self.compress_data(mapping)
            
            if compress:
                value = self.compress_data(value)
            with redis.Redis(self.host, self.port, self.db) as connection:
                if kwargs.get('force_update'):
                    self.flush_data()
                connection.hset(name, key, value, mapping)
        except Exception as e:
            print(e)

    def get_specific_values(self, keys):
        """
        This method return all the hash value of given name space id.
        """
        name = self.name_space

        with redis.Redis(self.host, self.port, self.db) as connection:
            data = connection.hmget(name=name, keys=keys)
        data = list(map(lambda a: self.decompress_data(a), data))
        return data

    def get_data(self, key, decompress=True):
        name = self.name_space
        with redis.Redis(self.host, self.port, self.db) as connection:
            data = connection.hget(name, key)
            if not data:
                return None
        if decompress:
            data = json.loads(self.decompress_data(data))
        return data

    def flush_data(self):
        name = self.name_space
        with redis.Redis(self.host, self.port, self.db) as connection:
            if record_ids := connection.hkeys(name):
                connection.hdel(name, *record_ids)

    def delete_data(self, key):
        name = self.name_space
        with redis.Redis(self.host, self.port, self.db) as connection:
            connection.hdel(name, key)

    def get_all_values(self):
        name = self.name_space
        with redis.Redis(self.host, self.port, self.db) as connection:
            data = connection.hvals(name)
        data = list(map(lambda a: self.decompress_data(a), data))
        return data

    def get_all_keys(self):
        name = self.name_space
        with redis.Redis(self.host, self.port, self.db) as connection:
            data = connection.hkeys(name)
        return data


student_element_wise_time_sync = RedisSync(name_space="student_element_wise_time_sync")
student_total_points_sync = RedisSync(name_space="student_total_points_sync")
student_total_diamond_sync = RedisSync(name_space="student_total_diamond_sync")


