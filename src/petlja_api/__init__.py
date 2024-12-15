from .auth import login
from .competition import (
    add_language,
    add_problem,
    remove_problem,
    create_competition,
    delete_competition,
    get_added_problem_ids,
    get_competition_id,
    upload_scoring,
)
from .problem import (
    create_problem,
    delete_problem,
    get_problem_id,
    get_problem_name,
    get_problem_metadata,
    set_memory_limit,
    set_time_limit,
    upload_statement,
    upload_testcases,
)
from .submit import (
    submit_solution,
    submit_solution_detailed,
)

__all__ = [
    "login",
    "add_language",
    "add_problem",
    "remove_problem",
    "create_competition",
    "delete_competition",
    "get_added_problem_ids",
    "get_competition_id",
    "upload_scoring",
    "create_problem",
    "delete_problem",
    "get_problem_id",
    "get_problem_name",
    "get_problem_metadata",
    "set_memory_limit",
    "set_time_limit",
    "upload_statement",
    "upload_testcases",
    "submit_solution",
    "submit_solution_detailed",
]
