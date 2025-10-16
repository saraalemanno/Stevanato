#!/bin/bash
ssh root@10.10.0.25 "sed -i 's/UseCambledPLCComm: false/UseCambledPLCComm: true/' /usr/config/BucintoroConfig.yaml"