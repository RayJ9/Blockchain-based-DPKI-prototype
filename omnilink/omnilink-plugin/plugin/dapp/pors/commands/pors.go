// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package commands

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"math/rand"
	"os"
	"strconv"
	"time"

	"code.corp.bcollie.net/omnilink/omnilink-base/common/address"

	"code.corp.bcollie.net/omnilink/omnilink-base/common/crypto"
	"code.corp.bcollie.net/omnilink/omnilink-base/rpc/jsonclient"
	rpctypes "code.corp.bcollie.net/omnilink/omnilink-base/rpc/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	ttypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/consensus/pors/types"
	vt "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/pors/types"
	"github.com/spf13/cobra"
)

var (
	strChars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" // 62 characters
	genFile  = "genesis_file.json"
	pvFile   = "priv_validator_"
	//AuthBLS ...
	AuthBLS = 259
)

// ValCmd qbftNode cmd register
func ValCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "pors",
		Short: "Construct pors transactions",
		Args:  cobra.MinimumNArgs(1),
	}
	cmd.AddCommand(
		IsSyncCmd(),
		GetBlockInfoCmd(),
		GetNodeInfoCmd(),
		GetCurrentStateCmd(),
		UpdateNodePowerCmd(),
		CreateKeyFileCmd(),
	)
	return cmd
}

// IsSyncCmd query qbft is sync
func IsSyncCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "is_sync",
		Short: "Query pors consensus is sync",
		Run:   isSync,
	}
	return cmd
}

func isSync(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	var res bool
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "pors.IsSync", nil, &res)
	ctx.Run()
}

// GetNodeInfoCmd get validator nodes
func GetNodeInfoCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "nodes",
		Short: "Get pors validator nodes",
		Run:   getNodeInfo,
	}
	return cmd
}

func getNodeInfo(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	var res *vt.PorsNodeInfoSet
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "pors.GetNodeInfo", nil, &res)
	ctx.Run()
}

// GetBlockInfoCmd get block info
func GetBlockInfoCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "info",
		Short: "Get pors consensus info",
		Run:   getBlockInfo,
	}
	addGetBlockInfoFlags(cmd)
	return cmd
}

func addGetBlockInfoFlags(cmd *cobra.Command) {
	cmd.Flags().Int64P("height", "t", 0, "block height (larger than 0)")
	cmd.MarkFlagRequired("height")
}

func getBlockInfo(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	height, _ := cmd.Flags().GetInt64("height")
	req := &vt.ReqPorsBlockInfo{
		Height: height,
	}
	params := rpctypes.Query4Jrpc{
		Execer:   vt.PorsX,
		FuncName: "GetBlockInfoByHeight",
		Payload:  types.MustPBToJSON(req),
	}

	var res vt.PorsBlockInfo
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Omnilink.Query", params, &res)
	ctx.SetResultCb(jsonOutput)
	result, err := ctx.RunResult()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return
	}
	fmt.Println(result)
}

func jsonOutput(arg interface{}) (interface{}, error) {
	res := arg.(types.Message)
	data, err := types.PBToJSON(res)
	if err != nil {
		return nil, err
	}
	var buf bytes.Buffer
	err = json.Indent(&buf, data, "", "    ")
	if err != nil {
		return nil, err
	}
	return buf.String(), nil
}

// GetCurrentStateCmd get current consensus state
func GetCurrentStateCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "state",
		Short: "Get pors current consensus state",
		Run:   getCurrentState,
	}
	return cmd
}

func getCurrentState(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	params := rpctypes.Query4Jrpc{
		Execer:   vt.PorsX,
		FuncName: "GetCurrentState",
	}

	var res vt.PorsState
	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Omnilink.Query", params, &res)
	ctx.SetResultCb(jsonOutput)
	result, err := ctx.RunResult()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return
	}
	fmt.Println(result)
}

// UpdateNodePowerCmd add validator power
func UpdateNodePowerCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "update",
		Short: "Update pors validator power",
		Run:   updateNodePower,
	}
	updateNodePowerFlags(cmd)
	return cmd
}

func updateNodePowerFlags(cmd *cobra.Command) {
	cmd.Flags().StringP("address", "a", "", "address")
	cmd.MarkFlagRequired("address")
	cmd.Flags().Int64P("power", "w", 0, "voting power")
	cmd.MarkFlagRequired("power")
	cmd.Flags().Int64P("height", "t", 0, "update height")
	cmd.MarkFlagRequired("height")
}

func updateNodePower(cmd *cobra.Command, args []string) {
	addr, _ := cmd.Flags().GetString("address")
	power, _ := cmd.Flags().GetInt64("power")
	height, _ := cmd.Flags().GetInt64("height")

	value := &vt.PorsExecAction_PowerUpdate{PowerUpdate: &vt.PorsPowerUpdate{Address: addr, Power: power, Height: height}}
	action := &vt.PorsExecAction{Value: value, Ty: vt.PorsActionPowerUpdate}
	tx := &types.Transaction{
		Payload: types.Encode(action),
		Nonce:   rand.Int63(),
		Execer:  []byte(vt.PorsX),
	}
	tx.To = address.ExecAddress(string(tx.Execer))

	txHex := types.Encode(tx)
	fmt.Println(hex.EncodeToString(txHex))
}

//CreateKeyFileCmd to create keyfiles
func CreateKeyFileCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "gen_file",
		Short: "Generate pors genesis and priv file",
		Run:   createKeyFiles,
	}
	addCreateKeyFileCmdFlags(cmd)
	return cmd
}

func addCreateKeyFileCmdFlags(cmd *cobra.Command) {
	cmd.Flags().StringP("num", "n", "", "num of the keyfile to create")
	cmd.MarkFlagRequired("num")
	cmd.Flags().StringP("type", "t", "ed25519", "sign type of the keyfile (secp256k1, secp256k1eth)")
}

// RandStr ...
func RandStr(length int) string {
	chars := []byte{}
MAIN_LOOP:
	for {
		val := rand.Int63()
		for i := 0; i < 10; i++ {
			v := int(val & 0x3f) // rightmost 6 bits
			if v >= 62 {         // only 62 characters in strChars
				val >>= 6
				continue
			} else {
				chars = append(chars, strChars[v])
				if len(chars) == length {
					break MAIN_LOOP
				}
				val >>= 6
			}
		}
	}

	return string(chars)
}

func initCryptoImpl(signType int) error {
	ttypes.CryptoName = types.GetSignName("", signType)
	fmt.Println("ttypes.CryptoName", ttypes.CryptoName)
	cr, err := crypto.Load(ttypes.CryptoName, -1)
	if err != nil {
		fmt.Printf("init crypto fail: %v", err)
		return err
	}
	ttypes.ConsensusCrypto = cr
	return nil
}

func createKeyFiles(cmd *cobra.Command, args []string) {
	// init crypto instance
	ty, _ := cmd.Flags().GetString("type")
	signType, ok := ttypes.SignMap[ty]
	if !ok {
		fmt.Println("type parameter is not valid")
		return
	}
	err := initCryptoImpl(signType)
	if err != nil {
		return
	}

	// genesis file
	genDoc := ttypes.GenesisDoc{
		ChainID:     fmt.Sprintf("omnilink-%v", RandStr(6)),
		GenesisTime: time.Now(),
	}

	num, _ := cmd.Flags().GetString("num")
	n, err := strconv.Atoi(num)
	if err != nil {
		fmt.Println("num parameter is not valid digit")
		return
	}
	for i := 0; i < n; i++ {
		// create private validator file
		pvFileName := pvFile + strconv.Itoa(i) + ".json"
		privValidator := ttypes.LoadOrGenPrivValidatorFS(pvFileName, signType)
		if privValidator == nil {
			fmt.Println("create priv_validator file fail")
			break
		}

		// create genesis validator by the pubkey of private validator
		gv := ttypes.GenesisValidator{
			PubKey:  ttypes.KeyText{Kind: ttypes.CryptoName, Data: privValidator.GetPubKey().KeyString()},
			Power:   10,
			Address: fmt.Sprintf("0x%s", hex.EncodeToString(privValidator.Address)),
		}

		genDoc.Validators = append(genDoc.Validators, gv)
	}

	if err := genDoc.SaveAs(genFile); err != nil {
		fmt.Println("generate genesis file fail")
		return
	}
	fmt.Printf("generate genesis file path %v\n", genFile)
}
