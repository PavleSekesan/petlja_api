import pytest

import petlja_api as petlja


def test_upload_scoring(sess, comp_with_problems, scoring):
    cid, _ = comp_with_problems
    pid = petlja.get_added_problem_ids(sess, cid)[0]
    petlja.upload_scoring(sess, cid, pid, scoring)


def test_get_competition_id(sess, empty_comp):
    cid, alias = empty_comp
    assert petlja.get_competition_id(sess, alias) == cid


def test_get_competition_id_nonexistent(sess):
    with pytest.raises(ValueError):
        petlja.get_competition_id(sess, "qurvoqireouqh")


def test_submit_unallowed_lang(sess, comp_with_problems, problem_factory, src_py):
    cid, _ = comp_with_problems
    pid, _ = problem_factory()
    with pytest.raises(Exception):
        petlja.submit_solution(sess, cid, pid, src_py)


def test_delete_competition(sess, empty_comp):
    cid, _ = empty_comp
    petlja.delete_competition(sess, cid)
    with pytest.raises(ValueError):
        petlja.get_competition_id(sess, cid)


def test_competition_access_denied(sess):
    with pytest.raises(PermissionError):
        petlja.get_competition_id(sess, "os-kv1-202425-6")


def test_remove_problem(sess, comp_with_problems):
    cid, _ = comp_with_problems
    pid = petlja.get_added_problem_ids(sess, cid)[0]
    petlja.remove_problem(sess, cid, pid)
    new_pids = petlja.get_added_problem_ids(sess, cid)
    assert pid not in new_pids


def test_remove_nonexistent_problem(sess, comp_with_problems):
    cid, _ = comp_with_problems
    with pytest.raises(ValueError):
        petlja.remove_problem(sess, cid, "123456789")


def test_sort_order(sess, comp_with_problems):
    cid, _ = comp_with_problems
    data = petlja.competition._get_competition_data(sess, cid)
    assert data["problems"][0]["sortOrder"] == 0
    assert data["problems"][1]["sortOrder"] == 1
