import pytest
import requests
from bs4 import BeautifulSoup

import petlja_api as petlja
from petlja_api.urls import CPANEL_URL


def test_create_problem(problem_factory):
    _, alias = problem_factory()
    res = requests.get(f"https://petlja.org/problems/{alias}")
    assert res.status_code == 200


def test_create_already_existing_prob(sess):
    with pytest.raises(ValueError):
        petlja.create_problem(sess, "Postojeci problem", "osdrz23odbijanje")


def test_upload_testcases(sess, problem_factory, testcases):
    id, _ = problem_factory()
    petlja.upload_testcases(sess, id, testcases)


def test_upload_statement(sess, problem_factory, statement):
    id, _ = problem_factory()
    petlja.upload_statement(sess, id, statement)


def _get_cpanel_problem_ids(sess):
    page = sess.get(f"{CPANEL_URL}/Problems")
    soup = BeautifulSoup(page.text, "html.parser")
    problems_list = soup.select(".list-group-item")
    # items are of format <li id=title-{id} class="list-group-item">
    problem_ids = []
    for p in problems_list:
        id_attr_str = p.get("id")
        assert id_attr_str is not None
        id = id_attr_str[len("title-") :]
        problem_ids.append(id)
    return problem_ids


def test_delete_problem(sess, problem_factory):
    pid, _ = problem_factory()
    petlja.delete_problem(sess, pid)
    # For some reason the problem isn't actually deleted
    # just unlisted from the problems page
    problem_ids = _get_cpanel_problem_ids(sess)
    assert pid not in problem_ids
