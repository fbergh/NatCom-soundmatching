from abc import ABC
import numpy as np
import itertools
from synthplayer.oscillators import Sine, Triangle, Square, SquareH, Sawtooth
from synthplayer.oscillators import Pulse, WhiteNoise, Semicircle, MixingFilter
from synthplayer.oscillators import Filter, Oscillator
from synthplayer import params
from typing import Generator, List
from scipy.signal import butter, filtfilt


osc_1_options = {
    'Sine': Sine,
    'Triangle': Triangle,
    'Square': Square,
    'SquareH': SquareH,
    'Sawtooth': Sawtooth,
    'Pulse': Pulse,
    'Semicircle': Semicircle
}

osc_2_options = {
    'Sine': Sine,
    'Triangle': Triangle,
    'Square': Square,
    'SquareH': SquareH,
    'Sawtooth': Sawtooth,
    'Pulse': Pulse,
    'WhiteNoise': WhiteNoise,
    'Semicircle': Semicircle
}


class Synth(ABC):
    def __init__(self, sr=44100):
        """
        Parameters
        ----------
        sr : int
            Samplerate used for the resulting sounds
        """
        self.sr = sr
        self.set_parameters()

    def set_parameters(self, **kwargs):
        """Sets the parameters of the synth"""
        self.osc_1_name = kwargs.get('osc_1', 'Sine')
        self.osc_1 = osc_1_options[self.osc_1_name]
        self.osc_2_name = kwargs.get('osc_2', 'Sine')
        self.osc_2 = osc_2_options[self.osc_2_name]
        self.amp_1 = kwargs.get('amp_1', 0.5)
        self.amp_2 = kwargs.get('amp_2', 0.5)
        self.phase_1 = kwargs.get('phase_1', 0)
        self._normalise_amp()
        self.cutoff = kwargs.get('cutoff', 10000)

    def get_parameters(self):
        """Returns a dict with the current paramters"""
        return {
            'osc_1': self.osc_1_name,
            'osc_2': self.osc_2_name,
            'amp_1': self.amp_1,
            'amp_2': self.amp_2,
            'phase_1': self.phase_1,
            'cutoff': self.cutoff,
        }

    def _get_raw_data_from_obj(self, obj, duration):
        num_blocks = self.sr*duration//params.norm_osc_blocksize
        tmp = np.array(list(itertools.islice(obj.blocks(), num_blocks)))
        return tmp.flatten()

    def _normalise_amp(self):
        """Rescales the amplitude of the two classifiers so that they
           sum to 1"""
        self.amp_1 = self.amp_1 / (self.amp_1+self.amp_2)
        self.amp_2 = 1 - self.amp_1

    def _hookup_modules(self, note):
        """Creates oscillators with the correct parameters pipeline"""
        osc1 = self.osc_1(note,
                          amplitude=self.amp_1,
                          phase=self.phase_1,
                          samplerate=self.sr)
        osc2 = self.osc_2(note,
                          amplitude=self.amp_2,
                          samplerate=self.sr)
        mix = MixingFilter(osc1, osc2)
        self.out = LowPassFilter(mix, cutoff=self.cutoff, samplerate=self.sr)

    def get_sound_array(self, note=440, duration=1):
        """Returns a sound for the set parameters

        Returns
        -------
        sound_array : np.ndarray
            The sound for the given note and duration
        """
        self._hookup_modules(note)
        return self._get_raw_data_from_obj(self.out, duration)


class LowPassFilter(Filter):
    """
    A low pass filter applied to an oscillator with the given cutoff
    """
    def __init__(self, source: Oscillator, cutoff: float, samplerate: float) -> None:
        assert isinstance(source, Oscillator)
        super().__init__([source])
        self.cutoff = cutoff
        self.samplerate

    def blocks(self) -> Generator[List[float], None, None]:
        source_blocks = self.sources[0].blocks()
        try:
            while True:
                block = next(source_blocks)
                b, a = butter(4, self.cutoff / (self.samplerate / 2.), 'low')
                yield filtfilt(b, a, block)
        except StopIteration:
            return
