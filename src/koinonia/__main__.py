import sys

from koinonia.aphesis import _witness as aphesis_w
from koinonia.circle import _witness as circle_w

if __name__ == "__main__":
    rc = circle_w()
    sys.exit(aphesis_w() if rc == 0 else rc)
