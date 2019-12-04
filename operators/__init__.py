"""Custom Blender Operators that are loaded by default with the Embark Tools.

If you add a new Operator, please define register() and unregister() functions
for it, and then import it in this file and add it to the __operators__ list.
"""


from . import (
    add_spiral,
    connect_contextual,
    documentation,
    frame_contextual,
    importer,
    update,
)


# List of operators to load by default.
REGISTER_CLASSES = (
    add_spiral,
    connect_contextual,
    documentation,
    frame_contextual,
    importer,
    update,
)
