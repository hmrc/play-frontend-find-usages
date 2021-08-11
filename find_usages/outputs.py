"""
Found usages are returned from all core search functions as async generators
which the methods in this module can consume and loop through to output in
different formats.
"""

import json

from aiostream import stream

separators_with_no_spaces_to_match_jq_compact_format = (",", ":")


def as_json_line(usage):
    return json.dumps(
        usage, separators=separators_with_no_spaces_to_match_jq_compact_format
    )


async def output_to_stdout(all_usages):
    async for usage in all_usages:
        print(as_json_line(usage))


async def output_to_file(all_usages, output_file):
    from aiofile import async_open

    async with async_open(output_file, "w") as file:
        async for usage in all_usages:
            await file.write(f"{as_json_line(usage)}\n")


async def output_to_sqlite(all_usages, database, table, batch_size):
    """
    If you need more flexibility you can output to stdout or file and pipe
    that into the sqlite-utils cli directly instead.
    """
    from sqlite_utils import Database

    db = Database(database, recreate=False)

    chunked_usages = stream.chunks(all_usages, batch_size)
    async with chunked_usages.stream() as usages_stream:
        async for usages in usages_stream:
            db[table].insert_all(usages, batch_size=batch_size)
