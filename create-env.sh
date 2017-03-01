#!/bin/bash

mkdir ./www
mkdir ./www/static
mkdir ./www/media
rm -rf ./env
virtualenv -p python3 ./env
source ./env/bin/activate
pip install -r ./dep/requirements.txt
cp ./src/pjsite/settings.template.py ./src/pjsite/settings.py
cd src
printf "\n\nA virtual environment with the appropriate libraries has been installed\nPlease modify src/pjsite/settings.py then run:\n $ source env/bin/activate\n $ cd src\n $ python manage.py migrate\n\n\n"
