#!/bin/bash
ssh root@172.30.135.41 "sed -i 's/UseCambledPLCComm: true/UseCambledPLCComm: false/' /usr/config/BucintoroConfig.yaml"