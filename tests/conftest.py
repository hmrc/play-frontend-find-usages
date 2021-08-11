import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--bless",
        action="store_true",
        default=False,
        help="Save the actual output as the new expected output",
    )


@pytest.fixture()
def update_expected_output(request):
    return request.config.getoption("--bless")
