# depviz — визуализация графа зависимостей

## Общее описание

Учебный инструмент визуализации графа зависимостей для менеджера пакетов
(вариант №12). Программа написана на Python и не использует сторонних
библиотек.

Сейчас выполнен **этап 1** — минимальный прототип с конфигурацией.
Программа принимает параметры из командной строки, проверяет их и
выводит на экран в формате ключ-значение. При ошибке в параметре
программа выводит сообщение `Ошибка: ...` и завершается с кодом 1.

## Структура проекта

```
depviz/
├── src/main.py         исходный код программы
├── tests/test_main.py  тесты
├── run.sh              запуск в Linux / macOS
├── run.bat             запуск в Windows
├── Makefile            команды запуска и тестов
├── README.md
└── .gitignore
```

## Функции и настройки

### Параметры командной строки

| Опция       | Описание                                         | Обязательна |
|-------------|--------------------------------------------------|-------------|
| `--package` | Имя анализируемого пакета                        | да          |
| `--repo`    | URL репозитория или путь к файлу тестового репозитория | да    |
| `--mode`    | Режим работы с репозиторием: `real` или `test`   | нет (`real`) |
| `--output`  | Имя файла с изображением графа (`.svg`)          | да          |
| `--filter`  | Подстрока для фильтрации пакетов                 | нет         |

### Проверка параметров (обработка ошибок)

| Параметр    | Когда выводится ошибка |
|-------------|------------------------|
| `--package` | имя не задано, пустое или содержит пробелы |
| `--mode`    | значение не `real` и не `test` |
| `--repo`    | не задан; в режиме `real` не начинается с `http://` или `https://`; в режиме `test` файл не существует |
| `--output`  | имя не задано, пустое или не оканчивается на `.svg` |
| `--filter`  | задан, но состоит только из пробелов |

### Функции в `src/main.py`

| Функция | Описание |
|---------|----------|
| `create_parser()` | создаёт парсер опций командной строки |
| `check_package(package)` | проверяет имя пакета |
| `check_mode(mode)` | проверяет режим работы |
| `check_repo(repo, mode)` | проверяет URL или путь к тестовому файлу |
| `check_output(output)` | проверяет имя файла изображения |
| `check_filter(text)` | проверяет подстроку фильтра |
| `check_params(params)` | вызывает все проверки по очереди |
| `print_params(params)` | выводит параметры в формате ключ-значение |
| `main(args)` | точка входа: разбор, проверка и вывод параметров |

## Сборка и запуск тестов

Сборка не нужна: нужен только Python 3.8 или новее.

Запуск программы:

```
./run.sh --package <имя> --repo <url> --output <файл.svg>
run.bat --package <имя> --repo <url> --output <файл.svg>
make run ARGS="--package <имя> --repo <url> --output <файл.svg>"
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

Обычный режим:

```
$ ./run.sh --package org.junit:junit --repo https://repo1.maven.org/maven2 --output graph.svg --filter test
package = org.junit:junit
repo = https://repo1.maven.org/maven2
mode = real
output = graph.svg
filter = test
```

Тестовый режим (файл должен существовать):

```
$ ./run.sh --package A --repo README.md --mode test --output graph.svg
package = A
repo = README.md
mode = test
output = graph.svg
filter = None
```

Примеры ошибок:

```
$ ./run.sh --repo https://repo1.maven.org/maven2 --output graph.svg
Ошибка: не задано имя пакета (--package)

$ ./run.sh --package A --repo ftp://example.org --output graph.svg
Ошибка: URL репозитория должен начинаться с http:// или https://

$ ./run.sh --package A --repo nofile.txt --mode test --output graph.svg
Ошибка: файл тестового репозитория не найден: nofile.txt

$ ./run.sh --package A --repo https://example.org --mode abc --output graph.svg
Ошибка: режим (--mode) должен быть real или test

$ ./run.sh --package A --repo https://example.org --output graph.png
Ошибка: файл изображения должен иметь расширение .svg

$ ./run.sh --package A --repo https://example.org --output graph.svg --filter " "
Ошибка: подстрока фильтра (--filter) не может быть пустой
```
