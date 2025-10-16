#!/bin/bash
ssh root@172.30.135.41 "sed -i 's/UseCambledPLCComm: false/UseCambledPLCComm: true/' /usr/config/BucintoroConfig.yaml"