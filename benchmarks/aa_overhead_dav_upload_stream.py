from getpass import getuser
from io import BytesIO
from random import randbytes
from time import perf_counter
from typing import Any

import matplotlib.pyplot as plt
from aa_overhead_common import measure_overhead, os_id

from nc_py_api import Nextcloud, NextcloudApp

ITERS = 10
CACHE_SESS = False


def measure_upload_100mb(nc_obj: Nextcloud | NextcloudApp) -> [Any, float]:
    __result = None
    medium_file_name = "100Mb.bin"
    medium_file = BytesIO()
    medium_file.write(randbytes(100 * 1024 * 1024))
    start_time = perf_counter()
    for _ in range(ITERS):
        medium_file.seek(0)
        nc_obj.files.upload_stream(medium_file_name, medium_file)
        nc_obj._session.init_adapter_dav(restart=not CACHE_SESS)  # noqa
    end_time = perf_counter()
    nc_obj.files.delete(medium_file_name, not_fail=True)
    return __result, round((end_time - start_time) / ITERS, 3)


if __name__ == "__main__":
    title = f"upload stream 100mb, {ITERS} iters, CACHE={CACHE_SESS} - {os_id()}"
    measure_overhead(measure_upload_100mb, title)
    plt.savefig(f"results/dav_upload_stream_100mb__cache{int(CACHE_SESS)}_iters{ITERS}__{getuser()}.png", dpi=200)
