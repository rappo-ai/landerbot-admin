from typing import Any, List


def add_padding(button_list: List, row_width: int, padding_obj: Any = "."):
    padding = (row_width - len(button_list) % row_width) % row_width
    if padding:
        button_list.extend([padding_obj] * padding)
