// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package cli

import (
	"fmt"
	"net/http"
	"os"
	"strings"

	"code.corp.bcollie.net/omnilink/omnilink-base/common/log"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/version"
	"code.corp.bcollie.net/omnilink/omnilink-base/pluginmgr"
	"code.corp.bcollie.net/omnilink/omnilink-base/rpc/jsonclient"
	rpctypes "code.corp.bcollie.net/omnilink/omnilink-base/rpc/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/system/dapp/commands"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"github.com/spf13/cobra"
)

//Run :
func Run(RPCAddr, ParaName, name string) {
	// cli 命令只打印错误级别到控制台
	log.SetLogLevel("error")
	configPath := ""
	for i, arg := range os.Args[:] {
		if arg == "--conf" && i+1 <= len(os.Args)-1 { // --conf omnilink.toml 可以配置读入cli配置文件路径
			configPath = os.Args[i+1]
			break
		}
		if strings.HasPrefix(arg, "--conf=") { // --conf="omnilink.toml"
			configPath = strings.TrimPrefix(arg, "--conf=")
			break
		}
	}
	if configPath == "" {
		if name == "" {
			configPath = "omnilink.toml"
		} else {
			configPath = name + ".toml"
		}
	}

	exist, _ := pathExists(configPath)
	var omnilinkCfg *types.OmnilinkConfig
	if exist {
		omnilinkCfg = types.NewOmnilinkConfig(types.ReadFile(configPath))
	} else {
		cfgstring := types.GetDefaultCfgstring()
		if ParaName != "" {
			cfgstring = strings.Replace(cfgstring, "Title=\"local\"", fmt.Sprintf("Title=\"%s\"", ParaName), 1)
			cfgstring = strings.Replace(cfgstring, "FixTime=false", "CoinSymbol=\"para\"", 1)
		}
		omnilinkCfg = types.NewOmnilinkConfig(cfgstring)
	}

	types.SetCliSysParam(omnilinkCfg.GetTitle(), omnilinkCfg)

	rootCmd := &cobra.Command{
		Use:     omnilinkCfg.GetTitle() + "-cli",
		Short:   omnilinkCfg.GetTitle() + " client tools",
		Version: fmt.Sprintf("%s %s", version.GetVersion(), version.BuildTime),
	}

	closeCmd := &cobra.Command{
		Use:   "close",
		Short: "Close " + omnilinkCfg.GetTitle(),
		Run: func(cmd *cobra.Command, args []string) {
			rpcLaddr, err := cmd.Flags().GetString("rpc_laddr")
			if err != nil {
				panic(err)
			}
			//		rpc, _ := jsonrpc.NewJSONClient(rpcLaddr)
			//		rpc.Call("Omnilink.CloseQueue", nil, nil)
			var res rpctypes.Reply
			ctx := jsonclient.NewRPCCtx(rpcLaddr, "Omnilink.CloseQueue", nil, &res)
			ctx.Run()
		},
	}

	rootCmd.AddCommand(
		commands.CertCmd(),
		commands.AccountCmd(),
		commands.BlockCmd(),
		commands.CoinsCmd(),
		commands.ExecCmd(),
		commands.MempoolCmd(),
		commands.NetCmd(),
		commands.SeedCmd(),
		commands.StatCmd(),
		commands.TxCmd(),
		commands.WalletCmd(),
		commands.VersionCmd(),
		commands.SystemCmd(),
		commands.OneStepSendCmd(),
		commands.OneStepSendCertTxCmd(),
		commands.BlacklistCmd(),
		closeCmd,
		commands.AssetCmd(),
		commands.NoneCmd(),
		commands.BtcScriptCmd(),
	)

	//test tls is enable
	RPCAddr = testTLS(RPCAddr)
	pluginmgr.AddCmd(rootCmd)
	log.SetLogLevel("error")
	omnilinkCfg.S("RPCAddr", RPCAddr)
	omnilinkCfg.S("ParaName", ParaName)
	rootCmd.PersistentFlags().String("rpc_laddr", omnilinkCfg.GStr("RPCAddr"), "http url")
	rootCmd.PersistentFlags().String("paraName", omnilinkCfg.GStr("ParaName"), "parachain")
	rootCmd.PersistentFlags().String("title", omnilinkCfg.GetTitle(), "get title name")
	rootCmd.PersistentFlags().MarkHidden("title")
	rootCmd.PersistentFlags().String("conf", "", "cli config")
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

func testTLS(RPCAddr string) string {
	rpcaddr := RPCAddr
	if !strings.HasPrefix(rpcaddr, "http://") {
		return RPCAddr
	}
	// if http://
	if rpcaddr[len(rpcaddr)-1] != '/' {
		rpcaddr += "/"
	}
	rpcaddr += "test"
	/* #nosec */
	resp, err := http.Get(rpcaddr)
	if err != nil {
		return "https://" + RPCAddr[7:]
	}
	defer resp.Body.Close()
	if resp.StatusCode == 200 {
		return RPCAddr
	}
	return "https://" + RPCAddr[7:]
}

func pathExists(path string) (bool, error) {
	_, err := os.Stat(path)
	if err == nil {
		return true, nil
	}
	if os.IsNotExist(err) {
		return false, nil
	}
	return false, err
}
