#!/bin/bash
set -e
ip netns add $1-browsertime
ip netns exec $1-browsertime ip link set dev lo up
podman run --shm-size=4g --rm -dit --network=ns:/var/run/netns/$1-browsertime --dns=10.0.1.4 --entrypoint "/bin/bash" -v "/tmp/browsertime-$1":/browsertime --cap-add=SYS_NICE --cap-add=CAP_NET_RAW --name $1-browsertime localhost/constantin/browsertime:latest
#DPID=$(podman inspect -f '{{.State.Pid}}' $1-browsertime)
#mkdir -p /var/run/netns
#ln -s /proc/$DPID/ns/net /var/run/netns/$1-browsertime
