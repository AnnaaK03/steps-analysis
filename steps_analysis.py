"""
Step analysis from Apple Health

What the program does:
  1. Reads the export.xml file (Apple Health export)
  2. Takes steps recorded by the iPhone only
  3. Calculates steps per day and prints statistics
  4. Draws five charts and saves them to the results/ folder
"""

from matplotlib.patches import FancyBboxPatch
import matplotlib.pyplot as plt
import os
import xml.etree.ElementTree as ET

import pandas as pd
import matplotlib
