from __future__ import annotations

import csv
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VALID_NAME = re.compile(r"[^a-zA-Z0-9_]")


def quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'