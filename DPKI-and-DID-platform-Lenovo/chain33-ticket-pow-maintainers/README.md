# Chain33 Ticket/PoW Maintainer Node

This folder runs a local Chain33 node with the built-in `ticket` consensus engine. Chain33 does not expose a consensus named literally `pow`; the PoW-style mining path in the official `33cn/plugin` package is `ticket`, which registers itself as `consensus.name = "ticket"` and mines blocks through ticket difficulty/target checks.

## Run

From this folder:

```powershell
.\start-pow.bat
```

Or with an explicit maintainer count:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-pow.ps1 -Maintainers 4
```

The default monitored maintainer count is `4`. The monitor imports the first four test maintainer keys from `maintainers.json`, unlocks the local wallet, starts `ticket.SetAutoMining`, and reports:

- current block height and height delta
- ticket count
- wallet auto-mining state
- imported maintainer count versus required maintainer count

Stop with `Ctrl+C`. If the node is still running, use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop-pow.ps1
```

## Ports

- JSON-RPC: `http://127.0.0.1:18801`
- gRPC: `127.0.0.1:18802`

These avoid the existing DPKI config ports `8801` and `8802`.

## Files

- `config/ticket-pow.toml`: Chain33 ticket consensus config based on the official ticket test config.
- `maintainers.json`: six public Chain33 test keys; the first four are used by default.
- `scripts/bootstrap-and-monitor.js`: RPC wallet bootstrap plus live monitor.
- `scripts/start-pow.ps1`: starts `bin/omni.exe` with the ticket config and runs the monitor.

## Notes

The keys in `maintainers.json` are public test keys from Chain33 source code. Do not use them outside a local development chain.

Official references:

- Chain33 docs, Mining Setting: https://chain.33.cn/document/195
- Chain33 docs, Consensus Module: https://chain.33.cn/document/180
- Ticket consensus source: https://github.com/33cn/plugin/blob/v1.68.4/plugin/consensus/ticket/ticket.go
- Ticket test config: https://github.com/33cn/plugin/blob/v1.68.4/plugin/consensus/ticket/testdata/chain33.cfg.toml
- Chain33 test keys: https://github.com/33cn/chain33/blob/v1.68.2/util/private.go
