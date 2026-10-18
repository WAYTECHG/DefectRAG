"""Read-only dependency visibility report for editor/runtime troubleshooting."""
import importlib.util
import json
import sys

if __name__=='__main__':
    names=['fastapi','uvicorn','torch','transformers','langchain_core','langchain_community','langchain_text_splitters','langgraph']
    modules={name:((spec.origin or list(spec.submodule_search_locations or [])) if (spec:=importlib.util.find_spec(name)) else None) for name in names}
    print(json.dumps({'python':sys.executable,'modules':modules,'all_visible':all(v is not None for v in modules.values())},indent=2))
    raise SystemExit(0 if all(v is not None for v in modules.values()) else 1)
