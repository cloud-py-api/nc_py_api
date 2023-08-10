import re
from sys import argv
from time import sleep

from requests import get


def check_heartbeat(url: str, regexp: str, n_tries: int, wait_interval: float) -> int:
    for _ in range(n_tries):
        try:
            result = get(url)
            if result.text:
                if re.search(regexp, result.text, re.IGNORECASE) is not None:
                    return 0
        except Exception as _:
            _ = _
        sleep(wait_interval)
    return 2


# params: app heartbeat url, string to check, number of tries, time to sleep between retries
if __name__ == "__main__":
    r = check_heartbeat(str(argv[1]), str(argv[2]), int(argv[3]), float(argv[4]))
    exit(r)
