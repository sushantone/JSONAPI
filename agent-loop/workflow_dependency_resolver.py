from collections import defaultdict, deque


def collect_dependencies(nodes, changed_nodes):
    """
    Recursively collect all downstream dependencies for the given changed nodes.

    Args:
        nodes (dict): Workflow graph loaded from workflow_dependencies.json
        changed_nodes (list[str]): List of nodes that were directly changed

    Returns:
        set[str]: All affected nodes (including changed ones and their dependents)
    """
    affected = set(changed_nodes)

    def dfs(node):
        for child in nodes[node]["outputs"]:
            if child not in affected:
                affected.add(child)
                dfs(child)

    for n in changed_nodes:
        dfs(n)

    return affected


def get_execution_order(nodes, changed_nodes):
    """
    Determine the valid execution order (topological sort)
    for all affected workflows, based on dependency relationships.

    Args:
        nodes: defined dependencies
        changed_nodes (list[str]): Changed nodes to start traversal from

    Returns:
        list[str]: Ordered list of nodes for execution
    """

    # Step 1: Get all affected nodes (changed + downstream)
    affected = collect_dependencies(nodes, changed_nodes)

    # Step 2: Build a subgraph with only the affected workflows
    subgraph = {n: nodes[n] for n in affected}

    # Step 3: Calculate indegree (number of unmet dependencies for each node)
    indegree = defaultdict(int)
    for node, info in subgraph.items():
        for dep in info["depends_on"]:
            if dep in subgraph:
                indegree[node] += 1

    # Step 4: Start with nodes that have no dependencies (indegree = 0)
    queue = deque([n for n in subgraph if indegree[n] == 0])
    ordered = []

    # Step 5: Perform topological sort
    while queue:
        node = queue.popleft()
        ordered.append(node)

        for child in subgraph[node]["outputs"]:
            if child in indegree:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

    # Step 6: Return ordered list
    return ordered

