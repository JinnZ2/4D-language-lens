"""Put the repository root on sys.path for pytest runs.

The modules live at the top level rather than in a package directory, so
`import revised_4dlens_v2` from tests/ needs the root on the path. The
stdlib runner (`python3 -m unittest discover -s tests`) gets this for free;
pytest does not.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
