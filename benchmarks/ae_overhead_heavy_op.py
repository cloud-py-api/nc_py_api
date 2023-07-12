import sys
from io import BytesIO
from pathlib import Path
from random import randbytes
from time import perf_counter

import matplotlib.pyplot as plt
from conf import NC_CFGS, init_nc, init_nc_app
from cpuinfo import get_cpu_info

USER_NAME = "admin"


if __name__ == "__main__":
    nc_versions = []
    results_medium_file_upload_chunked = []
    results_medium_file_upload_chunked_ae = []
    results_medium_file_download_stream = []
    results_medium_file_download_stream_ae = []
    for nextcloud_url, v in NC_CFGS.items():
        nc = init_nc(nextcloud_url, v)
        nc_app = init_nc_app(nextcloud_url, v)

        nc_versions.append(nc.srv_version["string"] if nc else nc_app.srv_version["string"])

        medium_file_name = "100Mb.bin"
        # First benchmark, medium file(1mb) upload
        medium_file = BytesIO()
        medium_file.write(randbytes(100 * 1024 * 1024))
        n_iter = 10
        if nc:
            start_time = perf_counter()
            for i in range(n_iter):
                medium_file.seek(0)
                nc.files.upload_stream(medium_file_name, medium_file)
            end_time = perf_counter()
            results_medium_file_upload_chunked.append((end_time - start_time) / n_iter)
        if nc_app:
            start_time = perf_counter()
            for i in range(n_iter):
                medium_file.seek(0)
                nc_app.files.upload_stream(medium_file_name, medium_file)
            end_time = perf_counter()
            results_medium_file_upload_chunked_ae.append((end_time - start_time) / n_iter)

        # Second benchmark, medium file(1mb) download
        n_iter = 10
        if nc:
            start_time = perf_counter()
            for i in range(n_iter):
                buf = BytesIO()
                nc.files.download2stream(medium_file_name, buf)
            end_time = perf_counter()
            results_medium_file_download_stream.append((end_time - start_time) / n_iter)
        if nc_app:
            start_time = perf_counter()
            for i in range(n_iter):
                buf = BytesIO()
                nc_app.files.download2stream(medium_file_name, buf)
            end_time = perf_counter()
            results_medium_file_download_stream_ae.append((end_time - start_time) / n_iter)

    fig, ax = plt.subplots()
    ax.plot(nc_versions, results_medium_file_upload_chunked, label="upload chunked 100Mb file")
    ax.plot(nc_versions, results_medium_file_upload_chunked_ae, label="upload chunked 100Mb file(AE)")
    ax.plot(nc_versions, results_medium_file_download_stream, label="download stream 100Mb file")
    ax.plot(nc_versions, results_medium_file_download_stream_ae, label="download stream 100Mb file(AE)")
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
