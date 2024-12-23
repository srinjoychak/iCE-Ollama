#!/bin/bash
echo "starting script"
rasa run --enable-api &
rasa run actions &
python3 webexconnect.py &
python3 Schedule.py
