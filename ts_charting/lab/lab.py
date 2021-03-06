"""
    Conceptually a Lab is a JSON-able working area. 

    A station, at least for now, maps to a Figure. 

    I'm not 100% sure these abstractions are the way to go, or
    if this even belongs in this module.
"""
from collections import OrderedDict
from ts_charting import json

from ts_charting import Figure, scf
from ts_charting.util import process_signal

class FakeFigure(object):
    """
    Figure that does no plotting.
    """
    def __getattr__(self, name):
        return self.fake_call

    def fake_call(self, *args, **kwargs):
        pass

class Lab(object):
    def __init__(self, draw=False):
        self.draw = draw
        self.data = {}
        self.plots = {}
        self.stations = OrderedDict()

    def station(self, name):
        station = Station(self, name, draw=self.draw)
        self.stations[name] = station
        scf(station)
        return station

    def to_json(self):
        dct = {}
        dct['stations'] = self.stations
        return json.to_json(dct)

class Station(object):
    def __init__(self, lab, name, draw=False):
        self.lab = lab
        self.name = name
        if draw:
            self.figure = Figure(1, warn=False)
        else:
            self.figure = FakeFigure()
        self.layers = []

    def plot_markers(self, name, series, yvalues=None, xindex=None, **kwargs):
        geom = {'type': 'marker'}
        # dont support xindex for now
        #geom['xindex'] = xindex
        geom.update(kwargs)

        if yvalues is not None:
            series = process_signal(series, yvalues)
        self.add_layer(name, series, geom)
        self.figure.plot_markers(name, series, **kwargs)

    def plot(self, label, series, **kwargs):
        geom = {'type': 'line'}
        geom.update(kwargs)
        self.add_layer(label, series, geom)
        self.figure.plot(label, series, **kwargs)

    def ohlc(self, df, width=0.3):
        # ohlc_df = normalize_ohlc(df)
        self.add_layer('candlestick', df, {'type': 'candlestick', 'width': .03})
        self.figure.ohlc(df, width=width)

    def add_layer(self, name, data, geoms):
        if not isinstance(geoms, list):
            geoms = [geoms]

        self.layers.append({'name': name, 'data': data, 'geoms':geoms})

    def to_json(self):
        dct = self.__dict__.copy()
        del dct['figure']
        del dct['lab']
        index = self.consolidate_index()
        dct['index'] = index
        return json.to_json(dct)

    def consolidate_index(self):
        """
        Take the index of every layer's data and create a single index. Currently 
        acts like the regular Grapher and uses the first data's index as the master
        index. All other indexes get reindex to that one
        """
        index = None
        for layer in self.layers:
            if index is None:
                index = layer['data'].index
                continue
            # reindex the layer data and any yvalues passed into its geoms
            layer['data'] = layer['data'].reindex(index) 
        return index
