import sys

from framepick.app import main
from framepick.selftest import run_self_test


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--self-test":
        run_self_test(sys.argv[2], sys.argv[3])
        raise SystemExit(0)
    raise SystemExit(main())
