import asyncio
import textwrap
import logging
import atexit
from PyQt5.QtWidgets import QWidget
from sipyco.pc_rpc import AsyncioClient
import asyncio

class _control_panel(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        loop = asyncio.get_event_loop()
        client = AsyncioClient()
        loop.run_until_complete(client.connect_rpc(
                "::1", 3251, "schedule"))
        # atexit.register(client.close_rpc)
        self.schedule_ctl = client


    async def _submit_by_content(self, schedule_ctl, content, class_name, title):
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

    def _faux_injection(self, setup, action, title, log_msg):
            # create kernel and fill it in and send-by-content
            dds_exp = textwrap.dedent(f"""
            from artiq.experiment import *
            from artiq.coredevice.urukul import *

            class SetDDS(EnvExperiment):
                def build(self):
                    self.setattr_device("core")   
                    {setup}                 
                @kernel
                def run(self):
                    self.core.reset()
                    self.core.break_realtime() 
                    delay(1*s)       
                    {action}    
            """)

            asyncio.ensure_future(self._submit_by_content(
                self.schedule_ctl,
                dds_exp,
                title,
                log_msg))
            

    def dds_set_frequency(self, board_name, freq, atten):
        setup = f"""
                    self.setattr_device("{board_name}")
        """
        action = f"""
                    self.{board_name}.set({freq} * MHz)
                    self.{board_name}.set_att({atten} * dB)
                    self.{board_name}.sw.on()
        """
        self._faux_injection(
            setup,
            action,
            "SetDDS",
            "Set {} {}MHz {}dB".format(board_name, freq, atten))
        
    def dds_turn_off(self, board_name):
        setup = f"""self.setattr_device("{board_name}")"""
        
        action = f"""
                    self.{board_name}.sw.off()
        """
        self._faux_injection(
            setup,
            action,
            "SetDDS",
            "Turn off {}".format(board_name))

    def dac_set(self, channel, voltage):
        setup = f"""
                    self.setattr_device("zotino0")
        """
        action = f"""
                    self.zotino0.init()
                    delay(1*s)
                    self.zotino0.write_dac({channel}, {voltage})
                    self.zotino0.load()
        """
        self._faux_injection(
            setup,
            action,
            "SetDDS",
            "Set DAC{} {}V".format(channel, voltage))
