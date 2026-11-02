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

POM_WITH_PROPERTIES = """<project>
  <groupId>org.example</groupId>
  <version>2.5</version>
  <properties>
    <hamcrestVersion>1.3</hamcrestVersion>
  </properties>
  <dependencies>
    <dependency>
      <groupId>org.hamcrest</groupId>
      <artifactId>hamcrest-core</artifactId>
      <version>${hamcrestVersion}</version>
    </dependency>
    <dependency>
      <groupId>${project.groupId}</groupId>
      <artifactId>part</artifactId>
      <version>${project.version}</version>
    </dependency>
    <dependency>
      <groupId>org.unknown</groupId>
      <artifactId>lib</artifactId>
      <version>${unknown.version}</version>
    </dependency>
  </dependencies>
</project>
"""

POM_WITH_SCOPES = """<project>
  <dependencies>
    <dependency>
      <groupId>a</groupId>
      <artifactId>compile</artifactId>
      <version>1</version>
    </dependency>
    <dependency>
      <groupId>a</groupId>
      <artifactId>runtime</artifactId>
      <version>1</version>
      <scope>runtime</scope>
    </dependency>
    <dependency>
      <groupId>a</groupId>
      <artifactId>test</artifactId>
      <version>1</version>
      <scope>test</scope>
    </dependency>
    <dependency>
      <groupId>a</groupId>
      <artifactId>provided</artifactId>
      <version>1</version>
      <scope>provided</scope>
    </dependency>
    <dependency>
      <groupId>a</groupId>
      <artifactId>optional</artifactId>
      <version>1</version>
      <optional>true</optional>
    </dependency>
  </dependencies>
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

    def test_properties(self):
        """Переменные ${...} заменяются значениями из файла POM."""
        result = maven.parse_dependencies(POM_WITH_PROPERTIES)
        self.assertEqual(result, ["org.hamcrest:hamcrest-core:1.3",
                                  "org.example:part:2.5",
                                  "org.unknown:lib:${unknown.version}"])

    def test_scopes(self):
        """Зависимости test, provided и optional не учитываются."""
        result = maven.parse_dependencies(POM_WITH_SCOPES)
        self.assertEqual(result, ["a:compile:1", "a:runtime:1"])


class TestCanDownload(unittest.TestCase):

    def test_known_version(self):
        """Обычная версия известна."""
        self.assertTrue(maven.can_download("junit:junit:4.13.2"))

    def test_unknown_version(self):
        """Без версии, с переменной или с диапазоном POM не скачать."""
        self.assertFalse(maven.can_download("junit:junit"))
        self.assertFalse(maven.can_download("a:b:${v}"))
        self.assertFalse(maven.can_download("a:b:[1.0,2.0)"))


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

    def test_unknown_version_not_downloaded(self):
        """Пакет с неизвестной версией не скачивается."""
        with mock.patch("maven.download_text") as download:
            result = maven.get_direct_dependencies("https://repo.org",
                                                   "x:y")
        download.assert_not_called()
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
