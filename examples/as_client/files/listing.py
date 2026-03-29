import asyncio

import nc_py_api


async def main():
    # create Nextcloud client instance class
    nc = nc_py_api.AsyncNextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")

    async def list_dir(directory):
        # usual recursive traversing over directories
        for node in await nc.files.listdir(directory):
            if node.is_dir:
                await list_dir(node)
            else:
                print(f"{node.user_path}")

    print("Files on the instance for the selected user:")
    await list_dir("")


if __name__ == "__main__":
    asyncio.run(main())
