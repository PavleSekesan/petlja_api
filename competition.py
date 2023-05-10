import json
import re
from datetime import datetime

from bs4 import BeautifulSoup

from auth import get_csrf_token
from problem import get_problem_name
from urls import ARENA_URL, PETLJA_URL


def get_competition_id(session, alias):
    page = session.get(f"{ARENA_URL}/competition/{alias}")
    if page.status_code == 404:
        raise ValueError(f"Competition with alias {alias} does not exist")

    soup = BeautifulSoup(page.text, "html.parser")
    competition_id = soup.find("button", attrs={"id": "ciRun"})["data-competition-id"]
    return competition_id


def get_added_problem_ids(session, competition_id):
    page = session.get(f"{PETLJA_URL}/cpanel/CompetitionTasks/{competition_id}")
    soup = BeautifulSoup(page.text, "html.parser")
    # Get object viewModel from inline script in html which contains data about added problems
    # FIXME regex hack, should be replaced with a proper parser
    regex = re.compile(r"var viewModel=({.*?});\n")
    match = regex.search(soup.prettify()).group(1)
    # Can be parsed as json since it is a javascript object
    data = json.loads(match)
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
            f"Invalid alias {alias}: must contain only lowercase alphanumeric characters and dashes"
        )

    url = f"{PETLJA_URL}/cpanel/CreateCompetition"
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


def add_problem(session, competition_id, problem_id, scoring=None):
    already_added = get_added_problem_ids(session, competition_id)
    if problem_id in already_added:
        return

    url = f"{PETLJA_URL}/api/dashboard/competitions/problems/add"
    problem_name = get_problem_name(session, problem_id)
    resp = session.post(
        url,
        json={
            "competitionId": competition_id,
            "problemId": problem_id,
            "name": problem_name,
            # "sortOrder": 0, # Seems to be optional
        },
    )

    # TODO: Check for errors
