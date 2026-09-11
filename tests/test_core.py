import tempfile
import unittest
from pathlib import Path

from data_analyzer.core import DataAnalyzer


class DataAnalyzerTests(unittest.TestCase):
    def test_import_csv_and_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "dados.csv"
            source.write_text("id,valor\\n1,10.5\\n2,20.5\\n", encoding="utf-8")
            analyzer = DataAnalyzer(root / "dados.db")
            analyzer.import_path(source)
            report = analyzer.analyze()
            analyzer.close()
        self.assertEqual(report["tables"]["dados"]["rows"], 2)
        self.assertEqual(report["tables"]["dados"]["columns"][1]["means"], 15.5)


if __name__ == "__main__":
    unittest.main()