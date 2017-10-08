"""
json serialization helpers
"""
import json

class Serializable:

    def __repr__(self):
        return json.dumps(self.__dict__)

    def to_json_str(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    def from_json_str(self, string_data):
        self = json.loads(string_data)
