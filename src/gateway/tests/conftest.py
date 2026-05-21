import sys
from pathlib import Path

# Allow bare `from adapters.cnc.*` imports in gateway tests
sys.path.insert(0, str(Path(__file__).parent))
