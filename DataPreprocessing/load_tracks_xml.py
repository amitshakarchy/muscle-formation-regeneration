import pytrackmate as tm

# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 18:34:11 2020

@author: Oron
"""


def load_tracks_xml(location):

    df = tm.trackmate_peak_import(location, get_tracks=True)  ## modified!
    tracks = list()
    ##### Grid count
    for label, labeld_df in df.groupby('label'):
        tracks.append(labeld_df)
    return tracks, df

def remove_short_tracks(tracks, threshold):
    # remove tracks shorter than threshold
    t = 0
    while t < len(tracks):
        if len(tracks[t]) < threshold:
            tracks.pop(t)
        else:
            t += 1
    return tracks