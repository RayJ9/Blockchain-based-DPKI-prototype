// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// Package commands 系统级dapp相关命令包
package commands

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/rpc/jsonclient"
	rpctypes "code.corp.bcollie.net/omnilink/omnilink-base/rpc/types"
	"github.com/spf13/cobra"
)

// SystemCmd get system config command
func SystemCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "system",
		Short: "Get node system info",
		Args:  cobra.MinimumNArgs(1),
	}
	cmd.AddCommand(
		getConfigCmd(),
	)
	return cmd
}

// SystemCmd get system config command
func getConfigCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "config",
		Short: "Get node config",
		Run:   config,
	}
	return cmd
}

func config(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	var res rpctypes.ChainConfigInfo
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Omnilink.GetChainConfig", nil, &res)
	ctx.Run()

}
