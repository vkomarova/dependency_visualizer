# dependency_visualizer — визуализация графа зависимостей

## Общее описание

Инструмент визуализации графа зависимостей для менеджера пакетов.

- **Этап 1.** Параметры задаются опциями командной строки и
  проверяются на ошибки.
- **Этап 2.** Сбор данных: программа скачивает из репозитория Maven
  файл POM заданного пакета и выводит на экран все его прямые
  зависимости.

## Структура проекта

```
depviz/
├── src/main.py           параметры командной строки и вывод результата
├── src/maven.py          получение прямых зависимостей из репозитория Maven
├── tests/test_main.py    тесты параметров и вывода
├── tests/test_maven.py   тесты получения зависимостей
├── run.sh                запуск в Linux / macOS
├── run.bat               запуск в Windows
├── Makefile              команды запуска и тестов
├── README.md
└── .gitignore
```

## Функции и настройки

### Параметры командной строки

| Опция       | Описание                                         | Обязательна |
|-------------|--------------------------------------------------|-------------|
| `--package` | Имя пакета в виде `groupId:artifactId:version`   | да          |
| `--repo`    | URL репозитория или путь к файлу тестового репозитория | да    |
| `--mode`    | Режим работы с репозиторием: `real` или `test`   | нет (`real`) |
| `--output`  | Имя файла с изображением графа (`.svg`)          | да          |
| `--filter`  | Подстрока для фильтрации пакетов                 | нет         |

Параметры `--output` и `--filter` пока только проверяются,
а использоваться будут на следующих этапах.

### Как программа получает зависимости

1. Из имени пакета и URL репозитория составляется адрес файла POM.
   Точки в `groupId` заменяются на `/`. Например, для пакета
   `junit:junit:4.13.2` и репозитория `https://repo1.maven.org/maven2`
   получается адрес
   `https://repo1.maven.org/maven2/junit/junit/4.13.2/junit-4.13.2.pom`.
2. Файл POM скачивается модулем `urllib` из стандартной библиотеки.
3. Файл читается как XML модулем `xml.etree` из стандартной библиотеки.
4. Прямые зависимости — это теги `project/dependencies/dependency`.
   Раздел `dependencyManagement` не учитывается: там только
   рекомендуемые версии, а не зависимости пакета.
5. Каждая зависимость выводится как `groupId:artifactId:version`.
   Если версия в POM не указана, выводится `groupId:artifactId`.

### Обработка ошибок

При ошибке программа выводит сообщение `Ошибка: ...` и завершается
с кодом 1.

| Параметр    | Когда выводится ошибка |
|-------------|------------------------|
| `--package` | имя не задано, пустое или содержит пробелы; в режиме `real` записано не как `groupId:artifactId:version` |
| `--mode`    | значение не `real` и не `test`; режим `test` пока не поддерживается |
| `--repo`    | не задан; в режиме `real` не начинается с `http://` или `https://`; в режиме `test` файл не существует |
| `--output`  | имя не задано, пустое или не оканчивается на `.svg` |
| `--filter`  | задан, но состоит только из пробелов |
| загрузка    | файл POM не удалось скачать (нет сети, пакет не найден) |
| чтение      | файл POM содержит ошибки XML |

### Функции в `src/main.py`

| Функция | Описание |
|---------|----------|
| `create_parser()` | создаёт парсер опций командной строки |
| `check_maven_name(package)` | проверяет формат `groupId:artifactId:version` |
| `check_package(package, mode)` | проверяет имя пакета |
| `check_mode(mode)` | проверяет режим работы |
| `check_repo(repo, mode)` | проверяет URL или путь к тестовому файлу |
| `check_output(output)` | проверяет имя файла изображения |
| `check_filter(text)` | проверяет подстроку фильтра |
| `check_params(params)` | вызывает все проверки по очереди |
| `get_dependencies(params)` | получает прямые зависимости пакета |
| `print_dependencies(package, dependencies)` | выводит зависимости на экран |
| `main(args)` | точка входа программы |

### Функции в `src/maven.py`

| Функция | Описание |
|---------|----------|
| `make_pom_url(repo, package)` | составляет URL файла POM |
| `download_text(url)` | скачивает файл по URL |
| `remove_namespaces(root)` | убирает пространство имён из тегов XML |
| `make_dependency_name(dependency)` | составляет имя зависимости из тега |
| `parse_dependencies(pom_text)` | находит прямые зависимости в POM |
| `get_direct_dependencies(repo, package)` | скачивает POM и возвращает зависимости |

## Сборка и запуск тестов

Запуск программы:

```
./run.sh --package <groupId:artifactId:version> --repo <url> --output <файл.svg>
run.bat --package <groupId:artifactId:version> --repo <url> --output <файл.svg>
make run ARGS="--package <groupId:artifactId:version> --repo <url> --output <файл.svg>"
```

Запуск тестов:

```
make test
```

или без make:

```
python3 -m unittest discover -s tests -v
```

## Примеры использования

Прямые зависимости пакета JUnit:

```
$ ./run.sh --package junit:junit:4.13.2 --repo https://repo1.maven.org/maven2 --output graph.svg
Прямые зависимости пакета junit:junit:4.13.2:
org.hamcrest:hamcrest-core:1.3
```

Примеры ошибок:

```
$ ./run.sh --package junit:junit --repo https://repo1.maven.org/maven2 --output graph.svg
Ошибка: имя пакета должно иметь вид groupId:artifactId:version

$ ./run.sh --package junit:junit:0.0 --repo https://repo1.maven.org/maven2 --output graph.svg
Ошибка: не удалось загрузить https://repo1.maven.org/maven2/junit/junit/0.0/junit-0.0.pom (HTTP Error 404: Not Found)

$ ./run.sh --package a:b:1 --repo ftp://example.org --output graph.svg
Ошибка: URL репозитория должен начинаться с http:// или https://

$ ./run.sh --package A --repo README.md --mode test --output graph.svg
Ошибка: режим test пока не поддерживается

$ ./run.sh --package a:b:1 --repo https://example.org --mode abc --output graph.svg
Ошибка: режим (--mode) должен быть real или test

$ ./run.sh --package a:b:1 --repo https://example.org --output graph.png
Ошибка: файл изображения должен иметь расширение .svg

$ ./run.sh --package a:b:1 --repo https://example.org --output graph.svg --filter " "
Ошибка: подстрока фильтра (--filter) не может быть пустой
```
