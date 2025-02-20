import unittest
import asyncio

from artiq.coredevice.comm_moninj import *
from artiq.test.hardware_testbench import ExperimentCase

def main():
    core_host = "192.168.169.253"
    loop_out_channel = 0x000004
    loop_in_channel = 0x000003

    notifications = []
    injection_statuses = []

    def monitor_cb(channel, probe, value):
        print("probe", (channel, probe, value * (32 / 171798692)))
        notifications.append((channel, probe, value ))

    def injection_status_cb(channel, override, value):
        print("injection", (channel, override, value))

        injection_statuses.append((channel, override, value))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        moninj_comm = CommMonInj(monitor_cb, injection_status_cb)
        loop.run_until_complete(moninj_comm.connect(core_host))
        try:


            # moninj_comm.monitor_probe(True, loop_out_channel, TTLProbe.level.value)
            # moninj_comm.monitor_injection(True, loop_out_channel, TTLOverride.level.en.value)
            # while True:
            #     print("notifications", notifications)
            #     print("injections", injection_statuses)

            #     loop.run_until_complete(asyncio.sleep(0.5))
            # moninj_comm.get_injection_status(0x00000a, 1)
            moninj_comm.monitor_probe(True, 0x000008, 0)
            # moninj_comm.monitor_injection(True, 0x00000a, 1)
            print("notifications", notifications)
            print("injections", injection_statuses)
            while True:
                # print("notifications", notifications)
                # print("injections", injection_statuses)
                # continue
                loop.run_until_complete(asyncio.sleep(0.5))
            ###############################

            # moninj_comm.inject(loop_out_channel, TTLOverride.level.value, 1)

            # moninj_comm.inject(loop_out_channel, TTLOverride.level.oe.value, 1)

            # moninj_comm.inject(loop_out_channel, TTLOverride.level.en.value, 1)
            # loop.run_until_complete(asyncio.sleep(0.5))
            # moninj_comm.get_injection_status(loop_out_channel, TTLOverride.en.value)
            # moninj_comm.inject(loop_out_channel, TTLOverride.level.value, 1)
            # loop.run_until_complete(asyncio.sleep(0.5))
            # moninj_comm.inject(loop_out_channel, TTLOverride.level.value, 0)
            # loop.run_until_complete(asyncio.sleep(0.5))
            # moninj_comm.inject(loop_out_channel, TTLOverride.level.en.value, 1)
            # loop.run_until_complete(moninj_comm._writer.drain())
        except Exception as e:  
            print(e)
        finally:
            print('hi')
            # loop.run_until_complete(moninj_comm.close())
    finally:
        loop.close()

    if notifications[0][2] == 1:
        notifications = notifications[1:]

    # self.assertEqual(notifications, [
    #     (loop_in_channel, , 0),
    #     (loop_in_channel, TTLProbe.level.value, 1),
    #     (loop_in_channel, TTLProbe.level.value, 0)
    # ])
    # self.assertEqual(injection_statuses, [
    #     (loop_out_channel, TTLOverride.en.value, 0),
    #     (loop_out_channel, TTLOverride.en.value, 0),
    #     (loop_out_channel, TTLOverride.en.value, 1),
    #     (loop_out_channel, TTLOverride.en.value, 1)
    # ])

if __name__ == "__main__":
    main()
