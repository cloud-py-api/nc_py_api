import sys

import matplotlib.pyplot as plt
import numpy as np
from conf import NC_CFGS, init_nc, init_nc_app, init_nc_by_app_pass

NC_VERSIONS = []


def measure_overhead(measure, title: str):
    penguin_means = {
        "Password": [],
        "AppPassword": [],
        "AppAPI": [],
    }

    for k, v in NC_CFGS.items():
        NC_VERSIONS.append(init_nc_app(k, v).srv_version["string"])

    for k, v in NC_CFGS.items():
        nc = init_nc(k, v)
        if nc:
            result_nc, time_nc = measure(nc)
            penguin_means["Password"].append(time_nc)
        else:
            penguin_means["Password"].append(0)

        nc_ap = init_nc_by_app_pass(k, v)
        if nc_ap:
            result_nc_ap, time_nc_ap = measure(nc_ap)
            penguin_means["AppPassword"].append(time_nc_ap)
        else:
            penguin_means["AppPassword"].append(0)

        nc_ae = init_nc_app(k, v)
        result_nc_ae, time_nc_ae = measure(nc_ae)
        penguin_means["AppAPI"].append(time_nc_ae)

        # Uncomment only for functions that return predictable values.
        # if result_nc is not None:
        #     assert result_nc == result_nc_ae
        # if result_nc_ap is not None:
        #     assert result_nc_ap == result_nc_ae

    penguin_means = {k: v for k, v in penguin_means.items() if v}

    x = np.arange(len(NC_VERSIONS))  # the label locations
    width = 0.25  # the width of the bars
    multiplier = 0

    fig, ax = plt.subplots(layout="constrained")

    for attribute, measurement in penguin_means.items():
        offset = width * multiplier
        rects = ax.bar(x + offset, measurement, width, label=attribute)
        ax.bar_label(rects, padding=3)
        multiplier += 1

    ax.set_ylabel("Time to execute")
    ax.set_title(title)
    ax.set_xticks(x + width, NC_VERSIONS)
    ax.legend(loc="upper left", ncols=3)
    values = []
    for v in penguin_means.values():
        values.append(max(v))
    ax.set_ylim(0, max(values) + 0.18 * max(values))


def os_id():
    if sys.platform.lower() == "darwin":
        return "macOS"
    elif sys.platform.lower() == "win32":
        return "Windows"
    return "Linux"
