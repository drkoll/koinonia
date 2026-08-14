import sys

from koinonia.aphesis import _witness as aphesis_w
from koinonia.circle import _witness as circle_w
from koinonia.netting import _witness as netting_w

if __name__ == "__main__":
    for w in (circle_w, aphesis_w, netting_w):
        rc = w()
        if rc != 0:
            sys.exit(rc)
    sys.exit(0)
