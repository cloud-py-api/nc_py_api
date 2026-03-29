import asyncio

import nc_py_api


async def main():
    # create Nextcloud client instance class
    nc = nc_py_api.AsyncNextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")

    print("Searching for all files which names ends with `.txt`:")
    result = await nc.files.find(["like", "name", "%.txt"])
    for i in result:
        print(i)
    print("")
    print("Searching for all files which name is equal to `Nextcloud_Server_Administration_Manual.pdf`:")
    result = await nc.files.find(["eq", "name", "Nextcloud_Server_Administration_Manual.pdf"])
    for i in result:
        print(i)


if __name__ == "__main__":
    asyncio.run(main())
