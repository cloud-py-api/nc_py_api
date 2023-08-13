import nc_py_api

if __name__ == "__main__":
    # create Nextcloud client instance class
    nc = nc_py_api.Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")

    def list_dir(directory):
        # usual recursive traversing over directories
        for node in nc.files.listdir(directory):
            if node.is_dir:
                list_dir(node)
            else:
                print(f"{node.user_path}")

    print("Files on the instance for the selected user:")
    list_dir("")
    exit(0)
