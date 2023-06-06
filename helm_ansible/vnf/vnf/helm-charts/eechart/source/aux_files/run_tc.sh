#!/bin/bash

# Get current timestamp in the desired format

timestamp=$(python3 -c 'import datetime; print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))')
echo $timestamp
sudo tc qdisc add dev wg0 root handle 1: prio
sudo tc filter add dev wg0 parent 1: protocol ip u32 match ip dst 10.10.3.0/24 match u32 0 0 flowid 1:1
sudo tc qdisc add dev wg0 parent 1:1 netem delay 100ms
sleep 20
sudo tc qdisc del dev wg0 root
