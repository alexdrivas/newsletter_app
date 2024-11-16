#!/bin/bash

# Activate the virtual environment
source /Users/alexandrosdrivas/Documents/Code\ Projects/venv-newsletter-app/bin/activate

curl -X POST http://localhost:5000/send_email_to_first_user

# Dectivate the virtual environment
deactivate
