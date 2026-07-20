# Omnilink PoW 4-node runtime

This runtime starts four independent Omnilink processes. Each process is one
PoW maintainer/miner, and the aggregate target mining interval is controlled by
`-MeanBlockMs`.

The launcher uses the verified precompiled runtime under `omnilink-runtime/`;
Go and the Omnilink source tree are not required.

```powershell
.\pow-4nodes-runtime\scripts\start-omnilink-pow-4nodes.ps1 -Clean -MeanBlockMs 200
node .\dpki-experiment-prototype\run-real-dpki-experiment.js --consensus-backend pow --rpc http://127.0.0.1:8545
.\pow-4nodes-runtime\scripts\stop-omnilink-pow-4nodes.ps1
```

By default the network does not mine empty blocks. This is the recommended DPKI
experiment mode because PoW service starts when the request queue has
transactions. Use `-MineEmpty` only when you explicitly want to observe idle
block production.

Default ports:

- node0: Web3 `8545`, Chain JSON-RPC `8801`, health `8805`, P2P `13803`
- node1: Web3 `8555`, Chain JSON-RPC `8811`, health `8815`, P2P `13804`
- node2: Web3 `8565`, Chain JSON-RPC `8821`, health `8825`, P2P `13805`
- node3: Web3 `8575`, Chain JSON-RPC `8831`, health `8835`, P2P `13806`
