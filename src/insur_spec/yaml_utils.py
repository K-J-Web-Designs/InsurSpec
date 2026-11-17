from __future__ import annotations

import io
from typing import Any

try:
    import yaml as _pyyaml
    safe_load = _pyyaml.safe_load
    safe_dump = _pyyaml.safe_dump
except ImportError:
    from ruamel.yaml import YAML

    _yaml_engine = YAML(typ="safe", pure=True)
    _yaml_engine.default_flow_style = False

    def safe_load(stream: Any) -> Any:
        return _yaml_engine.load(stream)

    def safe_dump(data: Any, stream: Any = None, **kwargs: Any) -> Any:
        if stream is not None:
            return _yaml_engine.dump(data, stream)
        buf = io.StringIO()
        _yaml_engine.dump(data, buf)
        return buf.getvalue()


class _YamlModule:
    safe_load = staticmethod(safe_load)
    safe_dump = staticmethod(safe_dump)


yaml = _YamlModule()
