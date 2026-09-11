from __future__ import annotations

import argparse
from pathlib import Path

from .core import DataAnalyzer


def collect_files(inputs: list[str]) -> list[Path]:
    files: list[Path] = []
    for item in inputs:
        path = Path(item)
        if path.is_dir():
            files.extend(
                sorted(
                    candidate
                    for candidate in path.rglob("*")
                    if candidate.suffix.lower() in {".csv", ".txt", ".xml", ".sql"}
                )
            )
        elif path.is_file():
            files.append(path)
        else:
            print(f"[AVISO] Caminho não encontrado: {path}")
    return files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importa arquivos em SQLite e gera análise automática."
    )
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="Arquivos ou diretórios de entrada",
    )
    parser.add_argument(
        "--database",
        default="dados.db",
        help="Arquivo SQLite de destino",
    )
    parser.add_argument(
        "--report-dir",
        default="relatorios",
        help="Diretório dos relatórios",
    )

    args = parser.parse_args()
    files = collect_files(args.input)

    if not files:
        parser.error("Nenhum arquivo suportado encontrado.")

    analyzer = DataAnalyzer(args.database)

    try:
        for path in files:
            try:
                result = analyzer.import_path(path)
                print(
                    f"[OK] {result.source}: {result.status} "
                    f"({result.rows} linhas, {result.table})"
                )
            except Exception as error:
                print(f"[ERRO] {path}: {error}")

        json_path, csv_path = analyzer.write_reports(args.report_dir)
        print(f"Relatórios: {json_path} | {csv_path}")

    finally:
        analyzer.close()


if __name__ == "__main__":
    main()