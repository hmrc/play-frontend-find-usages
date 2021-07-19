"""
Search functions are all async generators
"""

import os
import json

from aiostream import stream

from find_usages.ripgrep import (
    search_using_ripgrep,
    output_matches_as_json,
    output_newline_delimited_lists_of_files_grouped_by_matches,
    using_jq_select_only_matches,
    using_ripgrep_with_common_params,
    search_using_ripgrep_for_usages_via_deprecated_static_helper,
    match_instantiation_and_assignment,
    match_instantiation_and_use_as_argument,
    match_instantiation_and_use_immediately,
    match_injection,
    match_usages_not_instantiations,
    search_using_ripgrep_for_usages_via_nunjucks,
)

from find_usages.utils import (
    get_git_repo_latest_commit,
    get_git_repo_last_updated_at,
    identify_library,
    identify_language,
    parse_alias_and_files,
    run,
    terminate_all_subprocesses_on_exception,
)


async def parse_usage(usage, of_component, in_search_path, labels=None):
    result = json.loads(usage)
    repo, *path = result["data"]["path"]["text"].strip("./").split("/")
    path = "/".join(path)
    repo_path = os.path.join(in_search_path, repo)
    git_commit = await get_git_repo_latest_commit(repo_path)
    repo_last_updated = await get_git_repo_last_updated_at(repo_path)
    template_language = identify_language(path)
    library = identify_library(template_language, of_component)
    code = result["data"]["submatches"][0]["match"]["text"]
    line_start = result["data"]["line_number"]
    line_stop = line_start + code.count("\n")
    if labels is None:
        labels = []
    if ".withFormField" in code:
        # some services may construct this with their own helper and still be using with-form-field so this has
        # the -inline suffix to try and show it's not the complete set, although you should assume that it's
        # never going to be possible to find the complete set of any conditions with this tool because we're just
        # working with regex
        labels.append("using-with-form-field-inline")
    # TODO template last edited?
    # TODO library dependency versions?
    return {
        "repo": repo,
        "component": of_component,
        "library": library,
        "labels": labels,
        "template_language": template_language,
        "line_count": 1 + code.count("\n"),
        "parenthesis_count": code.count("("),
        "length": len(code),
        "repo_last_updated": repo_last_updated,
        "usage_example": {
            "github_url": f"https://github.com/hmrc/{repo}/blob/{git_commit}/{path}#L{line_start}-L{line_stop}",
            "line_number": line_start,
            "code": code,
            "path": path,
        },
        "code": code,
        "path": path,
    }


async def find_usages_in_files(of_component, files_to_search, in_search_path):
    async for usage in run(
        rf"""xargs --no-run-if-empty {using_ripgrep_with_common_params} --regexp '{match_usages_not_instantiations(of_component)}' --json"""
        rf""" | {using_jq_select_only_matches}""",
        working_dir=in_search_path,
        files_to_search=files_to_search,
    ):
        yield usage


async def find_usages_via_dependency_injection(in_search_path, of_component):
    async for alias_and_files in run(
        search_using_ripgrep(
            match_injection(of_component),
            output_newline_delimited_lists_of_files_grouped_by_matches,
        ),
        working_dir=in_search_path,
    ):
        (alias, files_its_found_in) = parse_alias_and_files(alias_and_files)

        async for usage in find_usages_in_files(
            alias, files_its_found_in, in_search_path
        ):
            yield await parse_usage(
                usage,
                of_component,
                in_search_path,
                labels=["via-dependency-injection"],
            )


async def find_usages_via_inline_instantiation_where_used_immediately(
    in_search_path, of_component
):
    async for usage in run(
        search_using_ripgrep(
            match_instantiation_and_use_immediately(of_component),
            output_matches_as_json,
        ),
        working_dir=in_search_path,
    ):
        yield await parse_usage(
            usage,
            of_component,
            in_search_path,
            labels=["via-inline-instantiation", "used-immediately"],
        )


async def find_usages_via_inline_instantiation_where_used_as_argument(
    in_search_path, of_component
):
    async for usage in run(
        search_using_ripgrep(
            match_instantiation_and_use_as_argument(of_component),
            output_matches_as_json,
        ),
        working_dir=in_search_path,
    ):
        yield await parse_usage(
            usage,
            of_component,
            in_search_path,
            labels=["via-inline-instantiation", "used-as-argument"],
        )


async def find_usages_via_inline_instantiation_where_assigned_to_variable(
    in_search_path, of_component
):
    async for alias_and_files in run(
        search_using_ripgrep(
            match_instantiation_and_assignment(of_component),
            output_newline_delimited_lists_of_files_grouped_by_matches,
        ),
        working_dir=in_search_path,
    ):
        (alias, files_its_found_in) = parse_alias_and_files(alias_and_files)

        async for usage in find_usages_in_files(
            alias, files_its_found_in, in_search_path=in_search_path
        ):
            yield await parse_usage(
                usage,
                of_component,
                in_search_path,
                labels=["via-inline-instantiation", "used-as-variable"],
            )


async def find_usages_via_inline_instantiation(in_search_path, of_component):
    searches = stream.merge(
        find_usages_via_inline_instantiation_where_used_immediately(
            in_search_path, of_component
        ),
        find_usages_via_inline_instantiation_where_used_as_argument(
            in_search_path, of_component
        ),
        find_usages_via_inline_instantiation_where_assigned_to_variable(
            in_search_path, of_component
        ),
    )

    async with searches.stream() as search_stream:
        async for usage in search_stream:
            yield usage


async def find_usages_via_deprecated_static_helper(in_search_path, of_component):
    async for usage in run(
        search_using_ripgrep_for_usages_via_deprecated_static_helper(of_component),
        working_dir=in_search_path,
    ):
        yield await parse_usage(
            usage,
            of_component,
            in_search_path,
            labels=["via-deprecated-static-helper"],
        )


async def find_usages_via_nunjucks(in_search_path, of_component):
    async for usage in run(
        search_using_ripgrep_for_usages_via_nunjucks(of_component),
        working_dir=in_search_path,
    ):
        yield await parse_usage(usage, of_component, in_search_path)


@terminate_all_subprocesses_on_exception
async def find_all_usages_for_component(in_search_path, of_component):
    searches = stream.merge(
        find_usages_via_dependency_injection(in_search_path, of_component),
        find_usages_via_deprecated_static_helper(in_search_path, of_component),
        find_usages_via_inline_instantiation(in_search_path, of_component),
        find_usages_via_nunjucks(in_search_path, of_component),
    )

    async with searches.stream() as search_stream:
        async for usage in search_stream:
            yield usage


@terminate_all_subprocesses_on_exception
async def find_all_usages_for_all_components(in_search_path, of_components):
    searches = stream.merge(
        *[
            find_all_usages_for_component(in_search_path, of_component=component)
            for component in of_components
        ]
    )

    async with searches.stream() as search_stream:
        async for usage in search_stream:
            yield usage
