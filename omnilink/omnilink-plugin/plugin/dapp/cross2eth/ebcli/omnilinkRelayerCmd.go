package main

import (
	"fmt"

	"code.corp.bcollie.net/omnilink/omnilink-base/rpc/jsonclient"
	rpctypes "code.corp.bcollie.net/omnilink/omnilink-base/rpc/types"
	ebTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/utils"
	"github.com/spf13/cobra"
)

//OmnilinkRelayerCmd RelayerCmd command func
func OmnilinkRelayerCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "omnilink ",
		Short: "Omnilink relayer ",
		Args:  cobra.MinimumNArgs(1),
	}

	cmd.AddCommand(
		ImportPrivateKeyCmd(),
		ShowValidatorAddrCmd(),
		ShowTxsHashCmd(),
		LockAsyncFromOmnilinkCmd(),
		BurnfromOmnilinkCmd(),
		simBurnFromEthCmd(),
		simLockFromEthCmd(),
		ShowBridgeRegistryAddr4omnilinkCmd(),
		TokenAddressCmd(),
		MultiSignCmd(),
		ResendOmnilinkEventCmd(),
		WithdrawFromOmnilinkCmd(),
		BurnWithIncreasefromOmnilinkCmd(),
	)

	return cmd
}

//TokenAddressCmd...
func TokenAddressCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "token",
		Short: "show token address and it's corresponding symbol",
		Args:  cobra.MinimumNArgs(1),
	}
	cmd.AddCommand(
		ShowTokenAddressCmd(),
	)
	return cmd
}

func ShowTokenAddressCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "show",
		Short: "show token address",
		Run:   ShowTokenAddress,
	}
	ShowTokenFlags(cmd)
	return cmd
}

//SetTokenFlags ...
func ShowTokenFlags(cmd *cobra.Command) {
	cmd.Flags().StringP("symbol", "s", "", "token symbol(optional), if not set,show all the token")
}

func ShowTokenAddress(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	symbol, _ := cmd.Flags().GetString("symbol")

	var res ebTypes.TokenAddressArray
	para := ebTypes.TokenAddress{
		Symbol:    symbol,
		ChainName: ebTypes.OmnilinkBlockChainName,
	}

	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Manager.ShowTokenAddress", para, &res)
	ctx.Run()
}

func ShowBridgeRegistryAddr4omnilinkCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "bridgeRegistry",
		Short: "show the address of Contract BridgeRegistry for omnilink",
		Run:   ShowBridgeRegistryAddr4omnilink,
	}
	return cmd
}

//ShowBridgeRegistryAddr ...
func ShowBridgeRegistryAddr4omnilink(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	var res ebTypes.ReplyAddr
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Manager.ShowBridgeRegistryAddr4omnilink", nil, &res)
	ctx.Run()
}

func simBurnFromEthCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "sim-burn",
		Short: "simulate burn bty assets from ethereum",
		Run:   simBurnFromEth,
	}
	SimBurnFlags(cmd)
	return cmd
}

//SimBurnFlags ...
func SimBurnFlags(cmd *cobra.Command) {
	cmd.Flags().StringP("key", "k", "", "Ethereum sender address")
	_ = cmd.MarkFlagRequired("key")
	cmd.Flags().StringP("token", "t", "", "token address")
	_ = cmd.MarkFlagRequired("token")
	cmd.Flags().StringP("receiver", "r", "", "receiver address on omnilink")
	_ = cmd.MarkFlagRequired("receiver")
	cmd.Flags().Float64P("amount", "m", float64(0), "amount")
	_ = cmd.MarkFlagRequired("amount")
}

func simBurnFromEth(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	key, _ := cmd.Flags().GetString("key")
	tokenAddr, _ := cmd.Flags().GetString("token")
	amount, _ := cmd.Flags().GetFloat64("amount")
	receiver, _ := cmd.Flags().GetString("receiver")

	realAmount := utils.ToWei(amount, 8)

	para := ebTypes.Burn{
		OwnerKey:         key,
		TokenAddr:        tokenAddr,
		Amount:           realAmount.String(),
		OmnilinkReceiver: receiver,
	}
	var res rpctypes.Reply
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Manager.SimBurnFromEth", para, &res)
	ctx.Run()
}

func simLockFromEthCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "sim-lock",
		Short: "simulate lock eth/erc20 assets from ethereum",
		Run:   simLockFromEth,
	}
	simLockEthErc20AssetFlags(cmd)
	return cmd
}

//LockEthErc20AssetFlags ...
func simLockEthErc20AssetFlags(cmd *cobra.Command) {
	cmd.Flags().StringP("key", "k", "", "Ethereum sender address")
	_ = cmd.MarkFlagRequired("key")
	cmd.Flags().StringP("token", "t", "", "token address, optional, nil for ETH")
	cmd.Flags().Float64P("amount", "m", float64(0), "amount")
	_ = cmd.MarkFlagRequired("amount")
	cmd.Flags().StringP("receiver", "r", "", "omnilink receiver address")
	_ = cmd.MarkFlagRequired("receiver")
}

func simLockFromEth(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	key, _ := cmd.Flags().GetString("key")
	tokenAddr, _ := cmd.Flags().GetString("token")
	amount, _ := cmd.Flags().GetFloat64("amount")
	receiver, _ := cmd.Flags().GetString("receiver")

	realAmount := utils.ToWei(amount, 8)

	para := ebTypes.LockEthErc20{
		OwnerKey:         key,
		TokenAddr:        tokenAddr,
		Amount:           realAmount.String(),
		OmnilinkReceiver: receiver,
	}
	var res rpctypes.Reply
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Manager.SimLockFromEth", para, &res)
	ctx.Run()
}

//LockAsyncCmd ...
func LockAsyncFromOmnilinkCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "lock",
		Short: "async lock bty from omnilink and cross-chain transfer to ethereum",
		Run:   LockBTYAssetAsync,
	}
	LockBTYAssetFlags(cmd)
	return cmd
}

func LockBTYAssetFlags(cmd *cobra.Command) {
	cmd.Flags().StringP("key", "k", "", "owner private key")
	_ = cmd.MarkFlagRequired("key")
	cmd.Flags().Float64P("amount", "m", float64(0), "amount")
	_ = cmd.MarkFlagRequired("amount")
	cmd.Flags().StringP("receiver", "r", "", "etheruem receiver address")
	_ = cmd.MarkFlagRequired("receiver")
}

func LockBTYAssetAsync(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	key, _ := cmd.Flags().GetString("key")
	amount, _ := cmd.Flags().GetFloat64("amount")
	receiver, _ := cmd.Flags().GetString("receiver")

	realAmount := utils.ToWei(amount, 8)

	para := ebTypes.LockBTY{
		OwnerKey:        key,
		Amount:          realAmount.String(),
		EtherumReceiver: receiver,
	}
	var res rpctypes.Reply
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Manager.LockBTYAssetAsync", para, &res)
	ctx.Run()
}

func BurnfromOmnilinkCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "burn",
		Short: "async burn the asset from omnilink to make it unlocked on ethereum",
		Run:   BurnAsyncFromOmnilink,
	}
	BurnAsyncFromOmnilinkFlags(cmd)
	return cmd
}

//BurnAsyncFromOmnilinkFlags ...
func BurnAsyncFromOmnilinkFlags(cmd *cobra.Command) {
	cmd.Flags().StringP("key", "k", "", "owner private key for omnilink")
	_ = cmd.MarkFlagRequired("key")
	cmd.Flags().StringP("token", "t", "", "token address")
	_ = cmd.MarkFlagRequired("token")
	cmd.Flags().StringP("receiver", "r", "", "receiver address on Ethereum")
	_ = cmd.MarkFlagRequired("receiver")
	cmd.Flags().Float64P("amount", "m", float64(0), "amount")
	_ = cmd.MarkFlagRequired("amount")
}

func BurnAsyncFromOmnilink(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	key, _ := cmd.Flags().GetString("key")
	tokenAddr, _ := cmd.Flags().GetString("token")
	amount, _ := cmd.Flags().GetFloat64("amount")
	receiver, _ := cmd.Flags().GetString("receiver")

	d, err := utils.SimpleGetDecimals(tokenAddr)
	if err != nil {
		fmt.Println("get decimals err")
		return
	}
	para := ebTypes.BurnFromOmnilink{
		OwnerKey:         key,
		TokenAddr:        tokenAddr,
		Amount:           utils.ToWei(amount, d).String(),
		EthereumReceiver: receiver,
	}
	var res rpctypes.Reply
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Manager.BurnAsyncFromOmnilink", para, &res)
	ctx.Run()
}

func BurnWithIncreasefromOmnilinkCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "burn_increase",
		Short: "async burn the asset from omnilink to make it unlocked on ethereum",
		Run:   BurnWithIncreaseAsyncFromOmnilink,
	}
	BurnAsyncFromOmnilinkFlags(cmd)
	return cmd
}

func BurnWithIncreaseAsyncFromOmnilink(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	key, _ := cmd.Flags().GetString("key")
	tokenAddr, _ := cmd.Flags().GetString("token")
	amount, _ := cmd.Flags().GetFloat64("amount")
	receiver, _ := cmd.Flags().GetString("receiver")

	d, err := utils.SimpleGetDecimals(tokenAddr)
	if err != nil {
		fmt.Println("get decimals err")
		return
	}
	para := ebTypes.BurnFromOmnilink{
		OwnerKey:         key,
		TokenAddr:        tokenAddr,
		Amount:           utils.ToWei(amount, d).String(),
		EthereumReceiver: receiver,
	}
	var res rpctypes.Reply
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Manager.BurnWithIncreaseAsyncFromOmnilink", para, &res)
	ctx.Run()
}

//ImportPrivateKeyCmd SetPwdCmd set password
func ImportPrivateKeyCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "import_privatekey",
		Short: "import omnilink private key to sign txs to be submitted to omnilink evm",
		Run:   importPrivatekey,
	}
	addImportPrivateKeyFlags(cmd)
	return cmd
}

func addImportPrivateKeyFlags(cmd *cobra.Command) {
	cmd.Flags().StringP("key", "k", "", "omnilink private key")
	_ = cmd.MarkFlagRequired("key")
}

func importPrivatekey(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	privateKey, _ := cmd.Flags().GetString("key")
	importKeyReq := ebTypes.ImportKeyReq{
		PrivateKey: privateKey,
	}

	var res rpctypes.Reply
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Manager.ImportOmnilinkRelayerPrivateKey", importKeyReq, &res)
	ctx.Run()
}

//ShowValidatorAddrCmd ...
func ShowValidatorAddrCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "show_validator",
		Short: "show me the validator",
		Run:   showValidatorAddr,
	}
	return cmd
}

func showValidatorAddr(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	var res string
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Manager.ShowOmnilinkRelayerValidator", nil, &res)
	ctx.Run()
}

//ShowTxsHashCmd ...
func ShowTxsHashCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "show_txhashes",
		Short: "show me the tx hashes",
		Run:   showOmnilinkRelayer2EthTxs,
	}
	return cmd
}

func showOmnilinkRelayer2EthTxs(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")

	var res ebTypes.Txhashes
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Manager.ShowOmnilinkRelayer2EthTxs", nil, &res)
	if _, err := ctx.RunResult(); nil != err {
		errInfo := err.Error()
		fmt.Println("errinfo:" + errInfo)
		return
	}
	for _, hash := range res.Txhash {
		fmt.Println(hash)
	}
}

func ResendOmnilinkEventCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "resendOmnilinkEvent",
		Short: "resend OmnilinkEvent to ethereum process goroutine",
		Run:   resendOmnilinkEvent,
	}
	addResendOmnilinkEventFlags(cmd)
	return cmd
}

func addResendOmnilinkEventFlags(cmd *cobra.Command) {
	cmd.Flags().Int64P("height", "g", 0, "height begin to resend omnilink event ")
	_ = cmd.MarkFlagRequired("height")
}

func resendOmnilinkEvent(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	height, _ := cmd.Flags().GetInt64("height")
	resendOmnilinkEventReq := &ebTypes.ResendOmnilinkEventReq{
		Height: height,
	}

	var res rpctypes.Reply
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Manager.ResendOmnilinkEvent", resendOmnilinkEventReq, &res)
	ctx.Run()
}

func WithdrawFromOmnilinkCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "withdraw",
		Short: "async withdraw the asset from omnilink to make it unlocked on ethereum",
		Run:   WithdrawFromOmnilink,
	}
	addWithdrawFromOmnilinkFlags(cmd)
	return cmd
}

//addWithdrawFromOmnilinkCmdFlags ...
func addWithdrawFromOmnilinkFlags(cmd *cobra.Command) {
	cmd.Flags().StringP("key", "k", "", "owner private key for omnilink")
	_ = cmd.MarkFlagRequired("key")
	cmd.Flags().StringP("token", "t", "", "token address")
	_ = cmd.MarkFlagRequired("token")
	cmd.Flags().StringP("receiver", "r", "", "receiver address on Ethereum")
	_ = cmd.MarkFlagRequired("receiver")
	cmd.Flags().Float64P("amount", "m", float64(0), "amount")
	_ = cmd.MarkFlagRequired("amount")
}

func WithdrawFromOmnilink(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	key, _ := cmd.Flags().GetString("key")
	tokenAddr, _ := cmd.Flags().GetString("token")
	amount, _ := cmd.Flags().GetFloat64("amount")
	receiver, _ := cmd.Flags().GetString("receiver")

	d, err := utils.SimpleGetDecimals(tokenAddr)
	if err != nil {
		fmt.Println("get decimals err")
		return
	}
	para := ebTypes.WithdrawFromOmnilink{
		OwnerKey:         key,
		TokenAddr:        tokenAddr,
		Amount:           utils.ToWei(amount, d).String(),
		EthereumReceiver: receiver,
	}
	var res rpctypes.Reply
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Manager.WithdrawFromOmnilink", para, &res)
	ctx.Run()
}
