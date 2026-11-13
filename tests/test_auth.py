import pytest

import petlja_api as petlja
from petlja_api.urls import ARENA_URL, PETLJA_URL


def test_login_success(sess):
    assert sess is not None


@pytest.mark.parametrize("site_url", [ARENA_URL, PETLJA_URL])
def test_login_authenticates_both_sites(sess, site_url):
    response = sess.post(f"{site_url}/token", allow_redirects=False)
    assert response.status_code == 200
    result = response.json()
    assert result["succeeded"]
    assert bool(result["value"]["rawData"])


def test_login_failed():
    with pytest.raises(PermissionError):
        petlja.login("wrongusername", "wrongpass")
