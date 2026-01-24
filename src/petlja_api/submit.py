from .urls import ARENA_URL
import time
import re
import math
from typing import List, Union

from dataclasses import dataclass

# Weird Petlja API language IDs
LANGUAGE_IDS = {
    ".c": 10,
    ".cs": 1,
    ".cpp": 11,
    ".java": 3,
    ".m": 7,
    ".pas": 4,
    ".py": 9,
}

TIMEOUT = 30


@dataclass
class TestcaseResult:
    """
    Represents the result of a single test case.

    Attributes:
        status (str): The status of the test case. Possible values are:
            - "WA": Wrong Answer
            - "OK": Correct Answer
            - "TLE": Time Limit Exceeded
            - "MLE": Memory Limit Exceeded
            - "RTE": Runtime Error

        time_ms (int | float | None): The runtime in milliseconds. Possible values are:
            - A positive number representing the runtime in milliseconds.
            - math.inf if the test case resulted in TLE
            - None if the runtime is not available.

        memory_mb (int | float | None): The memory usage in megabytes. Possible values are:
            - A positive number representing the memory usage in megabytes.
            - math.inf if the test case resulted in MLE
            - None if the memory usage is not available.
    """

    status: str
    time_ms: Union[int, float, None]
    memory_mb: Union[int, float, None]


@dataclass
class SubmissionResult:
    """
    Represents the result of a submission.

    Attributes:
        score (int | None): The score of the submission. Possible values are:
            - A positive integer representing the score.
            - 0 if the submission resulted in a compilation error.
            - None if the submission is still being processed.

        compile_error (bool): Whether the submission has compiled successfully.

        testcase_results (list[TestcaseResult]): The results of each test case.
    """

    score: Union[int, None]
    compile_error: bool
    testcase_results: List[TestcaseResult]


def _parse_time(time_str):
    if time_str == "-":
        return None
    time_regex = re.match(r"(>?)(\d+,\d\d)s", time_str)
    if time_regex is None:
        raise ValueError(f"Error parsing results time: {time_str}")
    if time_regex.group(1) == ">":
        # TLE happened
        time_ms = math.inf
    else:
        time_replaced_comma = time_regex.group(2).replace(",", ".")
        time_s = float(time_replaced_comma)
        time_ms = int(time_s * 1000)
    return time_ms


def _parse_memory(memory_str):
    if memory_str == "-":
        return None
    memory_regex = re.match(r"(\d+),\d\dMB", memory_str)
    if memory_regex is None:
        raise ValueError(f"Error parsing results memory: {memory_str}")
    memory_mb = int(memory_regex.group(1))
    return memory_mb


def _parse_detailed_results(results):
    return [
        TestcaseResult(
            testcase["status"],
            _parse_time(testcase["time"]),
            _parse_memory(testcase["memory"]),
        )
        for testcase in results
    ]


def _submit(session, competition_id, problem_id, source_path):
    with open(source_path) as source_file:
        source = source_file.read()

    extension = source_path.suffix
    res = session.post(
        f"{ARENA_URL}/api/competition/submit-competition-problem",
        json={
            "competitionId": competition_id,
            "problemId": problem_id,
            "source": source,
            "languageId": LANGUAGE_IDS[extension],
        },
    ).json()
    success = res["succeeded"]
    if not success:
        error = res["errors"][0]["description"]
        raise Exception(error)
    submission_id = res["value"]
    return submission_id


def _get_submission_results(session, competition_id, submission_id):
    # Polling the server every x seconds
    # Better solution may exist
    tries = 0
    while tries < TIMEOUT:
        submission_data = session.post(
            f"{ARENA_URL}/api/competition/submissions",
            json={
                "competitionId": competition_id,
                "idStamp": submission_id,
                "loadNew": True,
            },
        )
        results = submission_data.json()["value"]["item1"][0]
        score = results["score"]
        if score != "-":
            return results
        time.sleep(1)

    raise TimeoutError


def _parse_score(score):
    if score == "-":
        return None
    if score == "CE":
        return 0
    return int(score)


# TODO: Deprecate this function in favor of submit_solution_detailed
def submit_solution(session, competition_id, problem_id, source_path):
    submission_id = _submit(session, competition_id, problem_id, source_path)

    results = _get_submission_results(session, competition_id, submission_id)
    return results["score"]


def submit_solution_detailed(session, competition_id, problem_id, source_path):
    submission_id = _submit(session, competition_id, problem_id, source_path)
    results = _get_submission_results(session, competition_id, submission_id)
    score_id = results["scoreId"]
    detailed_results = session.get(
        f"{ARENA_URL}/api/competition/competitor-score/{score_id}"
    ).json()["value"]
    testcase_scores = detailed_results["testCaseScores"]
    return SubmissionResult(
        _parse_score(results["score"]),
        not detailed_results["hasCompiled"],
        _parse_detailed_results(testcase_scores),
    )
