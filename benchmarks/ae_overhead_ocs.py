from getpass import getuser
from time import perf_counter
from typing import Any, Union

import matplotlib.pyplot as plt
from ae_overhead_common import measure_overhead, os_id

from nc_py_api import Nextcloud, NextcloudApp

ITERS = 100
CACHE_SESS = True


def measure_get_details(nc_obj: Union[Nextcloud, NextcloudApp]) -> [Any, float]:
    __result = None
    start_time = perf_counter()
    for _ in range(ITERS):
        __result = nc_obj.users.get_details()
        nc_obj._session.init_adapter(restart=not CACHE_SESS)  # noqa
    end_time = perf_counter()
    return __result, round((end_time - start_time) / ITERS, 3)


if __name__ == "__main__":
    title = f"OCS: get_user, {ITERS} iters, CACHE={CACHE_SESS} - {os_id()}"
    measure_overhead(measure_get_details, title)
    plt.savefig(f"results/ocs_user_get_details__cache{int(CACHE_SESS)}_iters{ITERS}__{getuser()}.png", dpi=200)
