import matplotlib.pyplot as plt
import matplotlib.animation as ani

# Note: You may not have permissions to acquire the semaphore
# sudo won't help you. You need to chmod 777 /dev/shm/*
band_power_shm_name='summit_band_power_shm' 
band_power_sem_name='/summit_band_power_sem' 
stim_shm_name='summit_stim_shm' 
stim_sem_name='/summit_stim_sem'

band_power_sem = posix_ipc.Semaphore(band_power_sem_name)
stim_sem = posix_ipc.Semaphore(stim_sem_name)

stim_data_x = np.array([])
stim_data_y = np.array([])
band_power_data_x = np.array([])
band_power_data_y = np.array([])

def read_stim(): 

    # ***** start protected mutex session *****
    acquire_time = time.time()
    stim_sem.acquire(timeout=0)
    print('Stim Semaphore Acquired:', time.time())

    # open the shared memory array
    stim_shm = sa.attach(stim_shm_name)
    print('Attached to Stim Shared Memory')

    # store the packet number
    stim_packet_number = stim_shm[0]
    print('Found data from stim packet number', stim_packet_number)

    # store the packet data
    band_power_packet_number = stim_shm[1]
    print('Data corresponds to band power packet number', band_power_packet_number)
    
    # store the packet number
    stim_step = stim_shm[2]
    print('Stim command to change amplitude step by', stim_step, 'milliamps')

    release_time = time.time()
    stim_sem.release()
    print('Semaphore Released', time.time())
    # ***** end protected mutex session *****

    return (stim_packet_number, stim_step)

def read_band_power():

    # ***** start protected mutex session *****
    acquire_time = time.time() 
    band_power_sem.acquire(timeout=0)

    print('Band Power Semaphore Acquired:', time.time()) 

    # open the shared memory array 
    band_power_shm = sa.attach(band_power_shm_name)
    print('Attached to Band Power Shared Memory')

    # get the packet number (first entry in lfp shared memory array) 
    band_power_num_packets_i = int(band_power_shm[0])
    print('Found data from packet number', band_power_num_packets_i)

    # get the packet data (the other entries in the lfp shared memory array) 
    band_power = band_power_shm[1:] 
    print('Loaded data', band_power, 'into numpy array')

    release_time = time.time()
    band_power_sem.release()
    print('Semaphore Released:', time.time())
    # ***** end protected mutex session *****

    band_power_num_packets = band_power_num_packets_i

    # STEP TWO: CALCULATE THE STIM AMPLITUDE 
    step = calculate_stim(band_power) 

    return (band_power_num_packets_i, band_power)

def get_data(): 

    stim_packet_number = -1
    band_power_packet_number = -1

    # Get stim data 
    try:
        stim_packet_number, stim_step = read_stim()
        stim_data_x.append(stim_step)
        stim_data_y.append(stim_packet_number)
    except posix_ipc.BusyError:
        print('POSIX is Busy')

    # Get band power data 
    try: 
        band_power_packet_number, band_power = read_band_power()
        band_power_data_x.append(np.mean(band_power))
        band_power_data_y.append(band_power_packet_number)
    except posix_ipc.BusyError:
        print('POSIX is Busy')

def chartfunc(): 
    get_data()
    ax1.plot(stim_data_x, stim_data_y)
    ax2.plot(band_power_data_x, band_power_data_y)

fig, (ax1, ax2) = plt.subplots(2, 1)
fig.suptitle('Real Time Closed Loop DBS')

animator = ani.FuncAnimation(fig, chartfunc, interval = 500)
plt.show()

# out_file = r'C:\Users\Gary\Desktop'
# animator.save(out_file)
