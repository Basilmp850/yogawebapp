#!/bin/bash
# Install dependencies
apt-get update
apt-get install -y xvfb libfontconfig wkhtmltopdf

# Set up a virtual display
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
export DISPLAY=:99

# Test the installation
wkhtmltopdf --version
