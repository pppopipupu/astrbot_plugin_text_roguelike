import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.models import current_user_id as cid1

try:
    from game.models import current_user_id as cid2
except ImportError:
    cid2 = None

print("cid1 id:", id(cid1))
print("cid2 id:", id(cid2))
print("Is same:", cid1 is cid2)
