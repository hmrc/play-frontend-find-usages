import argparse
import asyncio
import os

from find_usages.core import find_all_usages_for_all_components
from find_usages.outputs import output_to_stdout, output_to_sqlite, output_to_file
from find_usages.utils import readlines_without_newlines, default_list_of_all_components

parser = argparse.ArgumentParser(
    description="Search a folder full of repositories for usages of components in twirl and nunjucks template and "
    "output as newline delimited json."
)

parser.add_argument(
    "search_path",
    type=str,
    help="Folder with repositories to search for usages within checkout as immediate sub folders",
)

parser.add_argument(
    "--component",
    metavar="NAME",
    type=str,
    help="Limit search to usages of a single component, for example: govukButton",
)

parser.add_argument(
    "--components",
    metavar="FILE",
    default=default_list_of_all_components,
    type=str,
    help="Path to newline delimited text file with names of components to search for instead of the default list",
)

parser.add_argument(
    "--output-file",
    metavar="FILE",
    type=str,
    help="Write output to this file rather than stdout",
)

parser.add_argument(
    "--output-sqlite",
    metavar="FILE",
    type=str,
    help="Write output to a sqlite database rather than to stdout, will be created if it does not yet exist.",
)

parser.add_argument(
    "--output-sqlite-table",
    metavar="TABLE",
    default="usages",
    type=str,
    help="Table to insert usages into within the output database.",
)


async def run():
    args = parser.parse_args()

    components = (
        [args.component]
        if args.component is not None
        else readlines_without_newlines(args.components)
    )

    if not os.path.isdir(args.search_path):
        raise ValueError(
            "Search path folder with git repositories checked out as immediate sub folders",
            args.search_path,
        )

    if len(components) < 1:
        raise ValueError(
            "Component list empty, need the name of at least one component",
        )

    all_usages = find_all_usages_for_all_components(
        in_search_path=args.search_path,
        of_components=components,
    )

    if args.output_file is not None:
        await output_to_file(all_usages, args.output_file)
    elif args.output_sqlite is not None:
        await output_to_sqlite(
            all_usages,
            database=args.output_sqlite,
            table=args.output_sqlite_table,
            batch_size=100,
        )
    else:
        await output_to_stdout(all_usages)


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
