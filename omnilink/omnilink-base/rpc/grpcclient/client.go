package grpcclient

import (
	"fmt"
	"sync"
	"time"

	"code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"

	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"google.golang.org/grpc"
	"google.golang.org/grpc/keepalive"
)

// paraChainGrpcRecSize 平行链receive最大100M
const paraChainGrpcRecSize = 100 * 1024 * 1024

var mu sync.RWMutex

var defaultClient types.OmnilinkClient

// GetDefaultMainClient get default client
func GetDefaultMainClient() types.OmnilinkClient {
	mu.RLock()
	defer mu.RUnlock()
	return defaultClient
}

//NewMainChainClient 创建一个平行链的 主链 grpc omnilink 客户端
func NewMainChainClient(cfg *types.OmnilinkConfig, grpcaddr string) (types.OmnilinkClient, error) {
	mu.Lock()
	defer mu.Unlock()
	if grpcaddr == "" && defaultClient != nil {
		return defaultClient, nil
	}
	serverAddr := cfg.GetModuleConfig().RPC.ParaChain.MainChainGrpcAddr
	if grpcaddr != "" {
		serverAddr = grpcaddr
	}

	kp := keepalive.ClientParameters{
		Time:                time.Second * 5,
		Timeout:             time.Second * 20,
		PermitWithoutStream: true,
	}

	var conn *grpc.ClientConn
	var err error
	log15.Error("NewMainChainClient start+++++++++++++++++++++++++++++++++")
	if cfg.GetModuleConfig().RPC.ParaChain.UseGrpcLBSync {
		conn, err = grpc.Dial(NewSyncURL(serverAddr), grpc.WithInsecure(),
			grpc.WithDefaultCallOptions(grpc.MaxCallRecvMsgSize(paraChainGrpcRecSize)),
			grpc.WithDefaultServiceConfig(fmt.Sprintf(`{"LoadBalancingPolicy": "%s"}`, SyncLbName)),
			grpc.WithKeepaliveParams(kp))
	} else {
		conn, err = grpc.Dial(NewMultipleURL(serverAddr), grpc.WithInsecure(),
			grpc.WithDefaultCallOptions(grpc.MaxCallRecvMsgSize(paraChainGrpcRecSize)),
			grpc.WithKeepaliveParams(kp))
	}
	if err != nil {
		return nil, err
	}
	grpcClient := types.NewOmnilinkClient(conn)
	if grpcaddr == "" {
		defaultClient = grpcClient
	}
	return grpcClient, nil
}
