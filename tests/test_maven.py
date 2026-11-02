import os
import sys
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import maven

POM_WITH_NAMESPACE = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <groupId>org.example</groupId>
  <artifactId>app</artifactId>
  <version>1.0</version>
  <dependencyManagement>
    <dependencies>
      <dependency>
        <groupId>org.managed</groupId>
        <artifactId>managed</artifactId>
        <version>9.9</version>
      </dependency>
    </dependencies>
  </dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>org.hamcrest</groupId>
      <artifactId>hamcrest-core</artifactId>
      <version>1.3</version>
    </dependency>
    <dependency>
      <groupId>org.slf4j</groupId>
      <artifactId>slf4j-api</artifactId>
    </dependency>
  </dependencies>
</project>
"""

POM_WITHOUT_NAMESPACE = """<project>
  <dependencies>
    <dependency>
      <groupId>a.b</groupId>
      <artifactId>c</artifactId>
      <version>2.0</version>
    </dependency>
  </dependencies>
</project>
"""

POM_WITHOUT_DEPENDENCIES = """<project>
  <groupId>a.b</groupId>
  <artifactId>c</artifactId>
</project>
"""


class TestMakePomUrl(unittest.TestCase):

    def test_url(self):
        """Точки в groupId заменяются на слэши."""
        url = maven.make_pom_url("https://repo1.maven.org/maven2",
                                 "org.apache.commons:commons-text:1.12.0")
        self.assertEqual(
            url,
            "https://repo1.maven.org/maven2/org/apache/commons/"
            "commons-text/1.12.0/commons-text-1.12.0.pom")

    def test_url_with_slash(self):
        """Лишний слэш в конце URL репозитория убирается."""
        url = maven.make_pom_url("https://repo.org/", "junit:junit:4.13.2")
        self.assertEqual(
            url, "https://repo.org/junit/junit/4.13.2/junit-4.13.2.pom")


class TestParseDependencies(unittest.TestCase):

    def test_with_namespace(self):
        """Берутся только прямые зависимости, без dependencyManagement."""
        result = maven.parse_dependencies(POM_WITH_NAMESPACE)
        self.assertEqual(result, ["org.hamcrest:hamcrest-core:1.3",
                                  "org.slf4j:slf4j-api"])

    def test_without_namespace(self):
        """Файл POM без пространства имён тоже читается."""
        result = maven.parse_dependencies(POM_WITHOUT_NAMESPACE)
        self.assertEqual(result, ["a.b:c:2.0"])

    def test_no_dependencies(self):
        """Если зависимостей нет, возвращается пустой список."""
        result = maven.parse_dependencies(POM_WITHOUT_DEPENDENCIES)
        self.assertEqual(result, [])

    def test_bad_xml(self):
        """Неправильный XML вызывает ошибку."""
        with self.assertRaises(ValueError):
            maven.parse_dependencies("<project><dependencies>")


class TestDownload(unittest.TestCase):

    def test_download_error(self):
        """Ошибка сети превращается в понятное сообщение."""
        error = urllib.error.URLError("нет сети")
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(ValueError) as context:
                maven.download_text("https://repo.org/a.pom")
        self.assertIn("не удалось загрузить", str(context.exception))

    def test_get_direct_dependencies(self):
        """Зависимости берутся из скачанного файла POM."""
        with mock.patch("maven.download_text",
                        return_value=POM_WITHOUT_NAMESPACE) as download:
            result = maven.get_direct_dependencies("https://repo.org",
                                                   "x:y:1.0")
        download.assert_called_once_with("https://repo.org/x/y/1.0/y-1.0.pom")
        self.assertEqual(result, ["a.b:c:2.0"])


if __name__ == "__main__":
    unittest.main()
