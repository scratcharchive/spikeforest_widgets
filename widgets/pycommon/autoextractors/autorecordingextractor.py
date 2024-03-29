from mountaintools import client as mt
from mountaintools import MountainClient
import h5py
import spikeextractors as se
import numpy as np
from .mdaextractors import MdaRecordingExtractor
from ...pycommon.load_nwb_item import load_nwb_item

class AutoRecordingExtractor(se.RecordingExtractor):
    def __init__(self, arg):
        super().__init__()
        self._hash = None
        if isinstance(arg, se.RecordingExtractor):
            self._recording = arg
            self.copy_channel_properties(recording=self._recording)
        else:
            self._recording = None
            self._client = MountainClient()
            if 'download_from' in arg:
                self._client.configDownloadFrom(arg['download_from'])
            if 'path' in arg:
                path = arg['path']
                if self._client.isFile(path):
                    file_path = self._client.realizeFile(path=path)
                    if not file_path:
                        raise Exception('Unable to realize file: {}'.format(path))
                    self._init_from_file(file_path, original_path=path, kwargs=arg)
                else:
                    raise Exception('Not a file: {}'.format(path))
            else:
                raise Exception('Unable to initialize recording extractor')
    def _init_from_file(self, path: str, *, original_path: str, kwargs: dict):
        if 'nwb_path' in kwargs:
            self._recording = NwbElectricalSeriesRecordingExtractor(path=path, nwb_path=kwargs['nwb_path'])
        elif original_path.endswith('.mda'):
            if 'samplerate' not in kwargs:
                raise Exception('Missing argument: samplerate')
            samplerate = kwargs['samplerate']
            self._recording = MdaRecordingExtractor(timeseries_path=path, samplerate=samplerate)
            hash0 = self._client.sha1OfObject(dict(
                timeseries_path=self._client.computeFileSha1(path),
                samplerate=samplerate
            ))
            setattr(self, 'hash', hash0)
        else:
            raise Exception('Unsupported format for {}'.format(original_path))
    
    def hash(self):
        if not self._hash:
            if hasattr(self._recording, 'hash'):
                if type(self._recording.hash) == str:
                    self._hash = self._recording.hash
                else:
                    self._hash = self._recording.hash()
            else:
                self._hash = _samplehash(self._recording)
        return self._hash

    def get_channel_ids(self):
        return self._recording.get_channel_ids()

    def get_num_frames(self):
        return self._recording.get_num_frames()

    def get_sampling_frequency(self):
        return self._recording.get_sampling_frequency()

    def get_traces(self, **kwargs):
        return self._recording.get_traces(**kwargs)

class NwbElectricalSeriesRecordingExtractor(se.RecordingExtractor):
    def __init__(self, *, path, nwb_path):
        super().__init__()
        self._path = path
        self._nwb_path = nwb_path
        with h5py.File(self._path, 'r') as f:
            X = load_nwb_item(file=f, nwb_path=self._nwb_path)
            self._samplerate = X['starting_time'].attrs['rate']
            self._num_timepoints = X['data'].shape[0]
            self._num_channels = X['data'].shape[1]

    def get_channel_ids(self):
        return list(range(self._num_channels))

    def get_num_frames(self):
        return self._num_timepoints

    def get_sampling_frequency(self):
        return self._samplerate

    def get_traces(self, channel_ids=None, start_frame=None, end_frame=None):
        if start_frame is None:
            start_frame = 0
        if end_frame is None:
            end_frame = self.get_num_frames()
        if channel_ids is None:
            channel_ids = self.get_channel_ids()
        with h5py.File(self._path, 'r') as f:
            X = load_nwb_item(file=f, nwb_path=self._nwb_path)
            return X['data'][start_frame:end_frame, :][:, channel_ids].T

def _samplehash(recording):
    from mountaintools import client as mt
    obj = {
        'channels': tuple(recording.get_channel_ids()),
        'frames': recording.get_num_frames(),
        'data': _samplehash_helper(recording)
    }
    return mt.sha1OfObject(obj)


def _samplehash_helper(recording):
    rng = np.random.RandomState(37)
    n_samples = min(recording.get_num_frames() // 1000, 100)
    inds = rng.randint(low=0, high=recording.get_num_frames(), size=n_samples)
    h = 0
    for i in inds:
        t = recording.get_traces(start_frame=i, end_frame=i + 100)
        h = hash((hash(bytes(t)), hash(h)))
    return h