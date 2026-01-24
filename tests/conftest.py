import os
import uuid

import pytest
from dotenv import load_dotenv

import petlja_api as petlja

load_dotenv()


@pytest.fixture
def sess():
    return petlja.login(os.environ["PETLJA_USER"], os.environ["PETLJA_PASS"])


@pytest.fixture
def problem_factory(sess):
    created = []

    def _create():
        uid = uuid.uuid4().hex
        alias = f"testprob{uid}"
        pid = petlja.create_problem(sess, "Test zadatak", alias)
        created.append(pid)
        return pid, alias

    yield _create
    for pid in created:
        petlja.delete_problem(sess, pid)


@pytest.fixture
def empty_comp(sess):
    uid = uuid.uuid4().hex
    alias = f"testcomp{uid}"
    cid = petlja.create_competition(sess, "Test takmicenje", alias)
    petlja.add_language(sess, cid, ".cpp")
    yield cid, alias
    petlja.delete_competition(sess, cid)


@pytest.fixture
def comp_with_problems(sess, empty_comp, problem_factory, scoring, testcases):
    cid, alias = empty_comp
    for i in range(2):
        pid, _ = problem_factory()
        petlja.add_problem(sess, cid, pid, sort_order=i)
        petlja.upload_testcases(sess, pid, testcases)
        petlja.upload_scoring(sess, cid, pid, scoring)
    return cid, alias


@pytest.fixture
def src_ce(tmp_path):
    src = r"""
    compile error
    """
    path = tmp_path / "trening_ce.cpp"
    path.write_text(src)
    return path


@pytest.fixture
def src_ok(tmp_path):
    src = r"""
    #include <iostream>
    using namespace std;

    int main()
    {
        int a, b; cin >> a >> b;
        cout << 2 * (a + b) << endl;
    }
    """
    path = tmp_path / "trening_ok.cpp"
    path.write_text(src)
    return path


@pytest.fixture
def src_wa(tmp_path):
    src = r"""
    #include <iostream>
    using namespace std;

    int main()
    {
        return 0;
    }
    """
    path = tmp_path / "trening_wa.cpp"
    path.write_text(src)
    return path


@pytest.fixture
def src_tle(tmp_path):
    src = r"""
    #include <iostream>
    using namespace std;

    int main()
    {
        int a, b; cin >> a >> b;
        while(true) {}
    }
    """
    path = tmp_path / "trening_tle.cpp"
    path.write_text(src)
    return path


@pytest.fixture
def src_rte(tmp_path):
    src = r"""
    #include <iostream>
    using namespace std;

    int main()
    {
        int a, b; cin >> a >> b;
        cout << 1 / 0;
    }
    """
    path = tmp_path / "trening_rte.cpp"
    path.write_text(src)
    return path


@pytest.fixture
def src_py(tmp_path):
    src = r"""
a = int(input())
b = int(input())
print(2 * (a + b))
    """
    path = tmp_path / "trening.py"
    path.write_text(src)
    return path


@pytest.fixture
def src_ok_wa(tmp_path):
    src = r"""
    #include <iostream>
    using namespace std;

    int main()
    {
        int a, b; cin >> a >> b;
        if (a % 2 == 0) cout << -1;
        cout << 2 * (a + b) << endl;
        return 0;
    }
    """
    path = tmp_path / "trening_ok_wa.cpp"
    path.write_text(src)
    return path


@pytest.fixture
def src_100ms_runtime(tmp_path):
    src = r"""
a = 0
for i in range(1000000):
    a += 1
    """
    path = tmp_path / "trening_100ms_runtime.py"
    path.write_text(src)
    return path


@pytest.fixture
def src_10mb_memory(tmp_path):
    src = r"""
    #include <stdio.h>
    #include <stdlib.h>
    #define N 9 * 1000 * 1000
    int main()
    {
        unsigned char a[N];
        for (int i = 0; i < N; i++) {
            a[i] = rand();
        }
        int s = 0;
        for (int i = 0; i < N; i++)
            s += a[i];
        printf("%d", s);
    }
    """
    path = tmp_path / "trening_10mb_memory.cpp"
    path.write_text(src)
    return path


@pytest.fixture
def statement(tmp_path):
    st = r"""
    За низ ћемо рећи да је **уравнотежен** ако је збир његових елемената једнак његовој дужини (броју елемената).

    Дат је низ $a$ дужине $n$, чији су елементи једноцифрени бројеви. Одредити колико он садржи уравнотежених сегмената (поднизова са узастопним елементима).

    ## Улаз

    У првом реду стандардног улаза је број $n$ $(1 \leq n \leq 10^5)$, а у другом $n$ ненегативних једноцифрених бројева, раздвојених по једним размаком.

    ## Излаз

    На стандардни излаз исписати тражени број.

    ## Пример

    ### Улаз

    ~~~
    5
    0 3 0 0 2
    ~~~

    ### Излаз

    ~~~
    4
    ~~~

    *Објашњење*: Тражени сегменти су $[0 3 0]$, $[3 0 0]$, $[0 2]$ и $[0 3 0 0 2]$.

    """
    path = tmp_path / "tekst-st.md"
    path.write_text(st)
    return path


@pytest.fixture
def testcases():
    return "tests/data/testcases.zip"


@pytest.fixture
def scoring(tmp_path):
    yaml = r"""
    type: testcase
    score_total: 100
    score_overrides:
    - {name: 1, score: 10}
    - {name: 2, score: 10}
    - {name: 3, score: 10}
    - {name: 4, score: 10}
    - {name: 5, score: 10}
    - {name: 6, score: 10}
    - {name: 7, score: 10}
    - {name: 8, score: 10}
    - {name: 9, score: 10}
    - {name: 10, score: 10}
    public: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    """
    scoring_path = tmp_path / "scoring.yaml"
    scoring_path.write_text(yaml)
    return scoring_path


# The following functions are taken from the pytest documentation:
# https://docs.pytest.org/en/latest/example/simple.html#control-skipping-of-tests-according-to-command-line-option


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
