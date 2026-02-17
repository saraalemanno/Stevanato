#!/bin/bash
ssh root@10.10.0.25 "sed -i 's/UseCambledPLCComm: true/UseCambledPLCComm: false/' /usr/config/BucintoroConfig.yaml"