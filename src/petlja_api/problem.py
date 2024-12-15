from bs4 import BeautifulSoup

from dataclasses import dataclass

from .auth import get_csrf_token
from .urls import CPANEL_URL, PROBLEMS_URL


def get_problem_id(session, alias):
    page = session.get(f"{PROBLEMS_URL}/{alias}")
    if page.status_code == 404:
        raise ValueError(f"Problem with alias {alias} does not exist")

    soup = BeautifulSoup(page.text, "html.parser")
    problem_id = soup.find("button", attrs={"class": "btn-solution-submit"})[
        "data-problem-id"
    ]
    return problem_id


def get_problem_name(session, problem_id):
    page = session.get(f"{CPANEL_URL}/EditProblem/{problem_id}")
    if page.status_code == 404:
        raise ValueError(f"Problem with id {problem_id} does not exist")

    soup = BeautifulSoup(page.text, "html.parser")
    problem_name = soup.find("input", attrs={"id": "Problem_Name"})["value"]
    return problem_name


def create_problem(session, name, alias):
    if not alias or not alias.isalnum() or not alias.islower():
        raise NameError(
            f"Invalid problem alias {alias}: must be alphanumeric and lowercase"
        )

    create_problem_page = session.get(f"{CPANEL_URL}/CreateTask")
    csrf_token = get_csrf_token(create_problem_page.text)
    resp = session.post(
        f"{CPANEL_URL}/CreateTask",
        data={
            "Name": name,
            "UniqueId": alias,
            "Type": "0",
            "__RequestVerificationToken": csrf_token,
        },
        allow_redirects=False,
    )
    if resp.status_code == 302:
        return get_problem_id(session, alias)
    elif resp.status_code == 200:
        raise ValueError("Problem alias already exists")
    else:
        raise RuntimeError(
            f"Unknown error while creating problem (status code {resp.status_code})"
        )


def delete_problem(session, problem_id):
    page = session.get(f"{CPANEL_URL}/EditProblem/{problem_id}")
    csrf_token = get_csrf_token(page.text)
    session.post(
        f"{CPANEL_URL}/EditProblem/{problem_id}",
        data={
            "PostAction": "DeleteProblem",
            "__RequestVerificationToken": csrf_token,
        },
    )


def _check_testcase_upload(page):
    soup = BeautifulSoup(page.text, "html.parser")
    error = soup.find("div", attrs={"class": "validation-summary-errors"})
    if error:
        errmsg = f"Testcase upload failed: {error.text.strip()}"
        if error.text.strip() == "UserIdNotFound":
            errmsg += " (Is the zip file in the correct format?)"
        raise ValueError(errmsg)


def upload_testcases(session, problem_id, testcases_path):
    page = session.get(f"{CPANEL_URL}/EditProblem/{problem_id}?tab=testcases")
    csrf_token = get_csrf_token(page.text)
    with open(testcases_path, "rb") as zipfile:
        resp = session.post(
            f"{CPANEL_URL}/EditProblem/{problem_id}",
            files={"TestCases": zipfile},
            data={
                "PostAction": "EditTestCases",
                "__RequestVerificationToken": csrf_token,
            },
        )
    # Have to scrape the response page to check for errors
    # because the response is 302 even if there is an error
    _check_testcase_upload(resp)


def upload_statement(session, problem_id, statement_path):
    page = session.get(f"{CPANEL_URL}/EditProblem/{problem_id}?tab=statement")
    csrf_token = get_csrf_token(page.text)
    with open(statement_path, encoding="utf-8") as statement:
        session.post(
            f"{CPANEL_URL}/EditProblem/{problem_id}",
            data={
                "Problem.ProblemStatementMD": statement.read(),
                "PostAction": "EditStatement",
                "Problem.MDSupported": "true",
                "__RequestVerificationToken": csrf_token,
            },
            allow_redirects=False,
        )
    # TODO: check for errors


@dataclass
class ProblemMetadata:
    name: str
    time_limit_ms: str
    memory_limit_mb: str
    author: str
    solution_author: str
    contributors: str
    origin: str
    tags: str


_inputname_to_metadata_attr_map = {
    "Problem.Name": "name",
    "Problem.TimeLimit": "time_limit_ms",
    "Problem.MemoryLimit": "memory_limit_mb",
    "Problem.Author": "author",
    "Problem.SolAuthor": "solution_author",
    "Problem.Contributors": "contributors",
    "Problem.Origin": "origin",
    "Problem.Tags": "tags",
}


def _problem_metadata_dict(sess, pid, metadata: ProblemMetadata):
    page = sess.get(f"{CPANEL_URL}/EditProblem/{pid}")
    if page.status_code == 404:
        raise ValueError(f"Problem with id {pid} does not exist")
    csrf_token = get_csrf_token(page.text)

    dict = {}
    for inputname, metadata_attr in _inputname_to_metadata_attr_map.items():
        dict[inputname] = (None, getattr(metadata, metadata_attr))

    dict.update(
        {
            # TODO Implement problem types (Standard, Output only, Functional) support
            # currently defaults to Standard (type 0)
            "Problem.Type": "0",
            # TODO Implement additional material upload,
            # this currently overwrites any existing additional material
            "Problem.AdditionalMaterialTitle": (None, ""),
            "Problem.AdditionalMaterialZip": (None, ""),
            "PostAction": (None, "EditMetaInfo"),
            "__RequestVerificationToken": (None, csrf_token),
        }
    )

    return dict


def _set_problem_metadata(session, problem_id, metadata: ProblemMetadata):
    res = session.post(
        f"{CPANEL_URL}/EditProblem/{problem_id}",
        files=_problem_metadata_dict(session, problem_id, metadata),
    )
    if res.status_code != 200:
        raise RuntimeError(
            f"Failed setting problem metadata: {res.status_code} {res.text}"
        )


def get_problem_metadata(session, problem_id):
    res = session.get(f"{CPANEL_URL}/EditProblem/{problem_id}")
    soup = BeautifulSoup(res.text, "html.parser")
    inputs = soup.select("#settingsPanel fieldset input")

    metadata_fields = {}
    for inp in inputs:
        field = _inputname_to_metadata_attr_map.get(inp["name"])
        if field is None:
            continue
        metadata_fields[field] = inp["value"]

    return ProblemMetadata(**metadata_fields)


def set_time_limit(session, problem_id, time_limit_ms):
    metadata = get_problem_metadata(session, problem_id)
    metadata.time_limit_ms = time_limit_ms
    try:
        _set_problem_metadata(session, problem_id, metadata)
    except RuntimeError as e:
        raise RuntimeError("Failed setting time limit") from e


def set_memory_limit(session, problem_id, memory_limit_mb):
    metadata = get_problem_metadata(session, problem_id)
    metadata.memory_limit_mb = memory_limit_mb
    try:
        _set_problem_metadata(session, problem_id, metadata)
    except RuntimeError as e:
        raise RuntimeError("Failed setting memory limit") from e
