package executor

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	ptypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/js/types"
)

func calcAllPrefix(cfg *types.OmnilinkConfig, name string) ([]byte, []byte) {
	execer := cfg.ExecName("user." + ptypes.JsX + "." + name)
	state := types.CalcStatePrefix([]byte(execer))
	local := types.CalcLocalPrefix([]byte(execer))
	return state, local
}

func calcCodeKey(name string) []byte {
	return append([]byte("mavl-"+ptypes.JsX+"-code-"), []byte(name)...)
}
