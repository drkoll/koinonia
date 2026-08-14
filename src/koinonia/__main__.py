import sys

from koinonia.allocate import _witness as allocate_w
from koinonia.aphesis import _witness as aphesis_w
from koinonia.circle import _witness as circle_w
from koinonia.leverage import _witness as leverage_w
from koinonia.netting import _witness as netting_w

if __name__ == "__main__":
    for w in (circle_w, aphesis_w, netting_w, allocate_w, leverage_w):
        rc = w()
        if rc != 0:
            sys.exit(rc)
    sys.exit(0)
