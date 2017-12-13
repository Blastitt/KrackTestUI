#!/bin/python

import time

with open('testOutput.txt', 'r') as f:
	for line in f:
		print line
		time.sleep(.300)