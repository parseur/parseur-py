"""The "please install parseur-py[mcp]" hint must only appear when `mcp` is
missing. If `mcp` is installed but unusable (e.g. mcp 2.x, which removed
`mcp.server.fastmcp`), the real import error must reach the user instead.

Each case imports ``parseur.mcp_server`` in a fresh interpreter so the
simulated environments cannot leak into other tests. These tests do not need
the ``mcp`` extra.
"""

import os
import subprocess
import sys
import textwrap

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALL_HINT = 'pip install "parseur-py[mcp]"'


def _import_mcp_server(prelude, extra_path=None):
    code = prelude + "\nimport parseur.mcp_server\n"
    path = [p for p in (extra_path, REPO_ROOT) if p]
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(path))
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )


def test_install_hint_when_mcp_is_missing():
    # Make `import mcp` fail exactly as it does when the package is absent,
    # even if it happens to be installed in this environment.
    prelude = textwrap.dedent("""
        import sys

        class _HideMcp:
            def find_spec(self, name, path=None, target=None):
                if name == "mcp":
                    raise ModuleNotFoundError("No module named 'mcp'", name="mcp")
                return None

        sys.meta_path.insert(0, _HideMcp())
        """)
    result = _import_mcp_server(prelude)

    assert result.returncode != 0
    assert INSTALL_HINT in result.stderr


def test_real_error_when_installed_mcp_is_incompatible(tmp_path):
    # A stand-in for mcp 2.x: the `mcp` package exists but has no
    # `mcp.server.fastmcp` module.
    pkg = tmp_path / "mcp"
    (pkg / "server").mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "server" / "__init__.py").write_text("")
    (pkg / "types.py").write_text(textwrap.dedent("""
            class ToolAnnotations:
                pass
            """))

    result = _import_mcp_server("", extra_path=str(tmp_path))

    assert result.returncode != 0
    assert "mcp.server.fastmcp" in result.stderr
    assert INSTALL_HINT not in result.stderr
