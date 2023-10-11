import json
import os
from datetime import *
from pathlib import Path

date = datetime.now()
day, month, year = date.day, date.month, date.year

path = Path(f"app/api/json/todays_matches/{day}_{month}_{year}.json")
with open(path, 'w') as outfile:
    json.dump(response.json(), outfile)