// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package pors

import (
	"fmt"

	dbm "code.corp.bcollie.net/omnilink/omnilink-base/common/db"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	tmtypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/pors/types"
	"github.com/golang/protobuf/proto"
)

var (
	stateKey = []byte("stateKey")
)

//ConsensusStore ...
type ConsensusStore struct {
	db dbm.DB
}

// NewConsensusStore returns a new ConsensusStore with the given DB
func NewConsensusStore() *ConsensusStore {
	db := DefaultDBProvider("state")
	db.SetCacheSize(100)
	return &ConsensusStore{
		db: db,
	}
}

// LoadStateFromStore ...
func (cs *ConsensusStore) LoadStateFromStore() *tmtypes.PorsState {
	buf, err := cs.db.Get(stateKey)
	if err != nil {
		porslog.Error("LoadStateFromStore", "err", err)
		return nil
	}
	state := &tmtypes.PorsState{}
	err = types.Decode(buf, state)
	if err != nil {
		panic(err)
	}
	return state
}

// LoadStateHeight ...
func (cs *ConsensusStore) LoadStateHeight() int64 {
	state := cs.LoadStateFromStore()
	if state == nil {
		return int64(0)
	}
	return state.LastBlockHeight
}

// LoadSeenCommit by height
func (cs *ConsensusStore) LoadSeenCommit(height int64) *tmtypes.PorsCommit {
	buf, err := cs.db.Get(calcSeenCommitKey(height))
	if err != nil {
		porslog.Error("LoadSeenCommit", "err", err)
		return nil
	}
	commit := &tmtypes.PorsCommit{}
	err = types.Decode(buf, commit)
	if err != nil {
		panic(err)
	}
	return commit
}

// SaveConsensusState save state and seenCommit
func (cs *ConsensusStore) SaveConsensusState(height int64, state *tmtypes.PorsState, sc proto.Message) error {
	seenCommitBytes := types.Encode(sc)
	stateBytes := types.Encode(state)
	batch := cs.db.NewBatch(true)
	batch.Set(calcSeenCommitKey(height), seenCommitBytes)
	batch.Set(stateKey, stateBytes)
	err := batch.Write()
	if err != nil {
		porslog.Error("SaveConsensusState batch.Write", "err", err)
		return err
	}
	return nil
}

func calcSeenCommitKey(height int64) []byte {
	return []byte(fmt.Sprintf("SC:%v", height))
}
