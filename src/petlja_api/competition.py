import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from .auth import get_csrf_token
from .problem import get_problem_name
from .submit import LANGUAGE_IDS
from .urls import ARENA_URL, COMPETITIONS_URL, CPANEL_URL


def get_competition_id(session, alias):
    page = session.get(f"{ARENA_URL}/competition/{alias}")
    if page.status_code == 404 or "error" in page.url:
        raise ValueError(f"Competition with alias {alias} does not exist")
    if "AccessDenied" in page.url:
        raise PermissionError("User does not have permission to view competition")

    soup = BeautifulSoup(page.text, "html.parser")
    competition_id = soup.find("button", attrs={"id": "ciRun"})["data-competition-id"]
    return competition_id


def _get_competition_data(session, competition_id):
    page = session.get(f"{CPANEL_URL}/CompetitionTasks/{competition_id}")
    soup = BeautifulSoup(page.text, "html.parser")
    # Get object viewModel from inline script in html
    # which contains data about added problems
    # FIXME regex hack, should be replaced with a proper parser
    regex = re.compile(r"var viewModel=({.*?});\n")
    match = regex.search(soup.prettify()).group(1)
    # Can be parsed as json since it is a javascript object
    data = json.loads(match)
    return data


def get_added_problem_ids(session, competition_id):
    data = _get_competition_data(session, competition_id)
    problem_ids = [str(problem["problemId"]) for problem in data["problems"]]
    return problem_ids


def create_competition(
    session, name, alias=None, description=None, start_date=None, end_date=None
):
    if alias is None:
        alias = ""
    if description is None:
        description = ""
    if start_date is None:
        start_date = datetime.now()
    if end_date is None:
        end_date = ""

    regex = re.compile(r"^[a-z0-9-]+$")
    if not regex.match(alias):
        raise NameError(
            f"Invalid alias {alias}: must contain only"
            "lowercase alphanumeric characters and dashes"
        )

    url = f"{CPANEL_URL}/CreateCompetition"
    page = session.get(url)
    csrf_token = get_csrf_token(page.text)
    resp = session.post(
        url,
        data={
            "Name": name,
            "Alias": alias,
            "Description": description,
            "StartDate": start_date,
            "EndDate": end_date,
            "HasNotEndDate": [True, False],  # Not sure what this field does
            "__RequestVerificationToken": csrf_token,
        },
        allow_redirects=False,
    )

    if resp.status_code == 302:
        header_loc = resp.headers["Location"]  # /cpanel/CompetitionSettings/:comp_id
        comp_id = header_loc.split("/")[-1]
        return comp_id
    elif resp.status_code == 200:
        raise ValueError("Competition alias already exists")
    else:
        raise RuntimeError(f"Unknown error: {resp.status_code}")


def delete_competition(session: requests.Session, competition_id):
    res = session.post(f"{COMPETITIONS_URL}/delete/{competition_id}")
    if res.status_code != 200:
        raise ValueError(f"Error deleting competition: {res.text}")


def add_problem(session, competition_id, problem_id, sort_order):
    already_added = get_added_problem_ids(session, competition_id)
    if problem_id in already_added:
        return

    url = f"{COMPETITIONS_URL}/problems/add"
    problem_name = get_problem_name(session, problem_id)
    session.post(
        url,
        json={
            "competitionId": competition_id,
            "problemId": problem_id,
            "name": problem_name,
            "sortOrder": sort_order,
        },
    )

    # TODO: Check for errors


def remove_problem(session, competition_id, problem_id):
    data = _get_competition_data(session, competition_id)
    # problem["id"] is the id of the problem in the competition
    # problem["problemId"] is the id of the problem globally
    problem_ids_map = {
        str(problem["problemId"]): str(problem["id"]) for problem in data["problems"]
    }
    if problem_id not in problem_ids_map:
        raise ValueError(f"Problem with id {problem_id} is not added to competition")

    problem_comp_id = problem_ids_map[problem_id]
    url = f"{COMPETITIONS_URL}/problems/remove/{competition_id}/{problem_comp_id}"
    resp = session.post(url)
    if resp.status_code != 200 or not resp.json()["succeeded"]:
        raise ValueError(f"Error removing problem: {resp.text}")


def upload_scoring(session, competition_id, problem_id, scoring_path):
    url = f"{COMPETITIONS_URL}/problems/addGraderHints"
    with open(scoring_path) as scoring_file:
        scoring = scoring_file.read()
    resp = session.post(
        url,
        json={
            "competitionId": competition_id,
            "problemId": problem_id,
            "hintsYML": scoring,
            "testCaseCount": 100,  # FIXME Count number of testcases from scoring file
        },
    )

    errors = resp.json()["errors"]
    if errors:
        raise ValueError(f"Error uploading scoring, petlja response: {errors[0]}")


def add_language(session, competition_id, extension):
    url = f"{COMPETITIONS_URL}/programmingLanguages/add"
    session.post(
        url,
        json={"competitionId": competition_id, "languageId": LANGUAGE_IDS[extension]},
    )
    # TODO Check for errors
