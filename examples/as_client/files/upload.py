import asyncio
from io import BytesIO

from PIL import Image  # this example requires `pillow` to be installed

import nc_py_api


async def main():
    nc = nc_py_api.AsyncNextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")
    buf = BytesIO()
    Image.merge(
        "RGB",
        [
            Image.linear_gradient(mode="L"),
            Image.linear_gradient(mode="L").transpose(Image.ROTATE_90),
            Image.linear_gradient(mode="L").transpose(Image.ROTATE_180),
        ],
    ).save(
        buf, format="PNG"
    )  # saving image to the buffer
    buf.seek(0)  # setting the pointer to the start of buffer
    await nc.files.upload_stream("RGB.png", buf)  # uploading file from the memory to the user's root folder


if __name__ == "__main__":
    asyncio.run(main())
