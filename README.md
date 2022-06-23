# Omni-Python-Examples

This project contains sample code for streaming data from the OpenMind Server. 

## Overview

The OpenMind Server provides a gRPC interface for interacting with the Medtronic API. This allows for custom applications to be built on any operating system using any of the [gRPC supported programming languages](https://grpc.io/docs/languages/). These examples show how to stream time domain data from the Summit RC+S using Python. 

The order of operations is as follows: 

1. Connect to the OpenMind Server
2. Find and connect to a bridge 
3. Find and connect to a device 
4. Configure sensing on the Summit RC+S
5. Stream time domain data from the Summit RC+S 

## Installation 

This demo requires a Summit RC+S, a CTM, and the [OpenMind Server](https://github.com/openmind-consortium/OmniSummitDeviceService). 

These examples use Python3, so make sure it is installed. Run `pip install grpcio` to install the gRPC tools and then build the protobuf files found in the submodule [`OmniProtos`](https://github.com/openmind-consortium/OmniProtos/tree/c8c2ad547a8bd7b890eb2ed20532e48beccb507e). 

After the protos are built, the protos directory needs to be added to the [PYTHONPATH environment variable](https://www.simplilearn.com/tutorials/python-tutorial/python-path#setting_the_python_environment_variable_pythonpath_on_windows). 

## Running

To run this demo, turn on the CTM and place it on the Summit RC+S for pairing. Next, start the OpenMind Server by building and running the Visual Studio solution. If your OpenMind Server is running on localhost, then you can run `python client.py` as is. Otherwise, you can change the default IP address by running `python client.py --ip <ip-address>`. Once the client code is connected to the device, time domain packets of data should start printing in the terminal. 

## Future Work

Enabling stimulation coming soon... 
