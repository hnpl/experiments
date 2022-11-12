import json
from pathlib import Path

class Config:
    # Allowed types. So far, we only support conversion from these types.
    available_types = {"int", "float", "string", "boolean", "path"}

    def __init__(self, from_json_file=None):
        if not from_json_file == None:
            self.init_from_json_file(from_json_file)
    
    # Convert a string to an object of a type specified by the input
    # . If the type is path, the string will be converted to the absolute path
    # . Note that: this is a choice of using pathlib.Path.absolute() rather than pathlib.Path.resolve()
    # as absolute() only prepends the absolute path to the relative path, and thus, the symlinks are
    # unsolved. In constrast, resolve() will resolve symlinks.
    def _convert_to_type(self, val, _type):
        converter = {"int": int, "float": float, "string": str, "boolean": bool, "path": Path}
        converted_val = converter[_type](val)
        if _type == "path":
            converted_val = converted_val.absolute()
        return converted_val

    # Read a json file and construct an object with attributes specified by the json file.
    # The json file should of the following format,
    # ```json
    # {
    #     "key1": {
    #         "type": "int",
    #         "value": "5"
    #     },
    #     "key2": {
    #         "type": "path",
    #         "value": "build/binaries/"
    #     }
    #     ...
    # ```
    def init_from_json_file(self, filepath):
        content = None
        with open(filepath, "r") as f:
            content = json.load(f)
            for key, val in content.items():
                assert(val["type"] in Config.available_types)
                val = self._convert_to_type(val["value"], val["type"])
                self.__dict__[key] = val
