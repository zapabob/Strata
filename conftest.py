r"""pytest: setup.py's data-folder migration (#198) saves the data folder it settled on in the user's settings file
(%APPDATA%\Strata\settings.json, ~/.config/strata/settings.json) and can MOVE model files from a folder it finds there.
A test that reaches it must never touch the real file, so the whole session gets its own config home."""
import os
import tempfile

# A caller's live local-server key must not authenticate synthetic test servers.
# Authentication cases supply their own fixture keys explicitly.
os.environ.pop("STRATA_API_KEY", None)

_home = tempfile.mkdtemp(prefix="strata-pytest-config-")
os.environ["APPDATA"] = _home
os.environ["XDG_CONFIG_HOME"] = _home
# The per-user STATE and DATA folders too (%LOCALAPPDATA%\Strata: tuning/recheck.json, the engine store, the update records; ~/.local/state, ~/.local/share).
# A test that installs a stub engine marks saved tuning presets for a re-check there: on 2026-10-24 one such run left an entry in the owner's real
# tuning\recheck.json. A test that wants a place of its own still names it (STRATA_COMPONENTS_DIR, state_base=...).
os.environ["LOCALAPPDATA"] = _home
os.environ["XDG_STATE_HOME"] = _home
os.environ["XDG_DATA_HOME"] = _home


def pytest_configure(config) -> None:
    """Clamp thinc seeds: pytest-randomly passes (seed+offset) unclamped to entry-point seeders.

    numpy gets ``seed % 2**32`` inside pytest-randomly, but thinc.util.fix_random_seed receives
    the raw sum and can raise ``ValueError: Seed must be between 0 and 2**32 - 1`` (seen on
    tests/test_hakua_hermes_memory_stack.py when hakua-memory pulls thinc in).
    """
    del config  # required pytest hook signature; unused
    try:
        import thinc.util as thinc_util
    except Exception:
        return
    original = thinc_util.fix_random_seed

    def _clamped_fix_random_seed(seed: int = 0) -> None:
        original(int(seed) % (2**32))

    thinc_util.fix_random_seed = _clamped_fix_random_seed  # type: ignore[assignment]
