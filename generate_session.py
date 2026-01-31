#!/usr/bin/env python3
from pyrogram import Client

API_ID = int(input("Enter API_ID: "))
API_HASH = input("Enter API_HASH: ")

with Client("assistant", api_id=API_ID, api_hash=API_HASH) as app:
    print("\n✅ Session String:\n")
    print(app.export_session_string())
    print("\nCopy this to your .env file!\n")
