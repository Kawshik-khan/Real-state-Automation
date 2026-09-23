"""GLG Assets Social AI OS — Backend Application Package."""
import warnings

# Suppress all deprecation and runtime warnings globally on startup
warnings.simplefilter("ignore")
warnings.filterwarnings("ignore")

# ── Future-Proof LangChain/LangGraph Serialization ────────────────────────
# Explicitly set Reviver default allowed_objects to 'core' so any internal
# cache or checkpointer serializer is strictly future-proof without warnings.
try:
    import langchain_core.load.load as _lc_load
    if hasattr(_lc_load, "Reviver"):
        _orig_reviver_init = _lc_load.Reviver.__init__

        def _future_proof_reviver_init(self, *args, allowed_objects="core", **kwargs):
            if allowed_objects is None:
                allowed_objects = "core"
            return _orig_reviver_init(self, *args, allowed_objects=allowed_objects, **kwargs)

        _lc_load.Reviver.__init__ = _future_proof_reviver_init
except Exception:
    pass
