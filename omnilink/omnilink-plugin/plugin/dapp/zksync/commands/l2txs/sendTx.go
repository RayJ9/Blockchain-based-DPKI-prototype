package l2txs

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/common"
	"code.corp.bcollie.net/omnilink/omnilink-base/rpc/jsonclient"
	rpctypes "code.corp.bcollie.net/omnilink/omnilink-base/rpc/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"github.com/spf13/cobra"
)

func SendOmnilinkL2TxCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "sendl2",
		Short: "send l2 tx to omnilink ",
		Args:  cobra.MinimumNArgs(1),
	}

	cmd.AddCommand(
		sendDepositTxCmd(),
		batchSendDepositTxCmd(),
		sendWithdrawTxCmd(),
		BatchSendTransferTxCmd(),
		SendTransferTxCmd(),
		sendManyDepositTxCmd(),
		sendManyWithdrawTxCmd(),
		treeManyToContractCmd(),
		contractManyToTreeCmd(),
		SendManyTransferTxCmd(),
		SendManyTransferTxFromOneCmd(),
		transferManyToNewCmd(),
		transferToNewManyCmd(),
		proxyManyExitCmd(),
		nftManyCmd(),
		setManyPubKeyCmd(),
		fetchL2BlockCmd(),
	)

	return cmd
}

func sendTx(rpcLaddr string, tx *types.Transaction) {
	txData := types.Encode(tx)
	dataStr := common.ToHex(txData)

	//fmt.Println("sendTx", "dataStr", dataStr)
	params := rpctypes.RawParm{
		Token: "BTY",
		Data:  dataStr,
	}

	ctx := jsonclient.NewRPCCtx(rpcLaddr, "Omnilink.SendTransaction", params, nil)
	ctx.RunWithoutMarshal()
}
