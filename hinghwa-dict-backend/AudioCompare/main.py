#!/usr/bin/env python
import os.path

from AudioCompare.error import *
from AudioCompare.Matcher import Matcher
from argparse import ArgumentParser


class Arg:
    def __init__(self, dirs=[], files=[]):
        self.dirs = dirs
        self.files = files


def audio_matcher(args: Arg):
    """Our main control flow."""

    # parser = ArgumentParser(
    #     description="Compare two audio files to determine if one "
    #                 "was derived from the other. Supports WAVE and MP3.",
    #     prog="audiomatch")
    # parser.add_argument("-f", action="append",
    #                     required=False, dest="files",
    #                     default=list(),
    #                     help="A file to examine.")
    # parser.add_argument("-d", action="append",
    #                     required=False, dest="dirs",
    #                     default=list(),
    #                     help="A directory of files to examine. "
    #                          "Directory must contain only audio files.")
    # args = parser.parse_args()

    search_paths = args.dirs + args.files

    if len(search_paths) != 2:
        die("Must provide exactly two input files or directories.")
    code = 0
    # Use our matching system
    matcher = Matcher(search_paths[0], search_paths[1])
    results = matcher.match()
    a = {}
    ans = {}
    for match in results:
        if not match.success:
            code = 1
            warn(match.message)
        else:
            filename = os.path.split(match.file1)[-1]
            if filename not in a:
                a[filename] = []
            a[filename].append((os.path.split(match.file2)[-1], match.score))
    for file1 in a.keys():
        a[file1].sort(key=lambda x: x[1], reverse=True)
        ans[file1] = a[file1][0][0] if a[file1][0][1] > 0 else None
    return ans


if __name__ == "__main__":
    exit(audio_matcher())
