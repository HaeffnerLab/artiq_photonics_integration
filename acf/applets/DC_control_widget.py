import os
import subprocess
import numpy as np
import pandas as pd
import PyQt5
# import pyqtgraph as pg
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox

# Add the project root to the PYTHONPATH
import sys
from pathlib import Path
root_path=str(Path(__file__).resolve().parent.parent.parent)
sys.path.append(root_path)
sys.path.append(root_path+'/DC_hardware/')

from artiq.applets.simple import TitleApplet, SimpleApplet

from DC_control_gui import DC_Ui_Form

from  Electrode2multipole import multipole2electode
import sys

class DCControlWidget(QtWidgets.QMainWindow):

    def __init__(self, args, req):
        super().__init__()
        self.param_prefix='__param__multipole/'
        self.ele_prefix='__param__DC/'
        self.req = req
        
        #init variable
        self.Electrodes_Value={'DC0':0,'DC1':0,'DC2':0,
                               'DC3':0,'DC4':0,'DC5':0,
                               'DC6':0,'DC7':0,'DC8':0}
        self.Multipoles_Value={'Ex':0,'Ey':0,'Ez':0,
                               'U1':0,'U2':0,'U3':0,
                               'U4':0,'U5':0}

        self.Electrodes = ["DC0","DC1","DC2","DC3","DC4","DC5","DC6","DC7","DC8"]  # Labels for text entry
        self.Multipoles = ["Ex","Ey","Ez","U1","U2","U3","U4","U5"]

        #init UI
        self.graphics = DC_Ui_Form()
        self.setupUi()

        self.graphics.setMultipoleButton.clicked.connect(self.on_button_set)
        self.graphics.ResetButton.clicked.connect(self.on_button_reset)


    def check_DC_range(self, new_multipoles):
        tmp_electrodes=multipole2electode(new_multipoles)
        for i in tmp_electrodes:
            if i<-9.5 or i>9.5:
                return False
        return True

    def data_changed(self, value, metadata, persist, mods):
        
        mod=mods[0]

        if mod["action"] == "init":
            
            tmp_multipole=self.Multipoles_Value.copy()
            for i in self.Multipoles:
                tmp_multipole[i]=value[self.param_prefix+i]
            
            if not self.check_DC_range(tmp_multipole):
                print("Initial DC out of Range!!!!\n")
                print("Set to Zero!")
            else:
                for i in self.Multipoles:
                    self.Multipoles_Value[i]=value[self.param_prefix+i]

            self.update_Electrodes()
            self.graphics.update_Electrodes_Label()
            self.graphics.update_Multipoles_Label()
            self.submit_exp()
        elif mod["action"] == "setitem":
            
            flag=False
            for i in self.Multipoles:
                #if there are changes, update the electrode
                if(np.abs(self.Multipoles_Value[i]-value[self.param_prefix+i])>1e-6):
                    flag=True
            if not flag:
                return

            tmp_multipole=self.Multipoles_Value.copy()
            for i in self.Multipoles:
                tmp_multipole[i]=value[self.param_prefix+i]
            
            

            if not self.check_DC_range(tmp_multipole):
                print("DC out of Range!!!!\n")
            else:
                for i in self.Multipoles:

                    #if there are changes, update the electrode
                    if(np.abs(self.Multipoles_Value[i]-value[self.param_prefix+i])>1e-6):
                        flag=True

                    self.Multipoles_Value[i]=value[self.param_prefix+i]

            self.update_Electrodes()
            self.graphics.update_Electrodes_Label()
            self.graphics.update_Multipoles_Label()
            
            self.submit_exp()
        else:
            print("Don't delete DC data sets!!!!!!!!!!!!!!!!!!!!!!!!!1")
            exit(-1)
    
    def param_changed(self):

        for i in self.Multipoles:
            dataset_name=self.param_prefix+i
            value=self.Multipoles_Value[i]
            self.req.set_dataset(dataset_name, value)
        
        for i in self.Electrodes:
            dataset_name=self.ele_prefix+i
            value=self.Electrodes_Value[i]
            self.req.set_dataset(dataset_name, value)


    def setupUi(self):
        self.graphics.setupUi(self)
    
    def check_Multipoles(self):
        tmp_multipole=self.Multipoles_Value.copy()
        for i in range(len(self.Multipoles)):
            tmp_multipole[self.Multipoles[i]]=self.graphics.Electrodes_SpinBox[self.Multipoles[i]].value()
        return self.check_DC_range(tmp_multipole)
    
    def update_Multipoles(self):
        for i in range(len(self.Multipoles)):
            self.Multipoles_Value[self.Multipoles[i]]=self.graphics.Electrodes_SpinBox[self.Multipoles[i]].value()
    
    def update_Electrodes(self):
        self.Electrodes_Value.update(multipole2electode(self.Multipoles_Value))


    def submit_exp(self):
        exp_file = root_path + "/repository/set_dc.py"
        # run_args = f"artiq_client submit {exp_file}  --class-name SetDC"
        # os.system(run_args)

                
        run_args = [
            "artiq_client",
            "submit",
            exp_file,
            "--class-name",
            "SetDC"
        ]
        
        subprocess.run(run_args)

    def on_button_set(self):

        flag= self.check_Multipoles()
        
        if flag:
            self.update_Multipoles()
            self.update_Electrodes()
            self.param_changed()
            self.submit_exp()
        else:
            print("DC out of Range!!!!\n")

        self.graphics.update_Electrodes_Label()
        self.graphics.update_Multipoles_Label()
        

    def on_button_reset(self):
        self.graphics.reset_Multipoles()
        self.update_Multipoles()
        self.update_Electrodes()
        self.param_changed()
        self.graphics.update_Electrodes_Label()
        self.graphics.update_Multipoles_Label()
        self.submit_exp()


def main():
    # app = QApplication(sys.argv)
    # window=DCControlWidget(sys.argv)
    # window.show() 
    # sys.exit(app.exec_())

    applet = SimpleApplet(DCControlWidget)
    applet.add_dataset("Ex", "DC Multipole Values")
    applet.add_dataset("Ey", "DC Multipole Values")
    applet.add_dataset("Ez", "DC Multipole Values")
    applet.add_dataset("U1", "DC Multipole Values")
    applet.add_dataset("U2", "DC Multipole Values")
    applet.add_dataset("U3", "DC Multipole Values")
    applet.add_dataset("U4", "DC Multipole Values")
    applet.add_dataset("U5", "DC Multipole Values")
    applet.run()

if __name__ == "__main__":
    main()


#$python acf/applets/DC_control_widget.py __param__multipole/Ex __param__multipole/Ey  __param__multipole/Ez  __param__multipole/U1 __param__multipole/U2  __param__multipole/U3 __param__multipole/U4  __param__multipole/U5
