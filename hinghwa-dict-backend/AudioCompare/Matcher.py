import math
import itertools
import pickle
import shutil

from AudioCompare.FFT import FFT
import numpy as np
from collections import defaultdict
from AudioCompare.InputFile import InputFile
import multiprocessing
import os
import stat
from AudioCompare.error import *
from AudioCompare.common import *

BUCKET_SIZE = 20
BUCKETS = 4
BITS_PER_NUMBER = int(math.ceil(math.log(BUCKET_SIZE, 2)))
assert (BITS_PER_NUMBER * BUCKETS) <= 32

NORMAL_CHUNK_SIZE = 1024
NORMAL_SAMPLE_RATE = 44100.0

SCORE_THRESHOLD = 0


class FileResult(BaseResult):
    """The result of fingerprinting
    an entire audio file."""

    def __init__(self, fingerprints, file_len, filename):
        super(FileResult, self).__init__(True, "")
        self.fingerprints = fingerprints
        self.file_len = file_len
        self.filename = filename

    def __str__(self):
        return self.filename


class ChunkInfo(object):
    """These objects will be the values in
    our master hashes that map fingerprints
    to instances of this class."""

    def __init__(self, chunk_index, filename):
        self.chunk_index = chunk_index
        self.filename = filename

    def __str__(self):
        return "Chunk: {c}, File: {f}".format(c=self.chunk_index, f=self.filename)


class MatchResult(BaseResult):
    """The result of comparing two files."""

    def __init__(self, file1, file2, file1_len, file2_len, score):
        super(MatchResult, self).__init__(True, "")
        self.file1 = file1
        self.file2 = file2
        self.file1_len = file1_len
        self.file2_len = file2_len
        self.score = score

    def __str__(self):
        short_file1 = os.path.basename(self.file1)
        short_file2 = os.path.basename(self.file2)
        if self.score > SCORE_THRESHOLD:
            if self.file1_len < self.file2_len:
                return "MATCH {f1} {f2} ({s})".format(
                    f1=short_file1, f2=short_file2, s=self.score
                )
            else:
                return "MATCH {f2} {f1} ({s})".format(
                    f1=short_file1, f2=short_file2, s=self.score
                )
        else:
            return "NO MATCH"


def _to_fingerprints(freq_chunks):
    """Examine the results of running chunks of audio
    samples through FFT. For each chunk, look at the frequencies
    that are loudest in each "bucket." A bucket is a series of
    frequencies. Return the indices of the loudest frequency in each
    bucket in each chunk. These indices will be encoded into
    a single number per chunk."""
    chunks = len(freq_chunks)
    fingerprints = np.zeros(chunks, dtype=np.uint32)
    # Examine each chunk independently
    for chunk in range(chunks):
        fingerprint = 0
        for bucket in range(BUCKETS):
            start_index = bucket * BUCKET_SIZE
            end_index = (bucket + 1) * BUCKET_SIZE
            bucket_vals = freq_chunks[chunk][start_index:end_index]
            max_index = bucket_vals.argmax()
            fingerprint += max_index << (bucket * BITS_PER_NUMBER)
        fingerprints[chunk] = fingerprint

    # return the indexes of the loudest frequencies
    return fingerprints


def _file_fingerprint(filename):
    """Read the samples from the files, run them through FFT,
    find the loudest frequencies to use as fingerprints,
    turn those into a hash table.
    Returns a 2-tuple containing the length
    of the file in seconds, and the hash table."""

    # Open the file
    try:
        file = InputFile(filename)

        # Read samples from the input files, divide them
        # into chunks by time, and convert the samples in each
        # chunk into the frequency domain.
        # The chunk size is dependent on the sample rate of the
        # file. It is important that each chunk represent the
        # same amount of time, regardless of the sample
        # rate of the file.
        chunk_size_adjust_factor = NORMAL_SAMPLE_RATE / file.get_sample_rate()
        fft = FFT(file, int(NORMAL_CHUNK_SIZE / chunk_size_adjust_factor))
        series = fft.series()

        file_len = file.get_total_samples() / file.get_sample_rate()

        file.close()

        # Find the indices of the loudest frequencies
        # in each "bucket" of frequencies (for every chunk).
        # These loud frequencies will become the
        # fingerprints that we'll use for matching.
        # Each chunk will be reduced to a tuple of
        # 4 numbers which are 4 of the loudest frequencies
        # in that chunk.
        # Convert each tuple in winners to a single
        # number. This number is unique for each possible
        # tuple. This hopefully makes things more
        # efficient.
        fingerprints = _to_fingerprints(series)

    except Exception as e:
        return FileErrorResult(str(e))

    return FileResult(fingerprints, file_len, filename)


class Matcher(object):
    """Create an instance of this class to use our matching system."""

    def __init__(self, dir1, dir2):
        """The two arguments should be strings that are
        file or directory paths. For files, we will simply
        examine these files. For directories, we will scan
        them for files."""
        self.dir1 = dir1
        self.dir2 = dir2
        if os.path.split(dir2)[1] != "submit":
            self.change = True
        else:
            self.change = False
        print(self.dir2, self.change)

    @staticmethod
    def __search_dir(dir):
        """Returns the regular files residing
        in the given directory, OR if the input
        is a regular file, return a 1-element
        list containing this file. All paths
        returned will be absolute paths."""

        results = []
        # Get the absolute path of our search dir
        abs_dir = os.path.abspath(dir)
        # Get info about the directory provide
        dir_stat = os.stat(abs_dir)

        # If it's really a file, just
        # return the name of it
        if stat.S_ISREG(dir_stat.st_mode):
            results.append(abs_dir)
            return results

        # If it's neither a file nor directory,
        # bail out
        if not stat.S_ISDIR(dir_stat.st_mode):
            die("{d} is not a directory or a regular file.".format(d=abs_dir))

        # Scan through the contents of the
        # directory (non-recursively).
        contents = os.listdir(abs_dir)
        for node in contents:
            abs_node = abs_dir + os.sep + node
            node_stat = os.stat(abs_node)
            # If we find a regular file, add
            # that to our results list, otherwise
            # warn the user.
            if stat.S_ISREG(node_stat.st_mode):
                results.append(abs_node)
            else:
                warn(
                    "An inode that is not a regular file was found at {f}".format(
                        abs_node
                    )
                )

        return results

    @staticmethod
    def __combine_hashes(files):
        """Take a list of FileResult objects and
        create a hash that maps all of their fingerprints
        to ChunkInfo objects."""
        master = defaultdict(list)
        for f in files:
            for chunk in range(len(f.fingerprints)):
                hash = f.fingerprints[chunk]
                master[hash].append(ChunkInfo(chunk, f.filename))

        return master

    @staticmethod
    def __file_lengths(files):
        """Take a list of FileResult objects and
        create a hash that maps their filenames
        to the length of each file, in seconds."""
        results = {}
        for f in files:
            results[f.filename] = f.file_len

        return results

    @staticmethod
    def __report_file_matches(file, master_hash, file_lengths):
        """Find files from the master hash that match
        the given file.
        @param file A FileResult object that is our query
        @param master_hash The data to search through
        @param file_lengths A hash mapping filenames to file lengths
        @return A list of MatchResult objects, one for every file
        that was represented in master_hash"""

        results = []

        # A hash that maps filenames to "offset" hashes. Then,
        # an offset hash maps the difference in chunk numbers of
        # the matches we will find.
        # We'll map those differences to the number of matches
        # found with that difference.
        # This allows us to see if many fingerprints
        # from different files occurred at the same
        # time offsets relative to each other.
        file_match_offsets = {}
        for f in file_lengths:
            file_match_offsets[f] = defaultdict(lambda: 0)

        # For each chunk in the query file
        for query_chunk_index in range(len(file.fingerprints)):
            # See if that chunk's fingerprint is in our master hash
            chunk_fingerprint = file.fingerprints[query_chunk_index]
            if chunk_fingerprint in master_hash:
                # If it is, record the offset between our query chunk
                # and the found chunk
                for matching_chunk in master_hash[chunk_fingerprint]:
                    offset = matching_chunk.chunk_index - query_chunk_index
                    file_match_offsets[matching_chunk.filename][offset] += 1

        # For each file that was in master_hash,
        # we examine the offsets of the matching fingerprints we found
        for f in file_match_offsets:
            offsets = file_match_offsets[f]

            # The length of the shorter file is important
            # to deciding whether two audio files match.
            min_len = min(file_lengths[f], file.file_len)

            # max_offset is the highest number of times that two matching
            # hash keys were found with the same time difference
            # relative to each other.
            if len(offsets) != 0:
                max_offset = max(offsets.values())
            else:
                max_offset = 0

            # The score is the ratio of max_offset (as explained above)
            # to the length of the shorter file. A short file that should
            # match another file will result in less matching fingerprints
            # than a long file would, so we take this into account. At the
            # same time, a long file that should *not* match another file
            # will generate a decent number of matching fingerprints by
            # pure chance, so this corrects for that as well.
            if min_len > 0:
                score = max_offset / min_len
            else:
                score = 0

            results.append(
                MatchResult(file.filename, f, file.file_len, file_lengths[f], score)
            )

        return results

    def match(self):
        """Takes two AbstractInputFiles as input,
        and returns a boolean as output, indicating
        if the two files match."""

        dir1_files = Matcher.__search_dir(self.dir1)
        dir2_files = Matcher.__search_dir(self.dir2)

        # Try to determine how many
        # processors are in the computer
        # we're running on, to determine
        # the appropriate amount of parallelism
        # to use
        try:
            cpus = multiprocessing.cpu_count()
        except NotImplementedError:
            cpus = 1

        # Construct a process pool to give the task of
        # fingerprinting audio files
        # pool = multiprocessing.Pool(cpus)
        try:
            # Get the fingerprints from each input file.
            # Do this using a pool of processes in order
            # to parallelize the work neatly.
            map1_result = [_file_fingerprint(item) for item in dir1_files]
            # map2_result = [_file_fingerprint(item) for item in dir2_files]
            # map1_result = pool.map_async(_file_fingerprint, dir1_files)
            dir1_results = map1_result
            if self.change or not os.path.exists(
                os.path.join(os.getcwd(), "submit结果存储.pkl")
            ):
                map2_result = [_file_fingerprint(item) for item in dir2_files]
                dir2_results = map2_result
                with open(os.path.join(os.getcwd(), "submit结果存储.pkl"), "wb") as f:
                    pickle.dump(dir2_results, f)
            else:
                with open(os.path.join(os.getcwd(), "submit结果存储.pkl"), "rb") as f:
                    dir2_results = pickle.load(f)
            # Wait for pool to finish processing
            # pool.close()
            # pool.join()
            # dir1_results = map1_result
            # dir2_results = map2_result
            # Get results from process pool

            shutil.rmtree(os.path.join(os.getcwd(), "temp"))
        except KeyboardInterrupt:
            # pool.terminate()
            raise

        results = []

        # If there was an error in fingerprinting a file,
        # add a special ErrorResult to our results list
        # results.extend(filter(lambda x: not x.success, dir1_results))
        # results.extend(filter(lambda x: not x.success, dir2_results))

        # Proceed only with fingerprints that were computed
        # successfully
        dir1_successes = list(
            filter(lambda x: x.success and x.file_len > 0, dir1_results)
        )
        dir2_successes = list(
            filter(lambda x: x.success and x.file_len > 0, dir2_results)
        )

        # Empty files should match other empty files
        # Our matching algorithm will not report these as a match,
        # so we have to make a special case for it.
        # dir1_empty_files = list(filter(lambda x: x.success and x.file_len == 0, dir1_results))
        # dir2_empty_files = list(filter(lambda x: x.success and x.file_len == 0, dir2_results))

        # Every empty file should match every other empty file
        # for empty_file1, empty_file2 in itertools.product(dir1_empty_files, dir2_empty_files):
        #     results.append(
        #         MatchResult(empty_file1.filename, empty_file2.filename, empty_file1.file_len, empty_file2.file_len,
        #                     SCORE_THRESHOLD + 1))

        # This maps filenames to the lengths of the files
        dir1_file_lengths = Matcher.__file_lengths(dir1_successes)
        dir2_file_lengths = Matcher.__file_lengths(dir2_successes)

        # Get the combined sizes of the files in our two search
        # paths
        dir1_size = len(dir1_file_lengths.values())
        dir2_size = len(dir2_file_lengths.values())

        # Whichever search path has more data in it is the
        # one we want to put in the master hash, and then query
        # via the other one
        # if dir1_size < dir2_size:
        dir_successes = dir1_successes
        master_hash = Matcher.__combine_hashes(dir2_successes)
        file_lengths = dir2_file_lengths
        # else:
        #     dir_successes = dir2_successes
        #     master_hash = Matcher.__combine_hashes(dir1_successes)
        #     file_lengths = dir1_file_lengths

        # Loop through each file in the first search path our
        # program was given.
        for file in dir_successes:
            # For each file, check its fingerprints against those in the
            # second search path. For matching
            # fingerprints, look up the the times (chunk number)
            # that the fingerprint occurred
            # in each file. Store the time differences in
            # offsets. The point of this is to see if there
            # are many matching fingerprints at the
            # same time difference relative to each
            # other. This indicates that the two files
            # contain similar audio.
            file_matches = Matcher.__report_file_matches(
                file, master_hash, file_lengths
            )
            results.extend(file_matches)

        return results
