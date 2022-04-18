import os

__all__ = [
    "SCML_RUNALL_TESTS",
    "SCML_FASTRUN",
    "SCML_RUN2019",
    "SCML_RUN2020",
    "SCML_RUN2021_TOURNAMENT",
    "SCML_RUN2021_ONESHOT",
    "SCML_RUN2021_ONESHOT_SYNC",
    "SCML_RUN2021_STD",
    "SCML_RUN_TUTORIAL2",
    "SCML_RUN_GENIUS",
    "SCML_RUN_TOURNAMENTS",
    "SCML_RUN_STD_TOURNAMENTS",
    "SCML_RUN_COLLUSION_TOURNAMENTS",
    "SCML_RUN_SABOTAGE_TOURNAMENTS",
    "SCML_RUN_TEMP_FAILING",
]

SCML_RUNALL_TESTS = os.environ.get("SCML_RUNALL_TESTS", False)
SCML_ON_GITHUB = os.environ.get("GITHUB_ACTIONS", False)
SCML_FASTRUN = os.environ.get("SCML_FASTRUN", SCML_ON_GITHUB and not SCML_RUNALL_TESTS)
SCML_RUN_TEMP_FAILING = os.environ.get("SCML_RUN_TEMP_FAILING", False)
SCML_RUN2021_ONESHOT = os.environ.get("SCML_RUN2021_ONESHOT", True)
SCML_RUN2021_STD = os.environ.get("SCML_RUN2021_STD", True)
SCML_RUN_GENIUS = os.environ.get(
    "SCML_RUN_GENIUS", not SCML_FASTRUN or SCML_RUNALL_TESTS
)
SCML_RUN_TOURNAMENTS = os.environ.get(
    "SCML_RUN_TOURNAMENTS", not SCML_FASTRUN or SCML_RUNALL_TESTS
)
SCML_RUN_STD_TOURNAMENTS = os.environ.get(
    "SCML_RUN_STD_TOURNAMENTS", SCML_RUN_TOURNAMENTS
)
SCML_RUN_COLLUSION_TOURNAMENTS = os.environ.get(
    "SCML_RUN_COLLUSION_TOURNAMENTS", SCML_RUN_TOURNAMENTS
)
SCML_RUN_SABOTAGE_TOURNAMENTS = os.environ.get(
    "SCML_RUN_SABOTAGE_TOURNAMENTS", SCML_RUN_TOURNAMENTS
)

SCML_RUN2021_TOURNAMENT = os.environ.get(
    "SCML_RUN2021_TOURNAMENT", not SCML_FASTRUN or SCML_RUNALL_TESTS
)
SCML_RUN2021_ONESHOT_SYNC = os.environ.get(
    "SCML_RUN2021_ONESHOT_SYNC", not SCML_FASTRUN or SCML_RUNALL_TESTS
)

SCML_RUN2019 = os.environ.get("SCML_RUN2019", not SCML_FASTRUN or SCML_RUNALL_TESTS)
SCML_RUN2020 = os.environ.get("SCML_RUN2020", not SCML_FASTRUN or SCML_RUNALL_TESTS)

SCML_RUN_TUTORIAL2 = os.environ.get(
    "SCML_RUN_TUTORIAL2", not SCML_FASTRUN or SCML_RUNALL_TESTS
)
SCML_RUN_NOTEBOOKS = os.environ.get(
    "SCML_RUN_NOTEBOOKS", not SCML_FASTRUN or SCML_RUNALL_TESTS
)
SCML_RUN_SCHEDULER = os.environ.get(
    "SCML_RUN_SCHEDULER", SCML_RUN2019 or SCML_RUNALL_TESTS
)
