from base64 import b64encode
from os import environ
from sys import argv

import requests


def sign_request(req_headers: dict, secret=None, user: str = ""):
    app_secret = secret if secret is not None else environ["APP_SECRET"]
    req_headers["AUTHORIZATION-APP-API"] = b64encode(f"{user}:{app_secret}".encode("UTF=8"))


# params: app base url
if __name__ == "__main__":
    request_url = argv[1] + "/sec_check?value=1"
    headers = {}
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 401  # Missing headers
    headers.update({
        "AA-VERSION": environ.get("AA_VERSION", "1.0.0"),
        "EX-APP-ID": environ.get("APP_ID", "nc_py_api"),
        "EX-APP-VERSION": environ.get("APP_VERSION", "1.0.0"),
    })
    sign_request(headers)
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 200
    # Invalid AA-SIGNATURE
    sign_request(headers, secret="xxx")
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 401
    sign_request(headers)
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 200
    # Invalid EX-APP-ID
    old_app_name = headers["EX-APP-ID"]
    headers["EX-APP-ID"] = "unknown_app"
    sign_request(headers)
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 401
    headers["EX-APP-ID"] = old_app_name
    sign_request(headers)
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 200
    # Invalid EX-APP-VERSION
    sign_request(headers)
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 200
    old_version = headers["EX-APP-VERSION"]
    headers["EX-APP-VERSION"] = "999.0.0"
    sign_request(headers)
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 401
    headers["EX-APP-VERSION"] = old_version
    sign_request(headers)
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 200
