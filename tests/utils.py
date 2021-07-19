import re

github_url_commit = re.compile(r"/blob/[0-9a-f]{40}/")


def remove_commit_hash_from_github_url(usage):
    """
    So that our tests don't break after we do a new commit
    """
    usage["usage_example"]["github_url"] = github_url_commit.sub(
        r"/blob/:commit/", usage["usage_example"]["github_url"]
    )


def replace_digits_with_zeros_in_datetimes(usage):
    usage["repo_last_updated"] = re.sub(r"\d", "0", usage["repo_last_updated"])


def replace_newlines_and_tabs_with_spaces(usage):
    """
    Makes it easier to review diffs in test results
    """
    inlined_code = usage["code"].replace("\n", " ").replace("\t", " ")
    usage["code"] = inlined_code
    usage["usage_example"]["code"] = inlined_code
