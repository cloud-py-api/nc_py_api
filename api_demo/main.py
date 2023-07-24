import sys
import json
import base64
import xmltodict

from json import JSONDecodeError
from files_sharing_client.api.shareapi import shareapi_create_share, shareapi_get_share, shareapi_update_share, shareapi_delete_share
from files_sharing_client.client import Client

# Configuration
host = "HOST_URL"
username = "USERNAME"
password = "PASSWORD"
demo_file = "demo_image.jpg"

user_pass = f"{username}:{password}"

# Base64 encode the string
user_pass_b64 = base64.b64encode(user_pass.encode()).decode()

# Create the header dictionary
headers = {"Authorization": f"Basic {user_pass_b64}"}

# Erstellen Sie eine Instanz des AuthenticatedClient
auth_client = Client(base_url=host, headers=headers, verify_ssl=False)

# Create public share on a file
print("\033[1;36mCreate public share\033[0m")

try:
    response = shareapi_create_share.sync_detailed(
        client=auth_client, path="/"+str(demo_file), share_type=3, public_upload=False, label="Demo Share"
    )
    print("\033[1;33mContent Type:\033[0m", response.headers.get("Content-Type"))
    print("\033[1;33mStatus Code:\033[0m", response.status_code)
    print("\033[1;33mHeaders:\033[0m", response.headers)
    print("\033[1;33mContent:\033[0m", response.content.decode())
    data_dict = xmltodict.parse(response.content.decode())
except JSONDecodeError:
    pass

try:
    new_id = int(data_dict['ocs']['data']['id'])
    print("\033[1;32m[ Created ]\033[0m", "Created new share with ID", int(new_id))
except Exception as e:
    print("\033[1;31m[ ERROR ]\[033[0m", str(e))
    sys.exit(1)
print()

# Update the public share
print("\033[1;36mUpdate the public share\033[0m", new_id)
try:
    response = shareapi_update_share.sync_detailed(client=auth_client, note="Updated the share", id=new_id)
    print("\033[1;33mContent Type:\033[0m", response.headers.get("Content-Type"))
    print("\033[1;33mStatus Code:\033[0m", response.status_code)
    print("\033[1;33mHeaders:\033[0m", response.headers)
    print("\033[1;33mContent:\033[0m", response.content.decode())
except JSONDecodeError:
    pass
print()

# Get the share information
print("\033[1;36mGet the share information\033[0m", new_id)
try:
    response = shareapi_get_share.sync_detailed(client=auth_client, id=new_id)
    print("\033[1;33mContent Type:\033[0m", response.headers.get("Content-Type"))
    print("\033[1;33mStatus Code:\033[0m", response.status_code)
    print("\033[1;33mHeaders:\033[0m", response.headers)
    print("\033[1;33mContent:\033[0m", response.content.decode())
except JSONDecodeError:
    pass
print()
