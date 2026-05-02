#!/bin/bash

# Start the background guard
python3 guard.py &

# Start the web bait
python3 bait.py
