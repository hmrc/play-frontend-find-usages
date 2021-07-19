import os
import html
import json

from datasette import hookimpl
from jinja2 import Markup, Template


with open(
    os.path.join(os.path.dirname(__file__), "render_code_sample.html.jinja2")
) as template:
    code_sample = Template(template.read())


@hookimpl
def render_cell(value, column, table, database, datasette):
    config = datasette.plugin_config(
        "datasette-render-code-sample", database=database, table=table
    )
    if not config:
        return None
    if column in config["columns"]:
        column_json = json.loads(value)

        # TODO maybe capture the complete first line if not an argument and use dedent to remove common whitespace

        escaped_code = (
            "<code>"
            + html.escape(column_json["code"]).replace("\n", "</code>\n<code>")  # so we can show line numbers
            + "</code>"
        )

        return Markup(
            code_sample.render(
                escaped_code=escaped_code,
                github_url=column_json["github_url"],
                file_path=column_json["path"],
                line_number=column_json["line_number"],
            )
        )
