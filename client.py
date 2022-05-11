from __future__ import print_function

import random
import logging

import time
import grpc

from protos import summit_pb2

from protos import device_pb2
from protos import device_pb2_grpc

from protos import bridge_pb2
from protos import bridge_pb2_grpc


import numpy as np

ip_addr = '10.39.77.9' # ip address the Summit Server is running on (ipconfig wifi ipv4 from Windows)

# Looks for any bridges connected to the host machine
# The Bridge ID must (partially) match partial_uri
def find_bridges(bridge_stub):

    # If you have the exact bridge ID you're looking for
    # you can store it in bridge_id
    bridge_id = 'NKW028769N'
    partial_uri = '//summit/bridge/' + bridge_id

    # Create a request to search for all connected bridges
    # who's ID matches partial_uri
    print('Looking for bridges')
    query_request = bridge_pb2.QueryBridgesRequest(query=partial_uri)

    # Receive a response from the server. This contains the list of
    # bridges that were found
    response = bridge_stub.ListBridges(query_request)

    # Iterate through the list of bridges
    for b in response.bridges:
        print('Found bridge:', b.name)

    # Return the bridges as a list
    return response.bridges

# Connect to a given bridge
def connect_to_bridge(bridge_stub, bridge):

    # Create a request to connect to the specified bridge
    print('Attempting to connect to bridge:', bridge.name)
    connect_request = bridge_pb2.ConnectBridgeRequest(name=bridge.name)

    # Receive a response from the server containing connection information
    response = bridge_stub.ConnectBridge(connect_request)

    # Check the connection status
    # why does this go through summit not? it doesn't make sense to me
    connection_status = response.connection_status
    print('Connection Status:', summit_pb2.SummitConnectBridgeStatus.Name(connection_status))

    # Return the connection status
    return connection_status

# Search for devices connected to a given bridge
def find_devices(bridge_stub, bridge):

    # Create a request to search for all connected devices
    # who's ID matches partial_uri
    print('Looking for devices')
    query_request = device_pb2.ListDeviceRequest(query=bridge.name)

    # Receive a response from the server. This contains the list of
    # devices that were found
    response = bridge_stub.ListDevices(query_request)

    # Iterate through the list of bridges
    for d in response.devices:
        print('Found device:', d.name)

    # Return the bridges as a list
    return response.devices

# Connect to a device
def connect_to_device(device_stub, device):

    # Create a request to connect to the specified device
    print('Attempting to connect to device:', device.name)
    connect_request = device_pb2.ConnectDeviceRequest(name=device.name)

    # Receive a response from the server containing connection information
    response = device_stub.ConnectDevice(connect_request)

    # Check the connection status
    connection_status = response.connection_status
    print('Connection Status Raw Value:', connection_status)

    # Return the connection status
    return connection_status

# Print the data being received from the Summit to the terminal
def print_data(time_domain_update):

    # time_domain_update and time_domain_update.data are both
    # streams that will generate data until the program is stopped  
    for update in time_domain_update:
        for data in update.data:

            channel_id = data.channel_id
            print(data.channel_data[0])

def create_sense_enables_config():

    print('Creating Sense Enables Config')

    sense_enables_config = summit_pb2.SummitSenseEnablesConfiguration(
        fft_stream_channel=summit_pb2.FFTStreamChannel.Value('CH0'),
        enable_timedomain=True,
        enable_fft=True,
        enable_power=True,
        enable_ld0=False,
        enable_ld1=False,
        enable_adaptive_stim=False,
        enable_loop_recording=False)

    return sense_enables_config

def create_time_domain_config():

    print('Creating Time Domain Config')

    minus = summit_pb2.TimeDomainMuxInputs.Value('MUX_0')
    plus = summit_pb2.TimeDomainMuxInputs.Value('MUX_2')
    low_pass_filter_stage1 = summit_pb2.TimeDomainLowPassFilterStage1.Value('LPF_100_HZ')
    low_pass_filter_stage2 = summit_pb2.TimeDomainLowPassFilterStage2.Value('LPF_100_Hz')
    high_pass_filters = summit_pb2.TimeDomainHighPassFilters.Value('HPF_0_85HZ')

    td_channel_config = summit_pb2.SummitTimeDomainChannelConfig(
        minus=minus,
        plus=plus,
        low_pass_filter_stage1=low_pass_filter_stage1,
        low_pass_filter_stage2=low_pass_filter_stage2,
        high_pass_filters=high_pass_filters,
        disabled=False
    )

    return td_channel_config

def create_fft_config():

    print('Creating FFT Config')

    size = summit_pb2.FastFourierTransformSizes.Value('SIZE_0064')
    interval = 50
    window_load = summit_pb2.FastFourierTransformWindowAutoLoads.Value('HANN_50_PERCENT')
    enable_window = False
    band_formation_config = summit_pb2.FastFourierTransformWeightMultiplies.Value('SHIFT_0')
    bins_to_stream = 0
    bins_to_stream_offset = 0

    fft_config = summit_pb2.SummitFastFourierTransformStreamConfiguration(
            size=size,
            interval=interval,
            window_load=window_load,
            enable_window=enable_window,
            band_formation_config=band_formation_config,
            bins_to_stream=bins_to_stream,
            bins_to_stream_offset=bins_to_stream_offset)

    return fft_config

def create_power_channel_config():

    print('Creating Power Channel Config')

    power_band_enables = True
    power_band_configuration = summit_pb2.PowerBandConfiguration(band_start=1, band_stop=2)

    power_channel_config = summit_pb2.SummitPowerStreamConfiguration(
            power_band_enables=(power_band_enables,)*8,
            power_band_configuration=(power_band_configuration,)*8)

    return power_channel_config

def create_misc_stream_config():

    print('Creating Misc Stream Config')

    bridging = summit_pb2.BridgingConfiguration.Value('BRIDGE_NONE')
    streaming_rate = summit_pb2.StreamingFrameRate.Value('FRAME_30_MS')
    loop_record_triggers = summit_pb2.LoopRecordingTriggers.Value('STATE_0')
    loop_recording_post_buffer_time = 30

    misc_stream_config = summit_pb2.MiscellaneousStreamConfiguration(
            bridging=bridging,
            streaming_rate=streaming_rate,
            loop_record_triggers=loop_record_triggers,
            loop_recording_post_buffer_time=loop_recording_post_buffer_time)

    return misc_stream_config

def create_accelerometer_config():

    print('Creating Accelerometer Config')

    sample_rate = summit_pb2.AccelerometerSampleRate.Value('SAMPLE_64')

    accelerometer_config = summit_pb2.SummitAccelerometerStreamConfiguration(
            sample_rate=sample_rate)

    return accelerometer_config

# Configure sensing
def configure_sensing(device_stub, device):

    print('Attempting to configure sensing from device:', device.name)

    timedomain_sampling_rate = 2 # 0 = 250 Hz, 1 = 500 Hz, 2 = 1000 Hz, 240 = DISABLE
    sense_enables_config = create_sense_enables_config()
    td_channel_config = create_time_domain_config()
    fft_config = create_fft_config()
    power_channel_config = create_power_channel_config()
    misc_stream_config = create_misc_stream_config()
    accelerometer_config = create_accelerometer_config()

    # Note: We need to send a config for every bit of sensing, even if it's not turned on
    sense_configure_request = device_pb2.SenseConfigurationRequest(
        name=device.name,
        timedomain_sampling_rate=timedomain_sampling_rate,
        td_channel_configs=(td_channel_config,)*4,
        fft_config=fft_config,
        power_channel_config=power_channel_config,
        misc_stream_config=misc_stream_config,
        accelerometer_config=accelerometer_config,
        sense_enables_config=sense_enables_config)

    # Send the request for sensing configuration
    sense_configure_response = device_stub.SenseConfiguration(sense_configure_request)

    # Confirm that sensing is enabled
    summit_error = sense_configure_response.error
    print('SUMMIT MESSAGE:', summit_error.message)

# TODO: Make this more generic. Add the stream type as an argument. 
# Stream time series data from a device
def stream_power_data(device_stub, bridge, device):

    print('Attempting to stream data from device:', device.name)

    # Configuring sensing
    # Sets streaming parameters for each type of stream 
    configure_sensing(device_stub, device)

    # Create a request to stream from the INS to the gRPC server
    summit_params = summit_pb2.SummitStreamEnablesConfiguration(enable_timedomain=True, enable_fft=True, enable_power=True)
    stream_configure_request = device_pb2.StreamConfigureRequest(name=device.name, parameters=summit_params)

    # Start the stream
    stream_configure_response = device_stub.StreamEnable(stream_configure_request)

    # Confirm that the stream is started
    stream_configure_status = stream_configure_response.stream_configure_status
    print('Stream Configured Status:', device_pb2.StreamConfigureStatus.Name(stream_configure_status))

    # Create a request to stream from the gRPC server to our application
    stream_enable_request = device_pb2.SetDataStreamEnable(name=bridge.name, enable_stream=1)

    # Stream time domain data
    time_domain_update = device_stub.TimeDomainStream(stream_enable_request)
    print('Time Domain Update')
    print(time_domain_update)

    # Print the data being recieved
    print_data(time_domain_update)

    band_power_update = device_stub.BandPowerStream(stream_enable_request)
    print("Code:", band_power_update.code())
    print("Details:", band_power_update.details())
    print('Band Power Update')
    for u in band_power_update: 
        print('We have something')
    print("What") 
    print("Code:", band_power_update.code())
    print("Details:", band_power_update.details())

    # # return a stream of band power data packets 
    # # time_domain_update and time_domain_update.data are both
    # # streams that will generate data until the program is stopped  
    # for update in band_power_update:
    #     print('Received update')
    #     for data in update.data:
    #         print('Data:', data)
    #         yield data.channel_data[0]

    print('Generating random data')

    # dummy: generate 100 random floats between 0 and 5
    return 5* np.random.random_sample((100,)) 

# TODO: Learn how to get time stamp for each data packet 
# TODO: Change window from sample based to time based
# calculate the average beta power over a time window 
def beta_power_threshold(device_stub, device, band_power_stream):
    
    # calculate a new average every 10 samples 
    window = 10 

    # array to store our beta powers before they are averaged 
    beta_power = []

    # calculate state table value 
    # based on beta power 
    for power in band_power_stream: 

        if len(beta_power) > window:

            # calculate the average power
            avg_power = np.mean(beta_power)

            # calculate our step in stim amplitude 
            step = calculate_stim(avg_power)

            # send out stim 
            stim_change_step_amp(device_stub, device, step)
            
            # reset our number of samples and array 
            beta_power = []

        # add this sample to our array of samples (to be averaged later)
        beta_power.append(power)
        
# TODO: Figure out state table 
# calculate the step in stim amplitude 
# based on the average power 
def calculate_stim(power): 

    print("Calculating change in amplitude")

    power_threshold = 10

    if power > power_threshold: 
        step = -0.1
    elif power < power_threshold: 
        step = 0.1
    else:
        step = 0

    return step

# Change the amplitude of stimulation by a step 
def stim_change_step_amp(device_stub, device, step): 

    print("Sending stim command")

    # the program number 
    program = '0b0000 0001'

    # send the stimulation command 
    stim_change_amp_request = device_pb2.StimChangeStepAmpRequest(name=device.name, program_number=program.encode(), amp_delta_milliamps=step)
    stim_change_amp_response = device_stub.StreamEnable(stim_change_amp_request)
    
    # confirm that stim was sent properly 
    if not stim_change_amp_response.error: 
        print("NEW STIM AMPLITUDE: %d" % stim_change_amp_response.new_stim_amplitude)
    else: 
        print("ERROR:\n")
        print(stim_change_amp_response.error)
    
def run():
    with grpc.insecure_channel(ip_addr+':50051') as channel:

        # Initialize stubs
        bridge_stub = bridge_pb2_grpc.BridgeManagerServiceStub(channel)
        device_stub = device_pb2_grpc.DeviceManagerServiceStub(channel)

        # Look for bridges
        bridges = find_bridges(bridge_stub)

        # Look through each bridge that was found
        for bridge in bridges:
            # Attempt to connect the each bridge
            bridge_connection_status = connect_to_bridge(bridge_stub, bridge)

            # If the bridge connected
            if bridge_connection_status == 1:
                # Search for devices on that bridge
                devices = find_devices(device_stub, bridge)

                # Look through each device that was found
                for device in devices:
                    # Attempt to connect to each device
                    device_connection_status = connect_to_device(device_stub,device)

                    # If the device connected
                    if device_connection_status == 1 or device_connection_status>4:
                        # Stream data from that device
                        band_power_stream = stream_power_data(device_stub, bridge, device)
                        # Run the burst algorithm on that data stream 
                        beta_power_threshold(device_stub, device, band_power_stream)

if __name__ == '__main__':
    logging.basicConfig()
    run()