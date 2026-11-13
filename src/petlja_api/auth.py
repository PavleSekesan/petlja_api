from getpass import getpass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .urls import ARENA_URL, CPANEL_URL, IDENTITY_URL


def _get_credentials():
    username = input("Petlja username: ")
    password = getpass("Petlja password: ")
    return username, password


def get_csrf_token(page):
    soup = BeautifulSoup(page, "html.parser")
    token = soup.find("input", {"name": "__RequestVerificationToken"})
    return token["value"]


def _login_form(page):
    password = BeautifulSoup(page.text, "html.parser").find(
        "input", {"name": "Password"}
    )
    return password.find_parent("form") if password is not None else None


def _check_signin(page):
    """Check the response after sign-in redirects have completed."""
    page.raise_for_status()
    if _login_form(page) is not None:
        raise PermissionError("Petlja login failed: check username and password")


def login(username=None, password=None):
    if username is None or password is None:
        username, password = _get_credentials()

    session = requests.Session()
    try:
        page = session.get(IDENTITY_URL)
        page.raise_for_status()
        form = _login_form(page)
        target = urljoin(page.url, form.get("action", ""))
        fields = {
            "UserNameOrEmail": username,
            "Password": password,
            "RememberMe": "false",
            "__RequestVerificationToken": get_csrf_token(str(form)),
        }
        page = session.post(target, data=fields)
        _check_signin(page)

        # Use the identity session to establish each site's own login cookies.
        page = session.get(CPANEL_URL)
        _check_signin(page)
        page = session.get(f"{ARENA_URL}/sr-Latn-RS/Account/Login")
        _check_signin(page)

        return session
    except Exception:
        session.close()
        raise
