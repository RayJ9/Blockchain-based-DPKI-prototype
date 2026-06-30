// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package executor_test

import (
	"testing"

	"code.corp.bcollie.net/omnilink/omnilink-base/executor"
	"code.corp.bcollie.net/omnilink/omnilink-base/util/testnode"
	"github.com/stretchr/testify/require"

	"strings"

	dbm "code.corp.bcollie.net/omnilink/omnilink-base/common/db"
	"code.corp.bcollie.net/omnilink/omnilink-base/queue"
	"code.corp.bcollie.net/omnilink/omnilink-base/store"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"github.com/stretchr/testify/assert"
)

func newStateDbForTest(height int64, cfg *types.OmnilinkConfig) dbm.KV {
	q := queue.New("channel")
	q.SetConfig(cfg)
	return executor.NewStateDB(q.Client(), nil, nil, &executor.StateDBOption{Height: height})
}
func TestStateDBGet(t *testing.T) {
	cfg := types.NewOmnilinkConfig(types.GetDefaultCfgstring())
	db := newStateDbForTest(0, cfg)
	testStateDBGet(t, db)
}

func testStateDBGet(t *testing.T, db dbm.KV) {
	err := db.Set([]byte("k1"), []byte("v1"))
	assert.Nil(t, err)
	v, err := db.Get([]byte("k1"))
	assert.Nil(t, err)
	assert.Equal(t, v, []byte("v1"))

	err = db.Set([]byte("k1"), []byte("v11"))
	assert.Nil(t, err)
	v, err = db.Get([]byte("k1"))
	assert.Nil(t, err)
	assert.Equal(t, v, []byte("v11"))

	stateDb := db.(*executor.StateDB)
	vs, err := stateDb.BatchGet([][]byte{[]byte("k1")})
	assert.NoError(t, err)
	assert.Equal(t, [][]byte{[]byte("v11")}, vs)
}

func TestStateDBTxGetOld(t *testing.T) {
	str := types.GetDefaultCfgstring()
	new := strings.Replace(str, "Title=\"local\"", "Title=\"omnilink\"", 1)
	cfg := types.NewOmnilinkConfig(new)

	q := queue.New("channel")
	q.SetConfig(cfg)
	// store
	s := store.New(cfg)
	s.SetQueueClient(q.Client())
	// exec
	db := executor.NewStateDB(q.Client(), nil, nil, &executor.StateDBOption{Height: cfg.GetFork("ForkExecRollback") - 1})
	defer func() {
		s.Close()
		q.Close()
	}()

	db.Begin()
	err := db.Set([]byte("k1"), []byte("v1"))
	assert.Nil(t, err)
	v, err := db.Get([]byte("k1"))
	assert.Nil(t, err)
	assert.Equal(t, v, []byte("v1"))

	db.Rollback()
	v, err = db.Get([]byte("k1"))
	assert.Equal(t, err, types.ErrNotFound)
	assert.Equal(t, v, []byte(nil))

	db.Begin()
	err = db.Set([]byte("k1"), []byte("v1"))
	assert.Nil(t, err)
	v, err = db.Get([]byte("k1"))
	assert.Nil(t, err)
	assert.Equal(t, v, []byte("v1"))

	db.Commit()
	v, err = db.Get([]byte("k1"))
	assert.Nil(t, err)
	assert.Equal(t, v, []byte("v1"))

	err = db.Set([]byte("k1"), []byte("v11"))
	assert.Nil(t, err)

	db.Begin()
	v, err = db.Get([]byte("k1"))
	assert.Nil(t, err)
	//fork 之前有bug，这里读到了脏数据
	assert.Equal(t, v, []byte("v1"))

	db.Begin()
	db.Rollback()
	db.Commit()
}

func testStateDBTxGet(t *testing.T, db dbm.KV) {
	//新版本
	db.Begin()
	err := db.Set([]byte("k1"), []byte("v1"))
	assert.Nil(t, err)
	v, err := db.Get([]byte("k1"))
	assert.Nil(t, err)
	assert.Equal(t, v, []byte("v1"))

	db.Commit()
	v, err = db.Get([]byte("k1"))
	assert.Nil(t, err)
	assert.Equal(t, v, []byte("v1"))

	//在非transaction中set，直接set成功，不能rollback
	err = db.Set([]byte("k1"), []byte("v11"))
	assert.Nil(t, err)

	db.Begin()
	v, err = db.Get([]byte("k1"))
	assert.Nil(t, err)
	assert.Equal(t, v, []byte("v11"))

	err = db.Set([]byte("k1"), []byte("v12"))
	assert.Nil(t, err)
	v, err = db.Get([]byte("k1"))
	assert.Nil(t, err)
	assert.Equal(t, v, []byte("v12"))

	db.Rollback()
	v, err = db.Get([]byte("k1"))
	assert.Nil(t, err)
	assert.Equal(t, v, []byte("v11"))
}

func TestStateDBTxGet(t *testing.T) {
	cfg := types.NewOmnilinkConfig(types.GetDefaultCfgstring())
	db := newStateDbForTest(cfg.GetFork("ForkExecRollback"), cfg)
	testStateDBTxGet(t, db)
}

func TestStateDBCache(t *testing.T) {

	mock33 := testnode.New("", nil)
	defer mock33.Close()
	db := executor.NewStateDB(mock33.GetClient(), nil, nil, nil)
	db.Begin()
	err := db.Set([]byte("key1"), []byte("value1"))
	require.Nil(t, err)
	db.Commit()
	db.Begin()
	val, err := db.Get([]byte("key1"))
	require.Nil(t, err)
	require.Equal(t, []byte("value1"), val)
	db.Set([]byte("key1"), nil)
	db.Commit()

	_, err = db.Get([]byte("key1"))
	require.Equal(t, types.ErrNotFound, err)
}
