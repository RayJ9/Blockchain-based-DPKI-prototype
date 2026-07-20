# Omnilink binary runtime

This directory is the redistributable Omnilink runtime used by every blockchain
experiment in this repository. It contains a compressed Windows x64 executable,
the PoW configuration template, a release manifest, and SHA-256 checksums. The
Omnilink source tree is not required at experiment time.

Install or verify the runtime manually with:

```powershell
.\omnilink-runtime\Install-OmnilinkRuntime.ps1
.\omnilink-runtime\Install-OmnilinkRuntime.ps1 -VerifyOnly
```

The four-node and three-chain launchers call the installer automatically. The
extracted `bin/windows-x64/omni.exe` is a generated local file; the versioned
release artifact is `releases/omnilink-windows-x64.zip`.

The binary redistribution notice is retained in `LICENSE`.

The current package targets Windows x64. Rebuilding Omnilink is intentionally
outside the public reproduction path; the source snapshot is retained in the
authors' private research archive.
