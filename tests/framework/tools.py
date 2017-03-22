import os
import json


def get_file_dir():
    return os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),
            "../framework/files"
        )
    )


def get_user_data():
    dirname = get_file_dir()
    ret = {}
    for uname in ("clitester1a", "go"):
        with open(os.path.join(dirname,
                               uname + "@globusid.org.json")) as f:
            ret[uname] = json.load(f)
    return ret
