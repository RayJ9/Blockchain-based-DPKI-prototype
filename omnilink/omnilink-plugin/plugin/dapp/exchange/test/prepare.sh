#!/usr/bin/env bash

BUILD=$(cd "$(dirname "$0")" && cd ../../../../build && pwd)
echo "$BUILD"

cd "$BUILD" || return

seed=$(./omnilink-cli seed generate -l 0)
echo "$seed"

./omnilink-cli seed save -p bty123456 -s "$seed"
sleep 1
./omnilink-cli wallet unlock -p bty123456
sleep 1
./omnilink-cli account list

## account
#genesis -- 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs
./omnilink-cli account import_key -k 3990969DF92A5914F7B71EEB9A4E58D6E255F32BF042FEA5318FC8B3D50EE6E8 -l genesis

#A -- 1KSBd17H7ZK8iT37aJztFB22XGwsPTdwE4
./omnilink-cli account import_key -k 0x6da92a632ab7deb67d38c0f6560bcfed28167998f6496db64c258d5e8393a81b -l A

#B -- 1JRNjdEqp4LJ5fqycUBm9ayCKSeeskgMKR
./omnilink-cli account import_key -k 0x19c069234f9d3e61135fefbeb7791b149cdf6af536f26bebb310d4cd22c3fee4 -l B

#C -- 1NLHPEcbTWWxxU3dGUZBhayjrCHD3psX7k
./omnilink-cli account import_key -k 0x7a80a1f75d7360c6123c32a78ecf978c1ac55636f87892df38d8b85a9aeff115 -l C

#D -- 1MCftFynyvG2F4ED5mdHYgziDxx6vDrScs
./omnilink-cli account import_key -k 0xcacb1f5d51700aea07fca2246ab43b0917d70405c65edea9b5063d72eb5c6b71 -l D

#Fee -- 1PTGVR7TUm1MJUH7M1UNcKBGMvfJ7nCrnN
./omnilink-cli account import_key -k 0xa691ceceadb1f6878c39702a057b09077971d2995b29f18ccba1e09cd9619b7f -l Fee

## config token
./omnilink-cli send config config_tx -c token-finisher -o add -v 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs -k 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs
sleep 1
./omnilink-cli config query -k token-finisher

./omnilink-cli send config config_tx -c token-blacklist -o add -v BTY -k 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs
sleep 1
./omnilink-cli config query -k token-blacklist

## 10亿
./omnilink-cli send token precreate -f 0.001 -i "test ccny" -n "ccny" -a 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs -p 0 -s CCNY -t 1000000000 -k 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs
sleep 1
./omnilink-cli token precreated
./omnilink-cli send token finish -s CCNY -f 0.001 -a 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs -k 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs
sleep 1
./omnilink-cli token created
./omnilink-cli token balance -a 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs -s CCNY -e token

## transfer bty
./omnilink-cli send coins transfer -a 10000 -t 1KSBd17H7ZK8iT37aJztFB22XGwsPTdwE4 -k 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs
./omnilink-cli send coins transfer -a 10000 -t 1JRNjdEqp4LJ5fqycUBm9ayCKSeeskgMKR -k 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs
./omnilink-cli send coins transfer -a 10000 -t 1NLHPEcbTWWxxU3dGUZBhayjrCHD3psX7k -k 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs
./omnilink-cli send coins transfer -a 10000 -t 1MCftFynyvG2F4ED5mdHYgziDxx6vDrScs -k 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs
./omnilink-cli account list

## send bty to execer， 每人10000 bty
./omnilink-cli send coins send_exec -e exchange -a 10000 -k 1KSBd17H7ZK8iT37aJztFB22XGwsPTdwE4
./omnilink-cli send coins send_exec -e exchange -a 10000 -k 1JRNjdEqp4LJ5fqycUBm9ayCKSeeskgMKR
./omnilink-cli send coins send_exec -e exchange -a 10000 -k 1NLHPEcbTWWxxU3dGUZBhayjrCHD3psX7k
./omnilink-cli send coins send_exec -e exchange -a 10000 -k 1MCftFynyvG2F4ED5mdHYgziDxx6vDrScs
echo "account balance in execer"
./omnilink-cli account balance -e exchange -a 1KSBd17H7ZK8iT37aJztFB22XGwsPTdwE4
./omnilink-cli account balance -e exchange -a 1JRNjdEqp4LJ5fqycUBm9ayCKSeeskgMKR
./omnilink-cli account balance -e exchange -a 1NLHPEcbTWWxxU3dGUZBhayjrCHD3psX7k
./omnilink-cli account balance -e exchange -a 1MCftFynyvG2F4ED5mdHYgziDxx6vDrScs

##transfer token，每人2亿 ccny
./omnilink-cli send token transfer -a 200000000 -s CCNY -t 1KSBd17H7ZK8iT37aJztFB22XGwsPTdwE4 -k 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs
./omnilink-cli send token transfer -a 200000000 -s CCNY -t 1JRNjdEqp4LJ5fqycUBm9ayCKSeeskgMKR -k 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs
./omnilink-cli send token transfer -a 200000000 -s CCNY -t 1NLHPEcbTWWxxU3dGUZBhayjrCHD3psX7k -k 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs
./omnilink-cli send token transfer -a 200000000 -s CCNY -t 1MCftFynyvG2F4ED5mdHYgziDxx6vDrScs -k 1CbEVT9RnM5oZhWMj4fxUrJX94VtRotzvs

## send token to excer
./omnilink-cli send token send_exec -a 200000000 -e exchange -s CCNY -k 1KSBd17H7ZK8iT37aJztFB22XGwsPTdwE4
./omnilink-cli send token send_exec -a 200000000 -e exchange -s CCNY -k 1JRNjdEqp4LJ5fqycUBm9ayCKSeeskgMKR
./omnilink-cli send token send_exec -a 200000000 -e exchange -s CCNY -k 1NLHPEcbTWWxxU3dGUZBhayjrCHD3psX7k
./omnilink-cli send token send_exec -a 200000000 -e exchange -s CCNY -k 1MCftFynyvG2F4ED5mdHYgziDxx6vDrScs
echo "token balance in execer"
./omnilink-cli token balance -e exchange -s CCNY -a "1KSBd17H7ZK8iT37aJztFB22XGwsPTdwE4 1JRNjdEqp4LJ5fqycUBm9ayCKSeeskgMKR 1NLHPEcbTWWxxU3dGUZBhayjrCHD3psX7k 1MCftFynyvG2F4ED5mdHYgziDxx6vDrScs"
