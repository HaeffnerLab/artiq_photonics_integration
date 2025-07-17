

from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QLabel, QTabWidget

class DC_Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 186)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(300, 150)

        Form.setCentralWidget(self.tabs) 
        self.tabs.addTab(self.tab1, "Electrodes")
        #self.tabs.addTab(self.tab2, "Multipoles")

        self.Electrodes_SpinBox={}
        self.Electrodes_Label={}

        #reference to the dict
        self.Multipoles=Form.Multipoles
        self.Electrodes=Form.Electrodes
        self.Multipoles_Value=Form.Multipoles_Value
        self.Electrodes_Value=Form.Electrodes_Value
        
        #electrode grid
        grid1 = QGridLayout(self.tab1)  
        for i in range(len(self.Multipoles)):            
            xcoord_label = 0
            xcoord_entry = 1
            ycoord = i
            
            SpinBox = QtWidgets.QDoubleSpinBox()
            SpinBox.setRange(-10,10)
            SpinBox.setSingleStep(0.01)
            SpinBox.setDecimals(4)
            SpinBox.setValue(self.Multipoles_Value[self.Multipoles[i]]) # set default values
            grid1.addWidget(SpinBox,ycoord,xcoord_entry,1,1)

            self.Electrodes_SpinBox[self.Multipoles[i]] = SpinBox

            #create label with name of the multipoles
            label = QLabel('       '+self.Multipoles[i])
            label.setAlignment(QtCore.Qt.AlignRight)
            grid1.addWidget(label,ycoord,xcoord_label,1,1)

        self.setMultipoleButton=QPushButton('Set')
        grid1.addWidget(self.setMultipoleButton)
        self.ResetButton=QPushButton('Reset')
        grid1.addWidget(self.ResetButton)

        for i in range(len(self.Electrodes)):
            xcoord_label = 2
            xcoord_entry = 3
            ycoord = i

            label=QLabel(self.Electrodes[i])
            label.setAlignment(QtCore.Qt.AlignRight)
            grid1.addWidget(label,ycoord,xcoord_label,1,1)

            label=QLabel(
                format(self.Electrodes_Value[self.Electrodes[i]], '.4f')
            )
            label.setAlignment(QtCore.Qt.AlignRight)
            grid1.addWidget(label,ycoord,xcoord_entry,1,1)

            self.Electrodes_Label[self.Electrodes[i]]=label
   
        QtCore.QMetaObject.connectSlotsByName(Form)
    
    def update_Electrodes_Label(self):
        for i in range(len(self.Electrodes)):
            self.Electrodes_Label[self.Electrodes[i]].setText(
                format(self.Electrodes_Value[self.Electrodes[i]], '.4f')
            )
    def update_Multipoles_Label(self):
        for i in range(len(self.Multipoles)):
            self.Electrodes_SpinBox[self.Multipoles[i]].setValue(self.Multipoles_Value[self.Multipoles[i]])
    
    def reset_Multipoles(self):
        for i in range(len(self.Multipoles)):
            self.Multipoles_Value[self.Multipoles[i]]=0
            self.Electrodes_SpinBox[self.Multipoles[i]].setValue(self.Multipoles_Value[self.Multipoles[i]]) 
