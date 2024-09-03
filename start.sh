#!/bin/bash

export NICEBLOG_USER=username
export NICEBLOG_PASSWORD=password
export NICEBLOG_HEADER_NAME="NiceBLOG DEMO"
export NICEBLOG_HEADER_TITLE="A minimal blog engine, written in NiceGUI"
export NICEBLOG_STORAGE_SECRET="fgvhgcghfxhgydywery"
export NICEBLOG_LANGUAGE="de-DE"
export NICEBLOG_TIMEZONE="Europe/Berlin"

python3 main.py
