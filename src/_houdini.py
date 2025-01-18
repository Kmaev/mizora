import hou
import re


def parse_variable(snippet_code: str, old_name: str, new_name: str) -> str:
    """
    Updates the 'snippet' parameter of a Houdini node, replacing occurrences of old_name with new_name

    """

    if old_name in snippet_code:
        parsed_code = snippet_code.replace(old_name, new_name)
        return parsed_code
    else:
        return snippet_code


def parse_wildcard_path(path: str) -> list:
    """
    Parses a wildcard path and returns a list of Houdini nodes matching the wildcard.
    """

    hou_path_list = []
    cleaned_path = path.rstrip('*')
    parent_node_list = cleaned_path.split('/')
    if parent_node_list:
        if parent_node_list[0] == '/':
            parent_node_list.pop(0)

        node_starts_with = parent_node_list.pop(-1)  # Extract wildcard prefix
        hou_parent_context = hou.node('/' + '/'.join(parent_node_list))

        if not hou_parent_context:
            raise RuntimeError(f"Invalid parent context: {hou_parent_context}")

        for child in hou_parent_context.children():
            if child.name().startswith(node_starts_with):
                hou_path_list.append(child)
    return hou_path_list


def get_hou_search_context(path: str) -> list:
    """
    Returns a list of Houdini nodes based on the given path.
    The context of these nodes will be used for future searches.
    """
    if not path:
        hou.ui.displayMessage(
            text='The path cannot be empty.',
            buttons=('OK',),
            title="Error",
            severity=hou.severityType.Error
        )
        raise ValueError("The path cannot be empty.")
    if not path.startswith("/"):
        hou.ui.displayMessage(
            text=f"Invalid Houdini node path: {path}",
            buttons=('OK',),
            title="Error",
            severity=hou.severityType.Error
        )
        raise ValueError(f"Invalid Houdini node path: {path} Pattern must start with '/'")
    segments = path.split("/")

    # Assume the first candidate is always "/"
    # Because we can find multiple roots that might match the pattern,
    # we need to collect the list of all possible roots that match it.
    candidates = [hou.node("/")]
    new_candidates = []
    path_list = []

    while segments:
        segment = segments.pop(0)

        # Empty strings mean double or leading '/' and we can ignore them
        if not segment:
            continue

        for candidate in list(candidates):
            # For each candidate if there's a "*" in the segment, we need to check
            # that every individual child matches the name we want to find.
            if "*" in segment:
                for child in candidate.children():
                    if hou.text.patternMatch(segment, child.name()):
                        new_candidates.append(child)
            else:
                node = candidate.node(segment)
                if node:
                    new_candidates.append(node)

        # Reset the candidates
        candidates = new_candidates
        new_candidates = []

    for candidate in candidates:
        path_list.append(hou.node(candidate.path()))
    return path_list


def find_variable_occurrences(context: list, searched_var: str) -> dict:
    """
    Recursively finds occurrences of a searched variable in a given context using regular expressions.


    Returns:
        dict: A dictionary where keys are nodes containing the variable and values are the snippets containing it.
    """
    nodes = {}

    pattern = re.compile(rf'{re.escape(searched_var)}')
    for geo in context:
        for child in geo.children():
            # Check if the child is attribwrangle
            if child.type().name() == 'attribwrangle':
                snippet = child.parm('snippet').eval()
                if pattern.search(snippet):
                    nodes[child] = snippet

            # Recursive check
            nodes.update(find_variable_occurrences([child], searched_var))
    return nodes
