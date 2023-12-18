from os import environ

from flask import Flask


def config(app: Flask):
    app.config["HDU_OA_CLIENT_ID"] = environ.get("HDU_OA_CLIENT_ID")
    app.config["HDU_OA_CLIENT_SECRET"] = environ.get("HDU_OA_CLIENT_SECRET")
    app.config["HDU_OA_REDIRECT_URI"] = environ.get("HDU_OA_REDIRECT_URI")
