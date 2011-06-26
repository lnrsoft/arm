"""
Base class for implementing graphing functionality.
"""

import random
import sys

from collections import deque

import gobject
import gtk

from TorCtl import TorCtl
from util import uiTools, torTools

from cagraph.ca_graph import CaGraph
from cagraph.axis.xaxis import CaGraphXAxis
from cagraph.axis.yaxis import CaGraphYAxis
from cagraph.ca_graph_grid import CaGraphGrid
from cagraph.series.area import CaGraphSeriesArea

GRAPH_INTERVAL = 30

class GraphStats(TorCtl.PostEventListener):
  def __init__(self, builder):
    TorCtl.PostEventListener.__init__(self)

    self.builder = builder

    self.graphs = { 'primary' : None, 'secondary' : None }
    self.data = {
        'primary'   : deque([0.0] * GRAPH_INTERVAL),
        'secondary' : deque([0.0] * GRAPH_INTERVAL)}

    self.total = {'primary': 0.0,  'secondary' : 0.0}
    self.ticks = {'primary': 0,  'secondary' : 0}

  def pack_widgets(self):
    self._pack_graph_widget('primary')
    self._pack_graph_widget('secondary')

    gobject.timeout_add(1000, self.draw_graph, 'primary')
    gobject.timeout_add(1000, self.draw_graph, 'secondary')
    gobject.timeout_add(1000, self.update_labels, 'primary')
    gobject.timeout_add(1000, self.update_labels, 'secondary')

  def _pack_graph_widget(self, name):
    graph = CaGraph()
    placeholder = self.builder.get_object('placeholder_graph_%s' % name)
    placeholder.pack_start(graph)

    xaxis = CaGraphXAxis(graph)
    yaxis = CaGraphYAxis(graph)

    xaxis.min = 0
    xaxis.max = GRAPH_INTERVAL - 1
    xaxis.axis_style.draw_labels = False
    yaxis.axis_style.label_color = (0, 0, 0)

    graph.axiss.append(xaxis)
    graph.axiss.append(yaxis)

    series = CaGraphSeriesArea(graph, 0, 1)

    line_colors = {'primary' : (1.0, 0.0, 1.0, 1.0), 'secondary' : (0.0, 1.0, 0.0, 1.0)}
    fill_colors = {'primary' : (1.0, 0.0, 1.0, 0.3), 'secondary' : (0.0, 1.0, 0.0, 0.3)}
    series.style.line_color = line_colors[name]
    series.style.fill_color = fill_colors[name]

    graph.seriess.append(series)
    graph.grid = CaGraphGrid(graph, 0, 1)

    self.graphs[name] = graph

    return graph

  def get_graph_data(self, name):
    packed_data = []

    for (index, value) in enumerate(self.data[name]):
      packed_data.append((index, value))

    return packed_data

  def is_graph_data_zero(self, name):
    data = self.data[name]
    return len(data) == map(int, data).count(0)

  def draw_graph(self, name):
    graph = self.graphs[name]
    data = self.get_graph_data(name)

    graph.seriess[0].data = data
    if not self.is_graph_data_zero(name):

      for (index, axis) in enumerate(graph.axiss):
        if axis.type != 'xaxis':
          graph.auto_set_yrange(index)

    graph.queue_draw()

    return True

  def update_labels(self, name):
    avg = 0

    try:
      avg = self.total[name] / float(self.ticks[name])
    except ZeroDivisionError:
      pass

    msg = "avg: %s/s, total: %s" % (uiTools.getSizeLabel(avg, 2, isBytes=False),
                                    uiTools.getSizeLabel(self.total[name], 2))
    label = self.builder.get_object('label_graph_%s_bottom' % name)
    label.set_text(msg)

    return True

  def update_header(self, name, msg):
    label = self.builder.get_object('label_graph_%s_top' % name)
    label.set_text(msg)

  def _processEvent(self, primary, secondary):
    values = {'primary' : primary, 'secondary' : secondary}

    for name in ('primary', 'secondary'):
      # right shift and store kbytes in left-most location
      self.data[name].rotate(1)
      self.data[name][0] = values[name] / 1024

      self.total[name] = self.total[name] + values[name]

      if values[name] > 0:
        self.ticks[name] = self.ticks[name] + 1

