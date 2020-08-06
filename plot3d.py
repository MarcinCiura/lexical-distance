#!/usr/bin/python
# -*- coding: utf-8 -*-

import bisect
import math
import sys

from matplotlib import animation
from matplotlib import font_manager
from matplotlib import patches
from matplotlib import pyplot as plt
from axes3d import Axes3D

FIGSIZE = (6.4, 4.8)
NUM_FRAMES = 120
MIN_ALPHA = 0.05
MAX_ALPHA = 1.0
LABEL_SIZE = 10
TITLE_SIZE = 16
BALL_B = 0.20

COLORS = {
  'base03': '#002b36',
  'base0': '#839496',
  'base3': '#fdf6e3',
  'yellow': '#b58900',
  'orange': '#cb4b16',
  'red': '#dc322f',
  'magenta': '#d33682',
  'violet': '#6c71c4',
  'blue': '#268bd2',
  'cyan': '#2aa198',
  'green': '#859900',
  'light-yellow': '#d9bf71',
  'light-orange': '#e4a07c',
  'light-red': '#ec9489',
  'light-magenta': '#e896b2',
  'light-violet': '#b4b3d3',
  'light-blue': '#91c0da',
  'light-cyan': '#93cbbd',
  'light-green': '#c1c771',
  'dark-yellow': '#5a5a1b',
  'dark-orange': '#653b26',
  'dark-red': '#6e2e32',
  'dark-magenta': '#69305c',
  'dark-violet': '#364e7d',
  'dark-blue': '#135b84',
  'dark-cyan': '#156667',
  'dark-green': '#42621b',
}

legend_handles = []
names = []
group_colors = {}
maxima = [-1e300, -1e300, -1e300]
languages = []
lengths = []
coordinates = []


def MakeDarker(color):
  rgb = [int(x, 16) for x in [color[1:3], color[3:5], color[5:7]]]
  for i, c in enumerate(rgb):
    rgb[i] = int(c / 2)
  return '#%02x%02x%02x' % tuple(rgb)


def Zorder(xx, yy, zz, l):
  return xx * l[2] + yy * l[3] + zz * l[4]


def Distance3D(coord1, coord2):
  return math.sqrt(sum((c1 - c2)**2 for c1, c2 in zip(coord1, coord2)))


def CartesianToSpherical(xx, yy, zz):
  azim = math.degrees(math.atan2(yy, xx))
  elev = math.degrees(math.asin(zz))
  return azim, elev


def Interpolate(fraction):
  distance = fraction * lengths[-1]
  i = bisect.bisect(lengths, distance)
  factor = (distance - lengths[i - 1]) / (lengths[i] - lengths[i - 1])
  return [pc + factor * (nc - pc)
          for pc, nc in zip(coordinates[i - 1], coordinates[i])]


def TennisBallSeam(i):
  # Fernando J. López-López
  # http://aapt.scitation.org/doi/10.1119/1.18343
  # basketball b = 0.38
  # softball b = 0.30
  # baseball b = 0.28
  # tennis ball b = 0.20
  t = 2 * math.pi * i / NUM_FRAMES
  BALL_A = 1.0 - BALL_B
  xx = BALL_A * math.sin(t) + BALL_B * math.sin(3 * t)
  yy = BALL_A * math.cos(t) - BALL_B * math.cos(3 * t)
  zz = math.sqrt(4 * BALL_A * BALL_B) * math.cos(2 * t)
  return xx, yy, zz


def Plot(nframe):
  sys.stderr.write('Drawing frame %d  \r' % nframe)
  plt.clf()
  ax = fig.add_subplot(111, projection='3d')
  ax.set_axis_off()
  fraction = float(nframe) / NUM_FRAMES
  xx, yy, zz = Interpolate(fraction)
  azim, elev = CartesianToSpherical(xx, yy, zz)
  ax.view_init(elev=elev, azim=azim)
  for l in languages:
    l[5] = Zorder(xx, yy, zz, l)
  languages.sort(key=lambda l: l[5])
  for i, (name, color, x, y, z, zorder) in enumerate(languages):
    # ax.plot([0, x], [0, y], [0, z], color='gray')
    ax.text(
        x, y, z, name, color='black',
        ha='center', va='center',
        fontproperties=font, fontsize=LABEL_SIZE,
        bbox=dict(
            boxstyle='round4', fc=color, ec=MakeDarker(color),
            alpha=MIN_ALPHA + (MAX_ALPHA - MIN_ALPHA) *
            (zorder - minzorder) / (maxzorder - minzorder)))
  limit = max(maxima) / scale
  ax.set_xlim(-limit, +limit)
  ax.set_ylim(-limit, +limit)
  ax.set_zlim(-limit, +limit)
  ax.set_aspect(1)
  leg = plt.figlegend(
      legend_handles, names, 'upper right',
      fancybox=True, framealpha=0.0, prop=font)
  leg.draw_frame(False)
  plt.annotate(
      'marcinciura.wordpress.com', xy=(1, 0),
      ha='right', va='bottom', xycoords='axes fraction',
      fontproperties=font)
  plt.title(
      'Lexical Distance among\n' + title,
      fontproperties=font, fontsize=TITLE_SIZE)
  plt.tight_layout()


def main():
  global title, scale
  with open(sys.argv[1]) as f:
    lines = f.readlines()
    title = lines[0].strip().decode('utf-8')
    output = lines[1].strip()
    scale = float(lines[2].strip())
    for line in lines[3:]:
      split = line.split()
      name = split[0].replace('_', ' ').decode('utf-8')
      names.append(name)
      color = COLORS[split[1]]
      legend_handles.append(patches.Circle((0.5, 0.5), color=color))
      for group in split[2:]:
        group_colors[group] = color

  sumx = 0.0
  sumy = 0.0
  sumz = 0.0
  n = 0
  skipped = 0
  with open('positions.txt') as f:
    for line in f:
      try:
        name, x, y, z = line.split()
      except:
        print line
        raise
      name, group = name.replace('_', ' ').decode('utf-8').split('/')
      if group in group_colors:
        languages.append([
            name, group_colors[group], float(x), float(y), float(z), 0.0])
        sumx += float(x)
        sumy += float(y)
        sumz += float(z)
        n += 1
      else:
        skipped += 1
  print 'Retained %s, skipped %s languages' % (n, skipped)

  sumx /= n
  sumy /= n
  sumz /= n
  for l in languages:
    l[2] -= sumx
    l[3] -= sumy
    l[4] -= sumz
    for i in xrange(3):
      maxima[i] = max(maxima[i], abs(l[i + 2]))

  global minzorder, maxzorder
  minzorder = +1e300
  maxzorder = -1e300
  length = 0.0
  for i in xrange(NUM_FRAMES + 1):
    xx, yy, zz = TennisBallSeam(i)
    if i > 0:
      length += Distance3D(coordinates[-1], (xx, yy, zz))
    lengths.append(length)
    coordinates.append((xx, yy, zz))
    for l in languages:
      zorder = Zorder(xx, yy, zz, l)
      minzorder = min(minzorder, zorder)
      maxzorder = max(maxzorder, zorder)

  global font, fig
  font = font_manager.FontProperties(fname='Delicious-Roman.otf')
  fig = plt.figure(figsize=FIGSIZE)
  # init_func has to be passed as a workaround for a bug in Matplotlib 1.5:
  # https://github.com/matplotlib/matplotlib/issues/5399
  # The two void calls to Plot() are needed to stablilize
  # the position of the title in subsequent calls.
  anim = animation.FuncAnimation(
      fig, Plot, frames=NUM_FRAMES, blit=False,
      init_func=lambda: (Plot(0), Plot(0)))
  anim.save(output, writer='imagemagick', fps=12.5)


if __name__ == '__main__':
  main()
