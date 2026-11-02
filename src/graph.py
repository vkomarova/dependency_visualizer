from collections import deque


def is_filtered(name, filter_text):
    return filter_text is not None and filter_text in name


def build_graph(start, get_dependencies, filter_text):
    graph = {}
    queue = deque([start])
    while queue:
        package = queue.popleft()
        if package in graph:
            continue
        dependencies = []
        for name in get_dependencies(package):
            if not is_filtered(name, filter_text):
                dependencies.append(name)
        graph[package] = dependencies
        queue.extend(dependencies)
    return graph
