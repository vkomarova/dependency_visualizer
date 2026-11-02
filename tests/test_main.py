import io
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import main

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SIMPLE_FILE = os.path.join(DATA_DIR, "simple.txt")
CYCLE_FILE = os.path.join(DATA_DIR, "cycle.txt")
BAD_FILE = os.path.join(DATA_DIR, "bad.txt")

REAL_ARGS = [
    "--package", "x:app:1.0",
    "--repo", "https://repo.org",
    "--output", "graph.svg",
]

POM_FILES = {
    "https://repo.org/x/app/1.0/app-1.0.pom": """<project>
  <dependencies>
    <dependency>
      <groupId>x</groupId><artifactId>lib</artifactId><version>2.0</version>
    </dependency>
  </dependencies>
</project>""",
    "https://repo.org/x/lib/2.0/lib-2.0.pom": "<project/>",
}


def run_main(args):
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main.main(args)
    return code, out.getvalue(), err.getvalue()


def make_test_args(path, package, *extra):
    args = ["--package", package, "--repo", path, "--mode", "test",
            "--output", "graph.svg"]
    return args + list(extra)


class TestTestMode(unittest.TestCase):

    def test_simple_graph(self):
        """Выводится весь граф с транзитивными зависимостями."""
        code, out, _ = run_main(make_test_args(SIMPLE_FILE, "A"))
        self.assertEqual(code, 0)
        self.assertEqual(out, "Граф зависимостей пакета A:\n"
                              "A -> B, C\n"
                              "B -> D\n"
                              "C -> D, E\n"
                              "D -> нет зависимостей\n"
                              "E -> F\n"
                              "F -> нет зависимостей\n")

    def test_cycle(self):
        """Граф с циклами выводится без зацикливания."""
        code, out, _ = run_main(make_test_args(CYCLE_FILE, "A"))
        self.assertEqual(code, 0)
        self.assertIn("C -> A, D", out)
        self.assertIn("D -> D", out)

    def test_filter(self):
        """Пакеты с подстрокой фильтра не попадают в граф."""
        args = make_test_args(SIMPLE_FILE, "A", "--filter", "E")
        code, out, _ = run_main(args)
        self.assertEqual(code, 0)
        self.assertIn("C -> D\n", out)
        self.assertNotIn("E", out.replace("Граф", ""))

    def test_package_not_in_file(self):
        """Пакета нет в файле тестового репозитория."""
        code, _, err = run_main(make_test_args(SIMPLE_FILE, "Z"))
        self.assertEqual(code, 1)
        self.assertIn("не найден в тестовом репозитории", err)

    def test_bad_file(self):
        """Ошибка в файле тестового репозитория."""
        code, _, err = run_main(make_test_args(BAD_FILE, "A"))
        self.assertEqual(code, 1)
        self.assertIn("строка 2", err)

    def test_bad_test_name(self):
        """В режиме test имя пакета - большие латинские буквы."""
        code, _, err = run_main(make_test_args(SIMPLE_FILE, "a"))
        self.assertEqual(code, 1)
        self.assertIn("больших латинских букв", err)


class TestRealMode(unittest.TestCase):

    def test_real_graph(self):
        """Граф строится по файлам POM из репозитория."""
        with mock.patch("maven.download_text", side_effect=POM_FILES.get):
            code, out, _ = run_main(REAL_ARGS)
        self.assertEqual(code, 0)
        self.assertIn("x:app:1.0 -> x:lib:2.0", out)
        self.assertIn("x:lib:2.0 -> нет зависимостей", out)

    def test_download_error(self):
        """Ошибка загрузки выводится как ошибка программы."""
        error = ValueError("не удалось загрузить файл")
        with mock.patch("maven.download_text", side_effect=error):
            code, out, err = run_main(REAL_ARGS)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("не удалось загрузить", err)


class TestBadParams(unittest.TestCase):

    def check_error(self, args, text):
        code, out, err = run_main(args)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn(text, err)

    def test_no_package(self):
        """Не задано имя пакета."""
        args = ["--repo", "https://x.org", "--output", "g.svg"]
        self.check_error(args, "не задано имя пакета")

    def test_package_with_space(self):
        """Имя пакета содержит пробел."""
        args = ["--package", "a b", "--repo", "https://x.org",
                "--output", "g.svg"]
        self.check_error(args, "пробелы")

    def test_package_without_version(self):
        """Имя пакета без версии."""
        args = ["--package", "junit:junit", "--repo", "https://x.org",
                "--output", "g.svg"]
        self.check_error(args, "groupId:artifactId:version")

    def test_no_repo(self):
        """Не задан репозиторий."""
        args = ["--package", "a:b:1", "--output", "g.svg"]
        self.check_error(args, "не задан репозиторий")

    def test_bad_url(self):
        """URL не начинается с http:// или https://."""
        args = ["--package", "a:b:1", "--repo", "ftp://x.org",
                "--output", "g.svg"]
        self.check_error(args, "URL репозитория")

    def test_missing_test_file(self):
        """Файл тестового репозитория не существует."""
        self.check_error(make_test_args("no_such_file.txt", "A"), "не найден")

    def test_bad_mode(self):
        """Неизвестный режим работы."""
        args = ["--package", "a:b:1", "--repo", "https://x.org",
                "--mode", "abc", "--output", "g.svg"]
        self.check_error(args, "режим")

    def test_no_output(self):
        """Не задано имя файла изображения."""
        args = ["--package", "a:b:1", "--repo", "https://x.org"]
        self.check_error(args, "не задано имя файла")

    def test_bad_output_extension(self):
        """Имя файла изображения без расширения .svg."""
        args = ["--package", "a:b:1", "--repo", "https://x.org",
                "--output", "g.png"]
        self.check_error(args, ".svg")

    def test_empty_filter(self):
        """Подстрока фильтра пустая."""
        args = ["--package", "a:b:1", "--repo", "https://x.org",
                "--output", "g.svg", "--filter", " "]
        self.check_error(args, "фильтр")


if __name__ == "__main__":
    unittest.main()