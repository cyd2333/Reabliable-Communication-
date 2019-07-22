#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.userlib import *
from random import randint
import time
from ipaddress import IPv4Address

def print_output(total_time, num_ret, num_tos, throughput, goodput):
    print("Total TX time (s): " + str(total_time))
    print("Number of reTX: " + str(num_ret))
    print("Number of coarse TOs: " + str(num_tos))
    print("Throughput (Bps): " + str(throughput))
    print("Goodput (Bps): " + str(goodput))

    
def switchy_main(net):
    my_intf = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_intf]
    myips = [intf.ipaddr for intf in my_intf]
    times =[]
    start = time.time()
    print(times)
    # read txt file to get params
    with open('blaster_params.txt', 'r') as f: 
        for line in f: 
            l = line.strip().split(' ')
            # how many packet need to send
            num = int(l[1])
            # len of payload
            length = int(l[3])
            sender_window = int(l[5])
            timeout = int(l[7])/1000
            recv_timeout = int(l[9])
    log_info(recv_timeout)
    counter_resend = 0
    counter_all = 0
    LHS = 0
    RHS = 0
    while True:
        log_info("loop begin!!!!")
        gotpkt = True
        try:
            #Timeout value will be parameterized!
            log_info(time.time())
            timestamp,dev,pkt = net.recv_packet(timeout=recv_timeout/1000)
        except NoPackets:
            log_info("No packets available in recv_packet")
            gotpkt = False
        except Shutdown:
            log_info("Got shutdown signal")
            break

        if gotpkt:
            log_info("I got a packet")
            # print("I receive a pkt!")
            # do we need to chekc order, or just increse LHS?
            has_rawbyte = pkt.has_header("RawPacketContents")
            if(has_rawbyte):
                # if it has rawbyte header
                # print(pkt)
                raw = pkt.get_header_by_name("RawPacketContents")
                rev_data = raw.data
                rev_seqnum = rev_data[:4]
                rev_seqnum = int.from_bytes(rev_seqnum, byteorder='big')
                rev_payload = rev_data[4:]
                if(len(rev_payload) == 8):
                    # it is ACK!!!
                    # update time table
                    times[rev_seqnum] = (times[rev_seqnum][0], times[rev_seqnum][1], True)
                """ if times[LHS][2] is True:
                    LHS += 1 """
                should_move_to =0
                for idx in range(len(times)):
                    if times[idx][2] is True:
                        should_move_to += 1
                    else:
                        break
                LHS = should_move_to

            
        else:
            log_info("Didn't receive anything")

            '''
            Creating the headers for the packet
            '''
        
        pkt = Ethernet() + IPv4() + UDP()
        pkt[1].protocol = IPProtocol.UDP
        
        pkt[1].dst = IPv4Address("192.168.200.1")
        pkt[1].src = IPv4Address("192.168.100.1")
       
        pkt[0].src = '10:00:00:00:00:01'
        pkt[0].dst = '40:00:00:00:00:01'
        
        '''
        Do other things here and send packet
        '''
        # each time we just send one pkt or mutiple pkts ?????
        # print(num)
        # simple move forward
        # print(str(RHS) + ' '+ str(LHS))
        if RHS < num and RHS - LHS <= sender_window:
            pkt_seqnum = (RHS.to_bytes(4, byteorder= 'big')) 
            # pkt_payload = ("a") * (randint(1, length))
            pkt_payload = ("a") * length
            pkt_length = (len(pkt_payload).to_bytes(2, byteorder = 'big'))
            pkt_payload = pkt_payload.encode()
            pkt += RawPacketContents(pkt_seqnum + pkt_length + pkt_payload)
            #print(type(pkt_seqnum)+"\t"+type(pkt_length)+"\t"+type(pkt_payload))
            log_info(pkt_length)
            net.send_packet(my_intf[0].name, pkt)
            temp = pkt
            times.append((time.time(), temp, False))
            RHS += 1
            counter_all += 1
            log_info("send pkt!")
            continue
        # print(str(len(times))+"****")
        # check time out... just brute force go through all of 
        # entries in time list...
        for i in list(times[LHS:RHS]):
            t = i[0]
            p = i[1]
            ack = i[2]
            cur = time.time()
            # print(str(timeout)+ " "+ str(cur -t ) + " "+str(ack))
            if cur - t >= timeout and (ack is False):
                net.send_packet(my_intf[0].name, p)
                temp = p
                times[times.index(i)] = ((time.time(), temp, False))
                # print("resend packet!")
                counter_resend += 1
                counter_all += 1
                log_info("resend pkt!")
                break
        if (counter_all - counter_resend) is num:
            end = time.time() - start 
            throughput = counter_all * length/end
            goodput = (counter_all - counter_resend)*length/end 
            log_info(counter_all - counter_resend)
            log_info(num * length /end)             
            print_output(end, counter_resend, counter_resend, throughput, goodput)
            break
    net.shutdown()
