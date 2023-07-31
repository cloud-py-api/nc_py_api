import re
from sys import argv
from time import sleep

from requests import get

# params: app heartbeat url, string to check, number of tries, time to sleep between retries
if __name__ == "__main__":
    for _ in range(int(argv[3])):
        try:
            result = get(argv[1])
            if result.text:
                if re.search(str(argv[2]), result.text, re.IGNORECASE) is not None:
                    exit(0)
        except Exception as _:
            _ = _
        sleep(float(argv[4]))
    exit(2)
