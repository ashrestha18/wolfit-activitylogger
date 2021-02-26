#!/bin/bash
export WOLFIT_SETTINGS=$(pwd)/dev.settings
flask db upgrade
python load_reddit_posts.py
gunicorn app:app