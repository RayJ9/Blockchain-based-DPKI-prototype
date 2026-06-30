FROM ubuntu:18.04

WORKDIR /root
COPY omnilink omnilink
COPY omnilink-cli omnilink-cli
COPY entrypoint.sh entrypoint.sh
COPY omnilink.toml omnilink*.toml ./


CMD ["/root/omnilink", "-f", "/root/omnilink.toml"]
