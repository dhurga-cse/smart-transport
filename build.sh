#!/bin/bash
cd smart_transport
pip install -r requirements.txt
python manage.py collectstatic --noinput
