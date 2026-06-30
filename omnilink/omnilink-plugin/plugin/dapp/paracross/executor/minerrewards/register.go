package minerrewards

import (
	"fmt"

	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	pt "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/paracross/types"
)

type RewardPolicy interface {
	GetConfigReward(cfg *types.OmnilinkConfig, height int64) (int64, int64, int64)
	RewardMiners(cfg *types.OmnilinkConfig, coinReward int64, miners []string, height int64) ([]*pt.ParaMinerReward, int64)
}

var MinerRewards = make(map[string]RewardPolicy)

func register(ty string, policy RewardPolicy) {
	if _, ok := MinerRewards[ty]; ok {
		panic(fmt.Sprintf("paracross minerreward ty=%s registered", ty))
	}
	MinerRewards[ty] = policy
}
