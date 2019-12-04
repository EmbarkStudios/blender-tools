"""Shared constant values used by the exporter."""


# Name of the Collection that holds Export Collections by default
EXPORT_COLLECTION_NAME = "ExportCollections"


# Groups icon
GROUPS_ICON = 'OUTLINER_OB_GROUP_INSTANCE'


# Property names
PROP_EXPANDED = "export_panel_expanded"
PROP_EXPORT_NAME = "export_name"
PROP_EXPORT_PATH = "export_path"
PROP_EXPORT_TYPE = "export_type"


# Type strings
STATIC_MESH_TYPE = "SM"
SKELETAL_MESH_TYPE = "SK"
MID_POLY_TYPE = "MID"
HIGH_POLY_TYPE = "HIGH"


# Blender enums for export types (referred to in code by the first item in the tuple)
EXPORT_TYPES = [
    (STATIC_MESH_TYPE, "Static Mesh", "Static Mesh", 'MESH', 1),
    (SKELETAL_MESH_TYPE, "Skeletal Mesh", "Skeletal Mesh", 'BONE', 2),
    (MID_POLY_TYPE, "Mid Poly", "Mid Poly", 'MESH', 3),
    (HIGH_POLY_TYPE, "High Poly", "High Poly", 'MESH', 4),
]


# Export type to format mappings
EXPORT_FILE_TYPES = {
    STATIC_MESH_TYPE: "FBX",
    SKELETAL_MESH_TYPE: "FBX",
    MID_POLY_TYPE: "OBJ",
    HIGH_POLY_TYPE: "OBJ",
}
