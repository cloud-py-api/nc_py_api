import hmac
from datetime import datetime, timezone
from hashlib import sha256
from json import dumps
from os import environ
from sys import argv

import requests
from xxhash import xxh64


def sign_request(url: str, req_headers: dict, time: int = 0):
    data_hash = xxh64()
    req_headers["AE-DATA-HASH"] = data_hash.hexdigest()
    if time:
        req_headers["AE-SIGN-TIME"] = str(time)
    else:
        req_headers["AE-SIGN-TIME"] = str(int(datetime.now(timezone.utc).timestamp()))
    req_headers.pop("AE-SIGNATURE", None)
    request_to_sign = "PUT" + url + dumps(req_headers, separators=(",", ":"))
    hmac_sign = hmac.new(environ["APP_SECRET"].encode("UTF-8"), request_to_sign.encode("UTF-8"), digestmod=sha256)
    req_headers["AE-SIGNATURE"] = hmac_sign.hexdigest()


# params: app base url
if __name__ == "__main__":
    request_url = argv[1] + "/enabled?enabled=1"
    headers = {}
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 401  # Missing headers
    headers.update(
        {
            "AE-VERSION": "1.0.0",
            "EX-APP-ID": "nc_py_api",
            "EX-APP-VERSION": "1.0.0",
        }
    )
    sign_request("/enabled?enabled=1", headers)
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 200
    # Invalid AE-SIGNATURE
    request_url = argv[1] + "/enabled?enabled=0"
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 401
    sign_request("/enabled?enabled=0", headers)
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 200
    # Invalid EX-APP-ID
    old_app_name = headers["EX-APP-ID"]
    headers["EX-APP-ID"] = "unknown_app"
    sign_request("/enabled?enabled=0", headers)
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 401
    headers["EX-APP-ID"] = old_app_name
    sign_request("/enabled?enabled=0", headers)
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 200
    # Invalid AE-DATA-HASH
    _ = xxh64()
    _.update(b"some_data")
    headers["AE-DATA-HASH"] = _.hexdigest()
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 401
    _ = xxh64()
    _.update(b"")
    headers["AE-DATA-HASH"] = _.hexdigest()
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 200
    # Sign time
    sign_request("/enabled?enabled=0", headers, time=int(datetime.now(timezone.utc).timestamp()))
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 200
    sign_request("/enabled?enabled=0", headers, time=int(datetime.now(timezone.utc).timestamp() - 4.0 * 60))
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 200
    sign_request("/enabled?enabled=0", headers, time=int(datetime.now(timezone.utc).timestamp() - 5.0 * 60 - 1.0))
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 401
    sign_request("/enabled?enabled=0", headers, time=int(datetime.now(timezone.utc).timestamp() + 4.0 * 60))
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 200
    sign_request("/enabled?enabled=0", headers, time=int(datetime.now(timezone.utc).timestamp() + 5.0 * 60 + 1.0))
    result = requests.put(request_url, headers=headers)
    assert result.status_code == 401
