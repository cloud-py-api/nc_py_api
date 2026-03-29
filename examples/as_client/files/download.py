import asyncio
from io import BytesIO

from PIL import Image  # this example requires `pillow` to be installed

import nc_py_api


async def main():
    # run this example after ``files_upload.py`` or adjust the image file path.
    nc = nc_py_api.AsyncNextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")
    rgb_image = await nc.files.download("RGB.png")
    Image.open(BytesIO(rgb_image)).show()  # wrap `bytes` into BytesIO for Pillow


if __name__ == "__main__":
    asyncio.run(main())
