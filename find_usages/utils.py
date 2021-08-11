import asyncio
import logging
import os
import signal

default_list_of_all_components = os.path.join(
    os.path.dirname(__file__), "resources", "components.csv"
)


def readlines_without_newlines(path):
    """
    Read file into a list of lines, this exists because open(path).readlines() will preserve trailing newlines
    """
    with open(path) as file:
        return [line.strip() for line in file]


def get_default_list_of_all_components():
    return readlines_without_newlines(default_list_of_all_components)


git_repo_latest_commit_cache = {}


async def get_git_repo_latest_commit(path):
    if path not in git_repo_latest_commit_cache:
        process = await asyncio.subprocess.create_subprocess_shell(
            "git rev-parse HEAD",
            cwd=path,
            stdout=asyncio.subprocess.PIPE,
        )

        stdout, _ = await process.communicate()

        git_repo_latest_commit_cache[path] = stdout.decode().strip()

    return git_repo_latest_commit_cache[path]


git_repo_last_updated_at_cache = {}


async def get_git_repo_last_updated_at(repo):
    if repo not in git_repo_last_updated_at_cache:
        process = await asyncio.subprocess.create_subprocess_shell(
            rf'git log -1 --date=short --pretty="format:%cd"',
            cwd=repo,
            stdout=asyncio.subprocess.PIPE,
        )

        stdout, _ = await process.communicate()

        git_repo_last_updated_at_cache[repo] = stdout.decode().strip()

    return git_repo_last_updated_at_cache[repo]


# ugly and brittle way of identifying which library a component came from
libraries = {
    "nunjucks": {
        "g": "alphagov-frontend",
        "f": "alphagov-frontend",
        "h": "hmrc-frontend",
        "t": "hmrc-frontend",
    },
    "twirl": {
        "g": "play-frontend-govuk",
        "h": "play-frontend-hmrc",
        "t": "play-frontend-hmrc",
        "f": "play-frontend-hmrc",
    },
}


def identify_library(template_language, component):
    return libraries[template_language][component[0]]


def identify_language(path):
    return "nunjucks" if os.path.splitext(path)[1] == ".njk" else "twirl"


def parse_alias_and_files(search_result):
    [alias, files_it_has_been_found_in] = search_result.decode().split(":")
    return alias, files_it_has_been_found_in.strip().split(",")


async def write_into(stdin, lines=None):
    stdin.write("\n".join(lines).encode())
    await stdin.drain()
    stdin.close()


subprocesses = []


def terminate_all_subprocesses():
    logging.info(f"Subprocesses to try terminating: {len(subprocesses)}")
    for proc in subprocesses:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            logging.debug(f"Process terminated: {proc}")
        except Exception as e:
            logging.debug(f"Process already terminated: {proc}")


def terminate_all_subprocesses_on_exception(function):
    def decorated(*args, **kwargs):
        async def inner():
            try:
                async for v in function(*args, **kwargs):
                    yield v
            except Exception as e:
                logging.exception(e)
                terminate_all_subprocesses()

        return inner()

    return decorated


async def run(command, working_dir=None, files_to_search=None):
    search_process = await asyncio.create_subprocess_shell(
        command,
        stdin=asyncio.subprocess.PIPE if files_to_search is not None else None,
        stdout=asyncio.subprocess.PIPE,
        limit=1024 * 256,
        cwd=working_dir,
        preexec_fn=os.setsid,
    )

    subprocesses.append(search_process)

    if files_to_search is not None:
        await write_into(search_process.stdin, files_to_search)

    while True:
        search_result = await search_process.stdout.readline()
        if not search_result:
            break
        yield search_result

    await search_process.wait()
