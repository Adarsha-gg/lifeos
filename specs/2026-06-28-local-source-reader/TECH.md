# Local Source-First Reader — Tech Spec

## Current context

- `tools/lifeos_vercel_build.py` builds the public static site into `public/` using an isolated vault.
- `.gitignore` excludes generated/public/private runtime data.
- `tools/lifeos_server.py` already blocks public tunnel requests outside the `/learn`/HTML lesson surface and authenticated `/api/progress`.

## Implementation

- Add `tools/lifeos_private_library.py`.
  - Input root: `LIFEOS_PRIVATE_LIBRARY` or `private/library/`.
  - Output root: `VAULT_ROOT/output/private-readings/`.
  - Commands: `init`, `list`, `build`.
  - Supported files: `.txt`, `.md`, `.markdown`, `.html`, `.htm`.
  - Renders all source content, not summaries.
  - Adds localStorage-backed text highlighting.
- Add `private/` to `.gitignore`.
- Add `/private` route to `tools/lifeos_server.py`.
  - Builds private pages lazily if missing.
  - Public tunnel guard already rejects `/private` because it is not in `public_get_allowed()`.

## Validation

- `python -m py_compile tools/lifeos_private_library.py tools/lifeos_server.py`
- `python tools/lifeos_private_library.py init`
- Build with sample local files under a temp `LIFEOS_PRIVATE_LIBRARY` and temp `LIFEOS_VAULT`.
- Verify generated pages include the complete sample text and highlighter script.
- Verify public-route guard rejects `/private` when a public host/Cloudflare header is present.
