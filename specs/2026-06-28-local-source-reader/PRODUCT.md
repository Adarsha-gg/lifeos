# Local Source-First Reader

## Goal

LifeOS should support a private, local-only reader for full user-provided source texts. The public Vercel learning site remains source-linked and companion-driven; full copyrighted/private material stays off GitHub and off Vercel.

## Behavior

1. The user can place `.txt`, `.md`, `.markdown`, `.html`, or `.htm` files under `private/library/`.
2. `private/` is ignored by Git and never included in Vercel public output.
3. Running `python tools/lifeos_private_library.py build` renders the whole local file content into `output/private-readings/` in the local vault.
4. The local server exposes the private reader at `/private`; public tunnel requests must not be allowed to access it.
5. Reader pages include local text highlighting saved in browser localStorage.
6. The tool does not fetch copyrighted material from the network. It only transforms files the user placed locally.

## Non-goals

- Do not commit private source files.
- Do not deploy private source files to Vercel.
- Do not bypass copyright restrictions by mirroring third-party copyrighted web pages into the public app.
