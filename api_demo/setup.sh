_URL="https://raw.githubusercontent.com/nextcloud/server/master/apps/files_sharing/openapi.json"
_FILE="openapi.json"
_RET=0

echo -e "\e[1;32m1. Downloading\e[0m"
wget -q "$_URL" -O "$_FILE"
_RET=$(($_RET+$?))

echo -e "\e[1;32m2. Adjusting OpenAPI\e[0m"
sed -i "s#application/json#text/plain#g" "$_FILE"
_RET=$(($_RET+$?))

echo -e "\e[1;32m3. Installing requirements\e[0m"
pip install -r requirements.txt

echo -e "\e[1;32m4. Generating\e[0m"
if [ -d "files-sharing-client" ];
    then
        openapi-python-client update --path $_FILE
    else
        openapi-python-client generate --path $_FILE
fi
_RET=$(($_RET+$?))

echo -e "\e[1;32m5. Preparing\e[0m"
cp -v "main.py" "files-sharing-client/main.py"
_RET=$(($_RET+$?))

if [ "$_RET" -eq 0 ];
    then
        echo -e "\e[0;44m,--------\e[0m"
        echo -e "\e[0;44m\e[1;37mSetup\e[0m\t\e[1;32mDone\e[0m"
        echo -e "\e[0;44m\`--------\e[0m"
    else
        echo -e "\e[0;41m,--------\e[0m"
        echo -e "\e[0;41m\e[1;37mSetup\e[0m\t\e[1;31mError\e[0m"
        echo -e "\e[0;41m\`--------\e[0m"
fi
