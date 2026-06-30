package l2txs

import (
	"fmt"
	"strings"

	zksyncTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/zksync/types"
	"github.com/spf13/cobra"
)

func sendDepositTxCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "deposit",
		Short: "send deposit tx to omnilink",
		Run:   sendDeposit,
	}
	sendDepositFlags(cmd)
	return cmd
}

func sendDepositFlags(cmd *cobra.Command) {
	cmd.Flags().Uint64P("tokenId", "t", 0, "eth token id")
	_ = cmd.MarkFlagRequired("tokenId")
	cmd.Flags().Int64P("queueId", "q", 0, "deposit priority queue id")
	_ = cmd.MarkFlagRequired("queueId")
	cmd.Flags().StringP("amount", "m", "0", "deposit amount")
	_ = cmd.MarkFlagRequired("amount")
	cmd.Flags().StringP("ethAddr", "e", "", "from eth addr")
	_ = cmd.MarkFlagRequired("ethAddr")
	cmd.Flags().StringP("omnilinkAddr", "a", "", "to omnilink addr")
	_ = cmd.MarkFlagRequired("omnilinkAddr")

	cmd.Flags().StringP("key", "k", "", "private key")
	_ = cmd.MarkFlagRequired("key")
}

func sendDeposit(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	tokenId, _ := cmd.Flags().GetUint64("tokenId")
	queueId, _ := cmd.Flags().GetInt64("queueId")
	amount, _ := cmd.Flags().GetString("amount")
	ethAddress, _ := cmd.Flags().GetString("ethAddr")
	omnilinkAddr, _ := cmd.Flags().GetString("omnilinkAddr")
	privateKey, _ := cmd.Flags().GetString("key")
	paraName, _ := cmd.Flags().GetString("paraName")

	deposit := &zksyncTypes.ZkDeposit{
		TokenId:      tokenId,
		Amount:       amount,
		EthAddress:   ethAddress,
		OmnilinkAddr: omnilinkAddr,
		L1PriorityId: queueId,
	}

	action := &zksyncTypes.ZksyncAction{
		Ty: zksyncTypes.TyDepositAction,
		Value: &zksyncTypes.ZksyncAction_Deposit{
			Deposit: deposit,
		},
	}

	tx, err := createOmnilinkTx(privateKey, getRealExecName(paraName, zksyncTypes.Zksync), action)
	if nil != err {
		fmt.Println("sendDeposit failed to createOmnilinkTx due to err:", err.Error())
		return
	}
	sendTx(rpcLaddr, tx)
}

func batchSendDepositTxCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "batchdeposit",
		Short: "send deposit tx to omnilink batch",
		Run:   batchSendDeposit,
	}
	batchSendDepositFlags(cmd)
	return cmd
}

func batchSendDepositFlags(cmd *cobra.Command) {
	cmd.Flags().Uint64P("tokenId", "t", 0, "eth token id")
	_ = cmd.MarkFlagRequired("tokenId")
	cmd.Flags().Uint64P("count", "c", 1, "count of txs to send in batch")
	_ = cmd.MarkFlagRequired("count")
	cmd.Flags().Int64P("queueId", "q", 0, "deposit queue id")
	_ = cmd.MarkFlagRequired("queueId")
	cmd.Flags().StringP("amount", "m", "0", "deposit amount")
	_ = cmd.MarkFlagRequired("amount")
	cmd.Flags().StringP("ethAddr", "e", "", "from eth addr")
	_ = cmd.MarkFlagRequired("ethAddr")
	cmd.Flags().StringP("omnilinkAddr", "a", "", "to omnilink addr")
	_ = cmd.MarkFlagRequired("omnilinkAddr")

	cmd.Flags().StringP("key", "k", "", "private key")
	_ = cmd.MarkFlagRequired("key")
}

func batchSendDeposit(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	tokenId, _ := cmd.Flags().GetUint64("tokenId")
	count, _ := cmd.Flags().GetUint64("count")
	queueId, _ := cmd.Flags().GetInt64("queueId")
	amount, _ := cmd.Flags().GetString("amount")
	ethAddress, _ := cmd.Flags().GetString("ethAddr")
	omnilinkAddr, _ := cmd.Flags().GetString("omnilinkAddr")
	privateKey, _ := cmd.Flags().GetString("key")
	paraName, _ := cmd.Flags().GetString("paraName")

	deposit := &zksyncTypes.ZkDeposit{
		TokenId:      tokenId,
		Amount:       amount,
		EthAddress:   ethAddress,
		OmnilinkAddr: omnilinkAddr,
		L1PriorityId: queueId,
	}

	action := &zksyncTypes.ZksyncAction{
		Ty: zksyncTypes.TyDepositAction,
		Value: &zksyncTypes.ZksyncAction_Deposit{
			Deposit: deposit,
		},
	}

	for i := uint64(0); i < count; i++ {
		tx, err := createOmnilinkTx(privateKey, getRealExecName(paraName, zksyncTypes.Zksync), action)
		if nil != err {
			fmt.Println("sendDeposit failed to createOmnilinkTx due to err:", err.Error())
			return
		}
		sendTx(rpcLaddr, tx)
	}
}

func sendManyDepositTxCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "deposit_many",
		Short: "send many deposit tx to omnilink",
		Run:   sendManyDeposit,
	}
	sendManyDepositFlags(cmd)
	return cmd
}

func sendManyDepositFlags(cmd *cobra.Command) {
	cmd.Flags().Uint64P("tokenId", "t", 0, "eth token id")
	_ = cmd.MarkFlagRequired("tokenId")
	cmd.Flags().Int64P("queueId", "q", 0, "deposit queue id")
	_ = cmd.MarkFlagRequired("queueId")
	cmd.Flags().StringP("amount", "m", "0", "deposit amount")
	_ = cmd.MarkFlagRequired("amount")
	cmd.Flags().StringP("ethAddr", "e", "", "from eth addr")
	_ = cmd.MarkFlagRequired("ethAddr")
	cmd.Flags().StringP("omnilinkAddrs", "a", "", "to omnilink addrs, use ',' separate")
	_ = cmd.MarkFlagRequired("omnilinkAddrs")
	cmd.Flags().StringP("key", "k", "", "private key")
	_ = cmd.MarkFlagRequired("key")
}

func sendManyDeposit(cmd *cobra.Command, args []string) {
	rpcLaddr, _ := cmd.Flags().GetString("rpc_laddr")
	tokenId, _ := cmd.Flags().GetUint64("tokenId")
	queueId, _ := cmd.Flags().GetInt64("queueId")
	amount, _ := cmd.Flags().GetString("amount")
	ethAddress, _ := cmd.Flags().GetString("ethAddr")
	omnilinkAddrs, _ := cmd.Flags().GetString("omnilinkAddrs")
	privateKey, _ := cmd.Flags().GetString("key")
	paraName, _ := cmd.Flags().GetString("paraName")

	toOmnilinkAddrs := strings.Split(omnilinkAddrs, ",")

	for i := 0; i < len(toOmnilinkAddrs); i++ {
		deposit := &zksyncTypes.ZkDeposit{
			TokenId:      tokenId,
			Amount:       amount,
			EthAddress:   ethAddress,
			OmnilinkAddr: toOmnilinkAddrs[i],
			L1PriorityId: queueId,
		}
		queueId++

		action := &zksyncTypes.ZksyncAction{
			Ty: zksyncTypes.TyDepositAction,
			Value: &zksyncTypes.ZksyncAction_Deposit{
				Deposit: deposit,
			},
		}

		tx, err := createOmnilinkTx(privateKey, getRealExecName(paraName, zksyncTypes.Zksync), action)
		if nil != err {
			fmt.Println("sendDeposit failed to createOmnilinkTx due to err:", err.Error())
			return
		}
		sendTx(rpcLaddr, tx)
	}
}
