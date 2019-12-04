"""Export Operators."""

from .add_to_collection import EmbarkAddToCollection
from .delete_export_collection import EmbarkDeleteExportCollection
from .export_all import EmbarkExportAll
from .export_by_selection import EmbarkExportBySelection
from .export import EmbarkExportCollection
from .new_export_collection import EmbarkNewExportCollection
from .new_export_collections_per_object import EmbarkNewExportCollectionsPerObject
from .remove_from_collection import EmbarkRemoveFromCollection
from .select_export_collection import EmbarkSelectExportCollection


REGISTER_CLASSES = (
    EmbarkAddToCollection,
    EmbarkDeleteExportCollection,
    EmbarkExportAll,
    EmbarkExportBySelection,
    EmbarkExportCollection,
    EmbarkNewExportCollection,
    EmbarkNewExportCollectionsPerObject,
    EmbarkRemoveFromCollection,
    EmbarkSelectExportCollection,
)
