package omnilink

import (
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/bridgevmxgo/boss4x/omnilink/offline"
	"github.com/spf13/cobra"
)

func OmnilinkCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "omnilink",
		Short: "deploy to omnilink",
	}
	cmd.AddCommand(
		offline.Boss4xOfflineCmd(),
		NewOracleClaimCmd(),
	)
	return cmd

}
