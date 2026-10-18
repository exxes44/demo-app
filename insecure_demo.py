import hashlib
import ipaddress
import json
import os
import re
import secrets
import sqlite3
import subprocess
from contextlib import closing

import requests
import yaml

DB_PASSWORD = os.environ["DB_PASSWORD"]


def get_user(username):
    with closing(sqlite3.connect("app.db")) as conn:
        return conn.execute(
            "SELECT * FROM users WHERE name = ?", (username,)
        ).fetchall()


def ping(host):
    if not isinstance(host, str) or not host or "%" in host:
        raise ValueError("Expected an IP address or a DNS hostname")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        labels = host.removesuffix(".").split(".")
        if len(host) > 253 or not all(
            re.fullmatch(r"(?!-)[A-Za-z0-9-]{1,63}(?<!-)", label)
            for label in labels
        ):
            raise ValueError("Expected an IP address or a DNS hostname") from None
    return subprocess.run(["ping", "-c", "1", host], check=False, timeout=10)


def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return salt, digest


def make_reset_token():
    return secrets.token_urlsafe(32)


def load_config(text):
    return yaml.safe_load(text)


def load_session(data):
    """Read JSON data only; unlike pickle, this format cannot invoke Python code."""
    return json.loads(data)


def fetch(url):
    return requests.get(url, timeout=10)
