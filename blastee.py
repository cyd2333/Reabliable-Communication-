#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.userlib import *
from threading import *
import time

def switchy_main(net):
    my_interfaces = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_interfaces]

    while True:
        gotpkt = True
        try:
            timestamp,dev,pkt = net.recv_packet()
            log_debug("Device is {}".format(dev))
        except NoPackets:
            log_debug("No packets available in recv_packet")
            gotpkt = False
        except Shutdown:
            log_debug("Got shutdown signal")
            break

        if gotpkt:
            log_info("I got a packet from {}".format(dev))
            log_info("Pkt: {}".format(pkt))
            # 
            # print("I am blastee, I got a pkt!")
            # print(pkt)
            ## modify ehter.src -> dst
            ## modify ether.dst -> src
            ## modify ipv4.src -> dst
            ## modify ipv4.dst -> src
            new_dst = pkt[Ethernet].src
            new_src = pkt[Ethernet].dst
            p = Packet()
            p += Ethernet()
            p[Ethernet].src = new_src
            p[Ethernet].dst = new_dst

            ## add ip header 
            ## do I need to add swap ip address? ttl? or others ????
            new_ip_src = pkt[IPv4].dst
            new_ip_dst = pkt[IPv4].src
            p += pkt[IPv4]
            p[IPv4].src = new_ip_src
            p[IPv4].dst = new_ip_dst

            ## add udp, can use same UDP from blaster ???
            new_udp_src = pkt[UDP].dst 
            new_udp_dst = pkt[UDP].src
            p += pkt[UDP]
            p[UDP].src = new_udp_src
            p[UDP].dst = new_udp_dst
            

            ## can I use struct packge?
            ## what does length mean, two space byte?
            ## is the sequence correct?
            ## do I need to decode seq_num in blastee?

            ## put sequence into it
            
            raw_byte = pkt[RawPacketContents].data
            log_info("arrive here!")
            seq_num = raw_byte[:4]
            payload_from_blaster = raw_byte[6:]
            payload_from_blaster = payload_from_blaster.decode()
            # add a padding..
            pad = "aaaaaaaa"
            len_pad = len(payload_from_blaster)
            log_info("-----------------------------------")
            # print(len_pad)
            if(len_pad < 8):
                payload_from_blaster += pad[:(8-len_pad)]
            else:
                payload_from_blaster = pad
            p += RawPacketContents(seq_num + payload_from_blaster.encode())
            # print(payload_from_blaster)
            log_info(p)
            # print(int.from_bytes(seq_num, byteorder = 'big'))
            net.send_packet(my_interfaces[0].name, p)
    net.shutdown()
