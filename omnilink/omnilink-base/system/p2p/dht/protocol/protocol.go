// Package protocol p2p protocol
package protocol

import (
	"context"
	"time"

	"code.corp.bcollie.net/omnilink/omnilink-base/client"
	dbm "code.corp.bcollie.net/omnilink/omnilink-base/common/db"
	"code.corp.bcollie.net/omnilink/omnilink-base/p2p"
	"code.corp.bcollie.net/omnilink/omnilink-base/queue"
	"code.corp.bcollie.net/omnilink/omnilink-base/system/p2p/dht/extension"
	types2 "code.corp.bcollie.net/omnilink/omnilink-base/system/p2p/dht/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	kbt "github.com/libp2p/go-libp2p-kbucket"
	"github.com/libp2p/go-libp2p/core/discovery"
	"github.com/libp2p/go-libp2p/core/host"
	"github.com/libp2p/go-libp2p/core/metrics"
	"github.com/libp2p/go-libp2p/core/peer"
)

// P2PEnv p2p全局公共变量
type P2PEnv struct {
	Ctx             context.Context
	ChainCfg        *types.OmnilinkConfig
	SubConfig       *types2.P2PSubConfig
	API             client.QueueProtocolAPI
	QueueClient     queue.Client
	Host            host.Host
	P2PManager      *p2p.Manager
	DB              dbm.DB
	PeerInfoManager IPeerInfoManager
	ConnManager     IConnManager
	ConnBlackList   iLRU
	Pubsub          *extension.PubSub
	RoutingTable    *kbt.RoutingTable
	Discovery       discovery.Discovery
}

type iLRU interface {
	Add(s string, t time.Duration)
	Has(s string) bool
	List() *types.Blacklist
}

// IPeerInfoManager is interface of PeerInfoManager
type IPeerInfoManager interface {
	Refresh(info *types.Peer)
	Fetch(pid peer.ID) *types.Peer
	FetchAll() []*types.Peer
	PeerHeight(pid peer.ID) int64
	PeerMaxHeight() int64
}

// IConnManager is interface of ConnManager
type IConnManager interface {
	FetchConnPeers() []peer.ID
	BoundSize() (in int, out int)
	GetNetRate() metrics.Stats
	BandTrackerByProtocol() *types.NetProtocolInfos
	RateCalculate(ratebytes float64) string
}

// QueryModule sends message to other module and waits response
func (p *P2PEnv) QueryModule(topic string, ty int64, data interface{}) (interface{}, error) {
	msg := p.QueueClient.NewMessage(topic, ty, data)
	err := p.QueueClient.Send(msg, true)
	if err != nil {
		return nil, err
	}
	resp, err := p.QueueClient.WaitTimeout(msg, time.Second*10)
	if err != nil {
		return nil, err
	}
	return resp.Data, nil
}
