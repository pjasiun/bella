#!/usr/bin/env python

import sys
from formatter import *

code = open(sys.argv[1], 'r').read()

stylist = Formatter()
code = stylist.arrange( code, False )

code = code[:-1]

print code