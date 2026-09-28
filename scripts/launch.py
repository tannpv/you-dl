"""PyInstaller entry point: keep multiprocessing dispatch before Qt imports."""

import multiprocessing
import sys
from pathlib import Path

if __name__ == "__main__":
    multiprocessing.freeze_support()
    from you_dl.diagnostics import SELF_TEST_FLAG, self_test

    if len(sys.argv) == 3 and sys.argv[1] == SELF_TEST_FLAG:
        sys.exit(self_test(Path(sys.argv[2])))
    from you_dl.app import main

    main()
