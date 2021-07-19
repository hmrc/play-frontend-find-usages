import json
import os

from find_usages.core import find_all_usages_for_all_components
import pytest

from find_usages.outputs import as_json_line
from find_usages.utils import (
    get_default_list_of_all_components,
)
from tests.utils import (
    remove_commit_hash_from_github_url,
    replace_digits_with_zeros_in_datetimes,
    replace_newlines_and_tabs_with_spaces,
)

fixtures_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures")

all_fixtures = [f.path for f in os.scandir(fixtures_path) if f.is_dir()]

components = get_default_list_of_all_components()


def normalized(usage):
    remove_commit_hash_from_github_url(usage)
    replace_newlines_and_tabs_with_spaces(usage)
    replace_digits_with_zeros_in_datetimes(usage)
    return usage


@pytest.mark.asyncio
@pytest.mark.parametrize("fixture", all_fixtures)
async def test_all_fixtures_against_their_expected_output(
    fixture, update_expected_output
):
    actual_output = [
        normalized(usage)
        async for usage in find_all_usages_for_all_components(
            in_search_path=fixture,
            of_components=components,  # or use ["govukButton"] to run quickly!
        )
    ]

    actual_output.sort(key=lambda d: json.dumps(d))

    if update_expected_output:
        # pass --bless when running pytest, handy way to quickly update fixtures
        with open(f"{fixture}.out", "w") as expected_stdout:
            for usage in actual_output:
                expected_stdout.write(f"{as_json_line(usage)}\n")

    with open(f"{fixture}.out", "r") as expected_stdout:
        expected_output = [json.loads(json_line) for json_line in expected_stdout]

    assert actual_output == expected_output
