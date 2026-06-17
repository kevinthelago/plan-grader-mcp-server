import importlib
import pkgutil

import plan_grader.tools
from plan_grader.app import mcp


def main() -> None:
    for _finder, name, _ispkg in pkgutil.iter_modules(
        plan_grader.tools.__path__,
        plan_grader.tools.__name__ + ".",
    ):
        importlib.import_module(name)
    mcp.run()


if __name__ == "__main__":
    main()
