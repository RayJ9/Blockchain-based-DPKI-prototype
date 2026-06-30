FROM ubuntu:20.04

WORKDIR /root
COPY omnilink omnilink
COPY omnilink-cli omnilink-cli
COPY *.toml ./

CMD /root/omnilink -f /root/omnilink.evm.test.toml