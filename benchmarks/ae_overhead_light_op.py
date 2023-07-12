import sys
from pathlib import Path
from random import randbytes
from time import perf_counter

import matplotlib.pyplot as plt
from conf import NC_CFGS, init_nc, init_nc_app
from cpuinfo import get_cpu_info

USER_NAME = "admin"


if __name__ == "__main__":
    nc_versions = []
    results_get_user = []
    results_get_user_ae = []
    results_small_file_upload = []
    results_small_file_upload_ae = []
    results_small_file_download = []
    results_small_file_download_ae = []
    for nextcloud_url, v in NC_CFGS.items():
        nc = init_nc(nextcloud_url, v)
        nc_app = init_nc_app(nextcloud_url, v)

        nc_versions.append(nc.srv_version["string"] if nc else nc_app.srv_version["string"])
        # First benchmark, OCS call
        n_iter = 100
        if nc:
            start_time = perf_counter()
            for i in range(n_iter):
                nc.users.get_details()
            end_time = perf_counter()
            results_get_user.append((end_time - start_time) / n_iter)
        if nc_app:
            start_time = perf_counter()
            for i in range(n_iter):
                nc_app.users.get_details()
            end_time = perf_counter()
            results_get_user_ae.append((end_time - start_time) / n_iter)

        small_file_name = "1Mb.bin"
        # Second benchmark, small file(1mb) upload
        small_file = randbytes(1024 * 1024)
        n_iter = 100
        if nc:
            start_time = perf_counter()
            for i in range(n_iter):
                nc.files.upload(small_file_name, small_file)
            end_time = perf_counter()
            results_small_file_upload.append((end_time - start_time) / n_iter)
        if nc_app:
            start_time = perf_counter()
            for i in range(n_iter):
                nc_app.files.upload(small_file_name, small_file)
            end_time = perf_counter()
            results_small_file_upload_ae.append((end_time - start_time) / n_iter)

        # Third benchmark, small file(1mb) download
        n_iter = 100
        if nc:
            start_time = perf_counter()
            for i in range(n_iter):
                nc.files.download(small_file_name)
            end_time = perf_counter()
            results_small_file_download.append((end_time - start_time) / n_iter)
        if nc_app:
            start_time = perf_counter()
            for i in range(n_iter):
                nc_app.files.download(small_file_name)
            end_time = perf_counter()
            results_small_file_download_ae.append((end_time - start_time) / n_iter)

    fig, ax = plt.subplots()
    ax.plot(nc_versions, results_get_user, label="get_user")
    ax.plot(nc_versions, results_get_user_ae, label="get_user(AE)")
    ax.plot(nc_versions, results_small_file_upload, label="upload 1Mb file")
    ax.plot(nc_versions, results_small_file_upload_ae, label="upload 1Mb file(AE)")
    ax.plot(nc_versions, results_small_file_download, label="download 1Mb file")
    ax.plot(nc_versions, results_small_file_download_ae, label="download 1Mb file(AE)")
    plt.ylabel("time to execute(s)")
    if sys.platform.lower() == "darwin":
        _os = "macOS"
    elif sys.platform.lower() == "win32":
        _os = "Windows"
    else:
        _os = "Linux"
    plt.xlabel(f"{_os} - {get_cpu_info()['brand_raw']}")
    ax.legend()
    plt.savefig(f"results/{Path(__file__).stem}_{_os}.png", dpi=200)
