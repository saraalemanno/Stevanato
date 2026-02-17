#!/bin/bash

# Reset IP configuration
ip addr flush dev eth0

# Assign Novo Nordisk IP
ip addr add 172.30.135.40/24 dev eth0

# Bring interface up
ip link set eth0 up

echo "eth0 configured for Novo Nordisk environment."
