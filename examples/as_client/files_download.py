from io import BytesIO

from PIL import Image  # this example requires `pillow` to be installed

import nc_py_api

if __name__ == "__main__":
    # run this example after ``files_upload.py`` or adjust the image file path.
    nc = nc_py_api.Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")
    rgb_image = nc.files.download("RGB.png")
    Image.open(BytesIO(rgb_image)).show()  # wrap `bytes` into BytesIO for Pillow
    exit(0)
