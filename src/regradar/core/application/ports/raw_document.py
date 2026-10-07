from collections.abc import Mapping

# A document exactly as the source delivered it, before validation.
type RawDocument = Mapping[str, object]
