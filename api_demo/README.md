
# Setup



You've got two options to install it

1.) Automaticaly:
- bash setup.sh
2.) Manually (just execute each step after each other):
- wget -O "openapi.json" "https://raw.githubusercontent.com/nextcloud/server/master/apps/files_sharing/openapi.json"
- sed -i "s#application/json#text/plain#g" "openapi.json"
- pip install -r requirements.txt
- openapi-python-client generate --path "openapi.json"
- cp -v "main.py" "files-sharing-client/main.py"

Execute the requests (It creates a share on demo_image.jpg, updates the note of the share and gets the information for the created share):
- cd files-sharing-client/
- Adjust the variables host, username, password and demo_file in main.py 
- python3 main.py
