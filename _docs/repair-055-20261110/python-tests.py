"""Run source unittests with the checkout import/cwd contract, inside its Job."""
import os
from pathlib import Path
import runpy
import sys

root = Path(__file__).resolve().parents[2]
os.chdir(root)
sys.path.insert(0, str(root))
sys.argv = ['unittest', *sys.argv[1:]]
runpy.run_module('unittest', run_name='__main__')
