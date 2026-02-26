#!/bin/bash

IP="$1"

if [ -z "$IP" ]; then
    echo "No IP provided"
    exit 1
fi

# Reset IP configuration
ip addr flush dev eth0

# Assign provided IP
ip addr add ${IP}/24 dev eth0

# Bring interface up
ip link set eth0 up

echo "eth0 configured with IP: ${IP}"
