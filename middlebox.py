#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.userlib import *
from threading import *
import random
import time

def drop(percent):
    return random.randrange(100) < percent

def switchy_main(net):

    my_intf = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_intf]
    mynames = [intf.name for intf in my_intf]
    myips = [intf.ipaddr for intf in my_intf]
    # read parameter from txt file
    with open('middlebox_params.txt', 'r') as f:
        for line in f:
            l = line.split(" ")
            s = int(l[1])
            p = int(l[3])

    random.seed(s) #Extract random seed from params file
    # 
    log_info("i am here!!")


    while True:
        log_info("not here")
        gotpkt = True
        try:
            log_info("try!")
            timestamp,dev,pkt = net.recv_packet()
            log_debug("Device is {}".format(dev))
        except NoPackets:
            log_info("not receive!")
            log_debug("No packets available in recv_packet")
            gotpkt = False
        except Shutdown:
            log_info("shutdown!")
            log_debug("Got shutdown signal")
            break

        if gotpkt:
            log_info("receive!")
            log_debug("I got a packet {}".format(pkt))

        if dev == "middlebox-eth0":
            # send to bleastee
            log_debug("Received from blaster")
            '''
            Received data packet
            Should I drop it?


            If not, modify headers & send to blastee
            '''
            is_drop = drop(p)
            if is_drop is False:
                # modify the Ethernet header
                # ?? just need to change source mac address ???
                pkt[Ethernet].src = mymacs[mynames.index(dev) - 1]
                pkt[Ethernet].dst = '20:00:00:00:00:01'
                net.send_packet("middlebox-eth1", pkt)
                log_info(pkt)
        elif dev == "middlebox-eth1":
            # send to blaster
            log_debug("Received from blastee")
            '''
            Received ACK
            Modify headers & send to blaster. Not dropping ACK packets!
            net.send_packet("middlebox-eth0", pkt)
            '''
            pkt[Ethernet].src = mymacs[mynames.index(dev) - 1]
            pkt[Ethernet].dst = '10:00:00:00:00:01'
            net.send_packet("middlebox-eth0", pkt)

        else:
            log_debug("Oops :))")

    net.shutdown()
