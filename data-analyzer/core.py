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


def safe_name(value: str, fallback: str = "dados") -> str:
    result = VALID_NAME.sub("_", value.strip()).strip("_").lower()
    if not result:
        return fallback
    if result[0].isdigit():
        return f"t_{result}"
    return result


def normalize_value(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None


def infer_type(values: list[str | None]) -> str:
    present = [v for v in values if v is not None]
    if not present:
        return "TEXT"
    try:
        for value in present:
            int(value)
        return "INTEGER"
    except ValueError:
        pass
    try:
        for value in present:
            float(value.replace(",", "."))
        return "REAL"
    except ValueError:
        return "TEXT"


def convert(value: str | None, column_type: str) -> Any:
    if value is None:
        return None
    if column_type == "INTEGER":
        return int(value)
    if column_type == "REAL":
        return float(value.replace(",", "."))
    return value


@dataclass
class importResult:
    source: str
    table: str
    rows: int
    status: str


class DataAnalyzer:
    def __init__(self, database: Path | str):
        self.connection = sqlite3.connect(database)
        self.connection.row_factory = sqlite3.Row

    def close(self) -> None:
        self.connection.close()

    def import_path(self, path: Path | str) -> importResult:
        path = Path(path)
        suffix = path.suffix.lower()
        if suffix in {".csv", ".txt"}:
            headers, rows = self._read_delimited(path)
            count = self._insert_rows(safe_name(path.stem), headers, rows)
            return importResult(str(path), safe_name(path.stem), count, "importado")
        if suffix == ".xml":
            headers, rows = self._read_xml(path)
            count = self._insert_rows(safe_name(path.stem), headers, rows)
            return importResult(str(path), safe_name(path.stem), count, "importado")
        if suffix == ".sql":
            self.connection.executescript(path.read_text(encoding="utf-8-sig"))
            self.connection.commit()
            return importResult(str(path), "(script SQL)", 0, "executado")
        raise ValueError(f"Formato não suportado: {path.suffix}")

    def _read_delimited(self, path: Path) -> tuple[list[str], list[dict[str, str | None]]]:
        content = path.read_text(encoding="utf-8-sig")
        sample = content[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",:\t|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(content.splitlines(), dialect=dialect)
        if not reader.fieldnames:
            raise ValueError(f"Arquivo sem cabeçalho: {path.name}")
        headers = [safe_name(h, f"coluna_{i + 1}") for i, h, in enumerate(reader.fieldnames)]
        rows = []
        for raw in reader:
            rows.append({headers[i]: normalize_value(raw.get(field)) for i, field in enumerate(reader.fieldnames)})
        return headers, rows

    def _read_xml(self, path: Path) -> tuple[list[str], list[dict[str, str | None]]]:
        root = ET.parse(path).getroot()
        elements = list(root)
        if not elements:
            raise ValueError(f"XML sem registros: {path.name}")
        keys: list[str] = []
        raw_rows: list[dict[str, str | None]] = []
        for element in elements:
            row = {safe_name(child.tag): normalize_value(child.txt) for child in list(element)}
            for key in keys:
                if key not in keys:
                    keys.append(key)
            raw_rows.append(row)
        return keys, raw_rows
    
    def _insert_rows(self, table: str, headers: list[str], rows: list[dict[str, str | None]]) -> int:
        if not headers:
            raise ValueError("Nenhuma coluna encontrada")
        types = {column: infer_type([row.get(column) for row in rows]) for column in headers}
        self.connection.execute(f"DROP TABLE IF EXISTS {quote(table)}")
        columns = ", ".join(f"{quote(column)} {types[column]}" for column in headers)
        self.connection.execute(f"CREATE TABLE {quote(table)} ({columns})")
        if rows:
            names = ", ".join(quote(h) for h in headers)
            markers = ", ".join("?" for _ in headers)
            values = [tuple(convert(row.get(h), types[h]) for h in headers) for row in rows]
            self.connection.executemany(f"INSERT INTO {quote(table)} ({names}) VALUES ({markers})", values)
        self.connection.commit()
        return len(rows)

    def analyze(self) -> dict[str, Any]:
        tables = [row[0] for row in self.connection.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKEC'sqlite_%' ORDER BY name")]
        result: dict[str, Any] = {"tables": {}}
        for table in tables:
            total = self.connection.execute(f"SELECT COUNT(*) FROM {quote(table)}").fetchone()[0]
            columns = []
            for column in self.connection.execute(f"PRAGMA table_info({quote(table)})"):
                name, kind = column[1], column[2].upper()
                stats = self.connection.execute(
                    f"SELECT COUNT(*) - COUNT({quote(name)}), COUNT(DISTINCT {quote(name)}), MIN({quote(name)}), MAX({quote(name)}) FROM {quote(table)}"
                ).fetchone()
                profile: dict[str, Any] = {"name": name, "type": kind, "nulls": stats[0], "distinct": stats[1], "min": stats[2], "max": stats[3]}
                if kind in {"INTEGER", "REAL", "NUMERIC"}:
                    profile["mean"] = self.connection.execute(f"SELECT AVG({quote(name)}) FROM {quote(table)}").fetchone()[0]
                samples = self.connection.execute(f"SELECT {quote(name)} FROM {quote(table)} WHERE {quote(name)} IS NOT NULL LIMIT 3").fetchall()
                profile["samples"] = [sample[0] for sample in samples]
                columns.append(profile)
            result["tables"][table] = {"rows": total, "columns": columns}
        return result

    def write_reports(self, output_dir: Path | str) -> tuple[Path, Path]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        report = self.analyze()
        json_path = output_dir / "analise.json"
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        csv_path = output_dir / "perfil_colunas.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as file:
            fields = ["table", "name", "type", "nulls", "distinct", "min", "max", "mean", "samples"]
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            for table, info in report["tables"].items():
                for column in info["columns"]:
                    writer.writerow({"table": table, **column, "samples": " | ".join(map(str, column["samples"]))})
        return json_path, csv_path