import sys


def die(msg):
    print(sys.stderr, "ERROR: {e}".format(e=msg))
    exit(1)


def warn(msg):
    print(sys.stderr, "ERROR: {e}".format(e=msg))


