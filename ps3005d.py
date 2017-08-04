#!/usr/bin/env python

import sys
import logging
import serial
import argparse
import time
import pandas as ps
from datetime import datetime

FORMAT = '%(levelname)-5s %(message)s'

logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.level = logging.DEBUG

device = None
data = []

def send(msg):
    global device
    # msg += '\r\n'
    # logger.debug('Sending: {0}'.format(msg))
    device.write(msg)

def receive(timeout=2000):
    global device
    end_time = time.time()+(timeout/1000)
    payload=''
    while(end_time-time.time() > 0):
        c = device.readline()
        if c:
            payload+=c
            break

    return payload


def get_id():
    send('*IDN?')
    payload=receive()
    return payload

def turn_on():
    send('OUT1')
    logger.info('Power ON')

def turn_off():
    send('OUT0')    
    logger.info('Power OFF')

def set_voltage(voltage):
    send('VSET1:{0}'.format(voltage))
    logger.info('Voltage set to {0}V'.format(voltage))

def set_current(current):
    send('ISET1:{0}'.format(current))
    logger.info('Current set to {0}V'.format(current))


def enable_ovp():
    send('OVP1')
    logger.info('Enabled OVP')

def disable_ovp():
    send('OVP0')
    logger.info('Disabled OVP')


def enable_ocp():
    send('OCP1')
    logger.info('Enabled OCP')


def disable_ocp():
    send('OCP0')
    logger.info('Disabled OCP')


def get_load_voltage():
    send('VOUT1?')
    payload=receive()
    return payload

def get_load_current():
    send('IOUT1?')
    payload=receive()
    return payload


def log(voltage,current,frequency):
    set_voltage(voltage)
    time.sleep(0.2)
    set_current(current)
    time.sleep(0.2)
    enable_ovp()
    time.sleep(0.2)
    enable_ocp()
    time.sleep(0.2)
    turn_on()
    time.sleep(0.2)
    timestamps = []
    voltages = []
    currents = []
    try:
        while True:
            v = get_load_voltage()
            i = get_load_current()
            timestamp = datetime.now()
            timestamps.append(timestamp)
            voltages.append(v)
            currents.append(i)
            time.sleep(frequency/1000)
    except KeyboardInterrupt:
        turn_off()
   
    df = ps.DataFrame(data={'voltage':voltages,'current':currents},index=timestamps)
    return df

def main():
    global device, data
    logger.info('Starting PS3005D interface')
    parser = argparse.ArgumentParser(description='PS3005D')
    parser.add_argument('port',type=str)
    parser.add_argument('cmd',type=str)
    parser.add_argument('args',nargs='*',type=float,default=[])
    parser.add_argument('--baud',dest='baud',type=int,default=9600)
    parser.add_argument('--log',dest='log',type=str,default='log.csv')
    args = parser.parse_args()

    try:
        device = serial.Serial(args.port, args.baud, timeout=1)
    except serial.SerialException:
        logger.error('Could not connect to device on {0}'.format(args.port))
        return 1

    if args.cmd == 'id':
        device_id=get_id()
        print('Device ID: {0}'.format(device_id))
    
    elif args.cmd == 'on':
        turn_on()
    
    elif args.cmd == 'off':
        turn_off()
    
    elif args.cmd == 'enable_ovp':
        enable_ovp()
    
    elif args.cmd == 'enable_ocp':
        enable_ocp()
    
    elif args.cmd == 'enable_ovp':
        disable_ovp()
    
    elif args.cmd == 'disable_ocp':
        disable_ocp()
    
    elif args.cmd == 'load_voltage':
        voltage = get_load_voltage()
        print('Load Voltage: {0}'.format(voltage))
    
    elif args.cmd == 'load_current':
        current = get_load_current()
        print('Load Voltage: {0}'.format(current))
    
    elif args.cmd == 'voltage':
        if not len(args.args) == 1:
            print('`voltage` command requires voltage argument')
            return 2
        voltage = args.args[0]
        set_voltage(voltage)
    
    elif args.cmd == 'current':
        if not len(args.args) == 1:
            print('`current` command requires current argument')
            return 2
        current = args.args[0]
        set_current(current)

    elif args.cmd == 'log':
        log_voltage = args.args[0]
        log_current = args.args[1]

        if len(args.args) == 2:
            log_frequency = 1000

        logger.info('Logging {0}V, {1}A every {2}ms'.format(log_voltage,log_current,log_frequency))

        data = log(log_voltage,log_current,log_frequency)
            
        data.to_csv(args.log,index_label='timestamp')
        logger.info('Saved {0} records to {1}'.format(len(data),args.log))


if __name__ == '__main__':
    sys.exit(main())
