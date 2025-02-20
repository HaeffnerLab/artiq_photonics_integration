import unittest
import asyncio
import textwrap
import logging
from PyQt5 import QtCore, QtGui, QtWidgets
from qasync import QEventLoop
from artiq.coredevice.comm_moninj import *
from artiq.test.hardware_testbench import ExperimentCase
from artiq.coredevice.ad9912_reg import AD9912_SER_CONF
from sipyco.pc_rpc import AsyncioClient, Client
import asyncio
import atexit
async def _submit_by_content(schedule_ctl, content, class_name, title):
        print('here3')

        expid = {
            "log_level": logging.WARNING,
            "content": content,
            "class_name": class_name,
            "arguments": {}
        }
        scheduling = {
            "pipeline_name": "main",
            "priority": 0,
            "due_date": None,
            "flush": False
        }
        rid = await schedule_ctl.submit(
            scheduling["pipeline_name"],
            expid,
            scheduling["priority"], scheduling["due_date"],
            scheduling["flush"])
        print(f"Submitted '{title}', RID is {rid}")
        # logger.info("Submitted '%s', RID is %d", title, rid)

def _dds_faux_injection(schedule_ctl, title, log_msg):
        # create kernel and fill it in and send-by-content
        print('here2')

        dds_exp = textwrap.dedent("""
        from artiq.experiment import *
        from artiq.coredevice.urukul import *

        class SetDDS(EnvExperiment):
            def build(self):
                self.setattr_device("core")
                self.setattr_device("urukul0_ch1")      


                
            @kernel
            def run(self):
                self.core.break_realtime()
                self.urukul0_ch1.cpld.init()
                delay(10*ms)
                self.urukul0_ch1.set(frequency = 89 * MHz, amplitude = 0.5)
                self.urukul0_ch1.sw.on()                 
        """)
        asyncio.ensure_future(_submit_by_content(
            schedule_ctl,
            dds_exp,
            title,
            log_msg))
        
        

def dds_set_frequency(schedule_ctl, dds_channel,  freq):
    print('here1')
    _dds_faux_injection(
        schedule_ctl,
        "SetDDS",
        "Set DDS {} {}MHz".format(dds_channel, freq / 1e6))


def main():
    app = QtWidgets.QApplication(["ARTIQ Dashboard"])
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    atexit.register(loop.close)
    client = AsyncioClient()
    loop.run_until_complete(client.connect_rpc(
            "::1", 3251, "schedule"))
    atexit.register(client.close_rpc)


    print(client)
    
    dds_set_frequency(client, 0, 0)

    loop.run_until_complete(asyncio.sleep(5))
        # core_host = "192.168.169.253"
    # loop_out_channel = 0x000004
    # loop_in_channel = 0x000003

    # notifications = []
    # injection_statuses = []

    # def monitor_cb(channel, probe, value):
    #     print("probe", (channel, probe, value * (32 / 171798692)))
    #     notifications.append((channel, probe, value ))

    # def injection_status_cb(channel, override, value):
    #     print("injection", (channel, override, value))

    #     injection_statuses.append((channel, override, value))

    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    
    # try:
    #     moninj_comm = CommMonInj(monitor_cb, injection_status_cb)
    #     loop.run_until_complete(moninj_comm.connect(core_host))
    #     try:


    #         # moninj_comm.monitor_probe(True, loop_out_channel, TTLProbe.level.value)
    #         # moninj_comm.monitor_injection(True, loop_out_channel, TTLOverride.level.en.value)
    #         # while True:
    #         #     print("notifications", notifications)
    #         #     print("injections", injection_statuses)

    #         #     loop.run_until_complete(asyncio.sleep(0.5))
    #         # moninj_comm.get_injection_status(0x00000a, 1)
    #         moninj_comm.monitor_probe(True, 0x000008, 0)
    #         # moninj_comm.monitor_injection(True, 0x00000a, 1)
    #         print("notifications", notifications)
    #         print("injections", injection_statuses)
    #         while True:
    #             # print("notifications", notifications)
    #             # print("injections", injection_statuses)
    #             # continue
    #             loop.run_until_complete(asyncio.sleep(0.5))
    #         ###############################

    #         # moninj_comm.inject(loop_out_channel, TTLOverride.level.value, 1)

    #         # moninj_comm.inject(loop_out_channel, TTLOverride.level.oe.value, 1)

    #         # moninj_comm.inject(loop_out_channel, TTLOverride.level.en.value, 1)
    #         # loop.run_until_complete(asyncio.sleep(0.5))
    #         # moninj_comm.get_injection_status(loop_out_channel, TTLOverride.en.value)
    #         # moninj_comm.inject(loop_out_channel, TTLOverride.level.value, 1)
    #         # loop.run_until_complete(asyncio.sleep(0.5))
    #         # moninj_comm.inject(loop_out_channel, TTLOverride.level.value, 0)
    #         # loop.run_until_complete(asyncio.sleep(0.5))
    #         # moninj_comm.inject(loop_out_channel, TTLOverride.level.en.value, 1)
    #         # loop.run_until_complete(moninj_comm._writer.drain())
    #     except Exception as e:  
    #         print(e)
    #     finally:
    #         print('hi')
    #         # loop.run_until_complete(moninj_comm.close())
    # finally:
    #     loop.close()

    # if notifications[0][2] == 1:
    #     notifications = notifications[1:]

    # # self.assertEqual(notifications, [
    # #     (loop_in_channel, , 0),
    # #     (loop_in_channel, TTLProbe.level.value, 1),
    # #     (loop_in_channel, TTLProbe.level.value, 0)
    # # ])
    # # self.assertEqual(injection_statuses, [
    # #     (loop_out_channel, TTLOverride.en.value, 0),
    # #     (loop_out_channel, TTLOverride.en.value, 0),
    # #     (loop_out_channel, TTLOverride.en.value, 1),
    # #     (loop_out_channel, TTLOverride.en.value, 1)
    # ])

if __name__ == "__main__":
    main()
