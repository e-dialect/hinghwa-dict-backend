import numpy as np
import time


class FFT:
    """A mechanism for identifying the dominant frequencies
    in time ranges in an audio file."""

    def __init__(self, input_file, chunk_size=1024, overlap_ratio=2):
        """Set up an file for FFT processing.
        The constructor doesn't actually do the processing.
        @param input_file The file we'll read audio data from. The should
        be a AbstractInputFile-like object
        @param chunk_size The size of the chunks to put through FFT."""
        self.input_file = input_file
        self.chunk_size = chunk_size
        self.overlap_ratio = overlap_ratio

    def series(self, chunks=-1):
        """Return the FFTs of samples of audio chunks. The number of FFT bins will be almost
        double the number of chunks, because we compute two bins per chunk, one that is
        halfway overlapping the next one.
        @param chunks The number of chunks to read and return. -1 means all. Must be positive number
        otherwise. If there isn't enough audio data to read all of these chunks, we may read less.
        @param f The number of frequency values to return per chunk. -1 means all. Must be positive number
        less than chunk size otherwise."""

        if chunks == -1:
            chunks = int(self.input_file.get_total_samples() / self.chunk_size)

        # get all the audio samples we'll be working with
        samples = self.input_file.get_audio_samples(chunks * self.chunk_size)
        # mix those samples down into one channel
        samples = samples.mean(axis=0)
        result = self.specgram(samples, NFFT=self.chunk_size,
                               window=FFT.__window_hanning,
                               noverlap=int(self.chunk_size / self.overlap_ratio))
        result = result.transpose()
        return result

    def specgram(self, x, NFFT, window, noverlap):
        """Compute a spectrogram of the given audio samples.

        This is a stripped-down version of the code inside
        matplotlib.mlab.specgram().

        Code in this method is taken from the file
        matplotlib/lib/matplotlib/mlab.py, in the
        method _spectral_helper().
        It has been stripped down to avoid performing
        unneeded checks and redundant computations, since
        our problem is more specific than the problem
        that _spectral_helper solves.

        Original code is copyright (c) 2002-2011 John D. Hunter;
        All Rights Reserved"""

        numFreqs = NFFT // 2 + 1
        windowVals = window(np.ones((NFFT,), x.dtype))

        step = NFFT - noverlap
        ind = np.arange(0, len(x) - NFFT + 1, step)
        n = len(ind)
        Pxx = np.zeros((numFreqs, n), np.complex_)

        # do the ffts of the slices
        for i in range(n):
            thisX = x[ind[i]:ind[i] + NFFT]
            thisX = windowVals * thisX
            fx = np.fft.fft(thisX, n=NFFT)
            Pxx[:, i] = np.conjugate(fx[:numFreqs]) * fx[:numFreqs]

        return Pxx

    def base_freq(self):
        """Returns the base frequency. This is the frequency corresponding
        to the first index in the arrays returned by series()(?)."""
        return float(self.input_file.get_sample_rate()) / float(self.chunk_size)

    @staticmethod
    def __window_hanning(x):
        "return x times the hanning window of len(x)"
        return np.hanning(len(x)) * x
