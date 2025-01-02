import hou


def parse_variable(node: object, old_name: str, new_name: str) -> None:
    """
    Updates the 'snippet' parameter of a Houdini node, replacing occurrences of old_name with new_name

    """
    snippet_code = node.parm('snippet').eval()
    if old_name in snippet_code:
        parsed_code = snippet_code.replace(old_name, new_name)
        node.parm('snippet').set(parsed_code)


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

    hou_contexts_list = []

    # Create context list based on the path
    # Wildcard case
    if path.endswith("*"):

        hou_contexts_list = parse_wildcard_path(path)

    else:
        # Append directly if no wildcard used
        node = hou.node(path)
        if node:
            hou_contexts_list.append(node)

        else:
            hou.ui.displayMessage(
                text=f"Invalid Houdini node path: {path}",
                buttons=('OK',),
                title="Error",
                severity=hou.severityType.Error
            )
            raise RuntimeError(f"Invalid Houdini node path: {path}")

    # RETURN
    if hou_contexts_list:
        return hou_contexts_list

        # Error message if no valid context is found
    else:
        hou.ui.displayMessage(
            text='No valid context was selected. Please select a valid context. For example: "/obj/my_geometry".',
            buttons=('OK',),
            title="Error",
            severity=hou.severityType.Error
        )
        raise RuntimeError('No valid context was selected')


def find_variable_occurrences(context: list, searched_var: str) -> dict:
    """
    Recursively finds occurrences of a searched variable in a given context.

    Returns:
        dict: A dictionary where keys are nodes containing the variable and values are the snippets containing it.
    """
    nodes = {}

    for geo in context:
        for child in geo.children():
            # Check if the child is attribwrangle
            if child.type().name() == 'attribwrangle':
                snippet = child.parm('snippet').eval()
                if searched_var in snippet:
                    nodes[child] = snippet

            # Recursive check
            nodes.update(find_variable_occurrences([child], searched_var))

    return nodes
