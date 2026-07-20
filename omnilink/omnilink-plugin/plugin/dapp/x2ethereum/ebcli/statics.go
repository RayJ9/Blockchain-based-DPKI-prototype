package main

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/rpc/jsonclient"
	ebTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/types"
	"github.com/spf13/cobra"
)

//StaticsCmd ...
func StaticsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "statics",
		Short: "statics of lock/unlock Eth or ERC20,or deposit/burn omnilink asset ",
		Args:  cobra.MinimumNArgs(1),
	}

	cmd.AddCommand(
		ShowLockStaticsCmd(),
		ShowDepositStaticsCmd(),
	)

	return cmd
}

//ShowLockStaticsCmd ...
func ShowLockStaticsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "lock",
		Short: "show the lock statics of ETH or ERC20",
		Run:   ShowLockStatics,
	}
	ShowLockStaticsFlags(cmd)
	return cmd
}

//ShowLockStaticsFlags ...
func ShowLockStaticsFlags(cmd *cobra.Command) {
	cmd.Flags().StringP("token", "t", "", "token address, optional, nil for ETH")
}

//ShowLockStatics ...
func ShowLockStatics(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	tokenAddr, _ := cmd.Flags().GetString("token")

	para := ebTypes.TokenStatics{
		TokenAddr: tokenAddr,
	}
	var res ebTypes.StaticsLock
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Manager.ShowLockStatics", para, &res)
	ctx.Run()
}

//ShowDepositStaticsCmd ...
func ShowDepositStaticsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "deposit",
		Short: "show the deposit statics of omnilink asset",
		Run:   ShowDepositStatics,
	}
	ShowDepositStaticsFlags(cmd)
	return cmd
}

//ShowDepositStaticsFlags ...
func ShowDepositStaticsFlags(cmd *cobra.Command) {
	cmd.Flags().StringP("token", "t", "", "token address")
	_ = cmd.MarkFlagRequired("token")
}

//ShowDepositStatics ...
func ShowDepositStatics(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	tokenAddr, _ := cmd.Flags().GetString("token")

	para := ebTypes.TokenStatics{
		TokenAddr: tokenAddr,
	}
	var res ebTypes.StaticsDeposit
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Manager.ShowDepositStatics", para, &res)
	ctx.Run()
}
