#!/usr/bin/env/python

import sys
import re

names = []
data = []
ids = ""

for line in sys.stdin:
  s = line.strip()
  if re.match('^pg_[0-9]{4}\.pdf$', s):
    if len(names) % 4 == 0:
      # UCAS forms come in slugs of 4 pages.
      # check if previous header looks like the start of a UCAS form
      ds = ' '.join(data)
      m = re.search(r"(?P<idn>[0-9]{10}\.)", ds)
      if m:
        # found what looks like a UCAS id.
        # print previous collate command
        if len(names) > 1:
          sys.stdout.write('pdftk {0} cat output {1}pdf\n'.format(' '.join(names), ids))
        # start new collate command
        ids = m.group('idn')
        names = []
    names.append(s)
    data = []
  else:
    data.append(s)

sys.stdout.write('pdftk {0} cat output {1}pdf\n'.format(' '.join(names), ids))

