#!/bin/bash
set -e
podman stop $1-browsertime
#rm /var/run/netns/$1-browsertime
ip netns del $1-browsertime
