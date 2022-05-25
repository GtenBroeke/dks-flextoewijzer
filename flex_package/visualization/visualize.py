"""
Module containing functions for visualization.
"""

import logging
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

logger = logging.getLogger(__name__)


def plot_afvoer(df, origin, destination):
    fig, ax = plt.subplots()
    ax.plot(df['time'], df['stock'])
    plt.xlabel("Tijd")
    plt.ylabel("Aantal RC")
    myFmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(myFmt)
    plt.title('Afvoer ' + str(origin) + ' -> ' + str(destination))
    plt.show()
    return plt


def plot_afvoer_flex(df, t, origin, destination):
    fig, ax = plt.subplots()
    ax.plot(df['time'], df['stock_corrected'], label='Voorspelling realtime')
    ax.plot(df['time'], df['stock'], label='Baseline voorspelling')
    plt.xlabel("Tijd")
    plt.ylabel("Aantal RC")
    flex_times = list(df[df['event'] == 'Flex']['time'])
    plt.axvline(x=t)
    if len(flex_times) > 1:
        for t in flex_times:
            plt.axvline(x=t, color='r', linestyle=':')
    legend = ax.legend(loc='upper left', shadow=True, fontsize='x-large')
    myFmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(myFmt)
    plt.title('Afvoer ' + str(origin) + ' -> ' + str(destination))
    plt.show()
    return plt

