#!/usr/bin/env python

import sys
from .formatter import *

if hasattr(sys, 'argv'):
	code = open(sys.argv[1], 'r').read()

	stylist = Formatter()
	code = stylist.arrange( code, False )

	code = code[:-1]

	print(code)