import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import graph

SIMPLE_REPO = {
    "A": ["B", "C"],
    "B": ["D"],
    "C": ["D", "E"],
    "D": [],
    "E": ["F"],
    "F": [],
}

CYCLE_REPO = {
    "A": ["B"],
    "B": ["C"],
    "C": ["A", "D"],
    "D": ["D"],
}


def make_loader(repo):

    def get_dependencies(name):
        """Вернуть зависимости пакета из словаря."""
        return repo.get(name, [])
    return get_dependencies


class TestBuildGraph(unittest.TestCase):

    def test_transitive(self):
        """В граф попадают и прямые, и транзитивные зависимости."""
        result = graph.build_graph("A", make_loader(SIMPLE_REPO), None)
        self.assertEqual(result, SIMPLE_REPO)

    def test_bfs_order(self):
        """Пакеты обходятся в ширину: сначала ближние, потом дальние."""
        result = graph.build_graph("A", make_loader(SIMPLE_REPO), None)
        self.assertEqual(list(result), ["A", "B", "C", "D", "E", "F"])

    def test_part_of_graph(self):
        """Граф строится только от заданного пакета."""
        result = graph.build_graph("E", make_loader(SIMPLE_REPO), None)
        self.assertEqual(result, {"E": ["F"], "F": []})

    def test_cycle(self):
        """Циклические зависимости не приводят к зацикливанию."""
        result = graph.build_graph("A", make_loader(CYCLE_REPO), None)
        self.assertEqual(result, CYCLE_REPO)

    def test_filter(self):
        """Пакеты с подстрокой фильтра не учитываются."""
        result = graph.build_graph("A", make_loader(SIMPLE_REPO), "E")
        expected = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        self.assertEqual(result, expected)

    def test_filter_breaks_cycle(self):
        """Фильтр может убрать пакет из цикла."""
        result = graph.build_graph("A", make_loader(CYCLE_REPO), "C")
        self.assertEqual(result, {"A": ["B"], "B": []})

    def test_is_filtered(self):
        """Проверка подстроки фильтра в имени пакета."""
        self.assertTrue(graph.is_filtered("org.junit:junit:4.13", "junit"))
        self.assertFalse(graph.is_filtered("org.slf4j:slf4j-api", "junit"))
        self.assertFalse(graph.is_filtered("A", None))


if __name__ == "__main__":
    unittest.main()