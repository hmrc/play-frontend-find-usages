"""
Module abstracts all ripgrep commands and regexp composed by core search functions
"""


using_jq_select_only_matches = r"""jq --compact-output 'select(.type == "match")'"""

using_jq_select_only_matches_that_are_not_being_instantiated_inline = r"""jq --compact-output 'select((.type == "match") and (.data.submatches[0].match.text | startswith("new") | not))'"""

using_ripgrep_with_common_params = (
    r"""rg --no-pcre2-unicode --pcre2 --multiline --only-matching"""
)


def search_using_ripgrep(regexp, output):
    """
    Wrapper so we can say compose things as "search for X output as Y" rather than "output as Y things that match X"
    """
    return output(regexp)


def output_matches_as_json(regexp):
    return (
        rf"""{using_ripgrep_with_common_params} --regexp '{regexp}' --glob '**/*.scala.html' --json ."""
        rf""" | {using_jq_select_only_matches}"""
    )


def output_newline_delimited_lists_of_files_grouped_by_matches(
    regexp, field_separator=":"
):
    return (
        rf"""{using_ripgrep_with_common_params} --regexp '{regexp}' --glob '**/*.scala.html' ."""
        rf""" | datamash --field-separator '{field_separator}' --sort --group 2 collapse 1"""
    )


def search_using_ripgrep_for_usages_via_deprecated_static_helper(component):
    match_assigned_inline = rf"{component}\s+="
    match_assigned_via_injection = rf"{component} *:"

    return (
        rf"""{using_ripgrep_with_common_params} --regexp '{match_assigned_inline}' --regexp '{match_assigned_via_injection}' --files-without-match --glob "**/*.scala.html" ."""
        rf""" | xargs --no-run-if-empty {using_ripgrep_with_common_params} '(new)? *{match_optional_package}{component}({match_any_params(2)})' --json"""
        rf""" | {using_jq_select_only_matches_that_are_not_being_instantiated_inline}"""
    )


def search_using_ripgrep_for_usages_via_nunjucks(of_component):
    return (
        rf"""{using_ripgrep_with_common_params} --regexp '{of_component}({match_any_params()})' --glob "**/*.njk" --json ."""
        rf""" | {using_jq_select_only_matches}"""
    )


match_optional_package = (
    r"(?:[\w\.]*(?:govuk|hmrc)frontend[\w\.]*|components.|helpers.)?"
)


def match_any_params(group=1):
    """
    If there is a previous capture group in the regex then group needs to be the index of match_any_params
    """
    return rf"\((?:[^)(]*(?{group})?)*+\)"


def match_class_name(component):
    return rf"""[{component[0].lower()}{component[0].upper()}]{component[1:]}"""


def match_injection(component):
    return rf"""\w+(?=\s*:\s*{match_optional_package}{match_class_name(component)}[,\s\)])"""


def match_instantiation_and_use_immediately(component):
    return rf"""new\s*{match_optional_package}{match_class_name(component)}({match_any_params()})({match_any_params(2)})"""


def match_instantiation_and_use_as_argument(component):
    return rf"""(?<=[^@][\({{,])\s*new\s*{match_optional_package}{match_class_name(component)}({match_any_params()})(?=[^\(])"""


def match_instantiation_and_assignment(component):
    return rf"""(?<=@)\w+(?=\s+=\s+@{{\s*new\s+{match_optional_package}{match_class_name(component)}({match_any_params()})[^/(])"""


def match_usages_not_instantiations(component):
    return rf"""(?<!\w)(?<!new )(?<!new  ){component}({match_any_params()})"""
