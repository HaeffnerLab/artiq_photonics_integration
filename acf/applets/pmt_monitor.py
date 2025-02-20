import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from artiq.applets.simple import TitleApplet, SimpleApplet

class PMTMonitor(QWidget):
    def __init__(self,args, req):
        super().__init__()

        self.number = 0  # Initialize the number to 0

        self.pmt_count_name='PMT_count'

        self.initUI()



    def initUI(self):
        # Set up the layout
        layout = QVBoxLayout()

        # Create a label to display the number
        self.label = QLabel(str(self.number), self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont('Arial', 48))  # Set the font size to 24
        layout.addWidget(self.label)

        # Create a button to increase the number
        # self.button = QPushButton('Increase Number', self)
        # self.button.clicked.connect(self.increase_number)
        # layout.addWidget(self.button)

        # Set the layout for the widget
        self.setLayout(layout)

        # Set the window title and size
        self.setWindowTitle('Number Display Widget')
        self.setGeometry(300, 300, 400, 200)

    def change_number(self):
    #
        self.label.setText(str(self.number))

    def data_changed(self, value, metadata, persist, mod_buffer):
        if self.pmt_count_name not in value:
            raise RuntimeError(f"Dataset name '{self.pmt_count_name}' not in value.")

        self.number=value[self.pmt_count_name][0]

        self.change_number()


        



#     def data_changed(self, value, metadata, persist, mod_buffer):
#         if self.y_dataset_name not in value:
#             raise RuntimeError(f"Y Dataset name '{self.y_dataset_name}' "
#                                 "not in value.")

#         if self.has_x_dataset and self.x_dataset_name not in value:
#             raise RuntimeError(f"X Dataset name '{self.x_dataset_name}' "
#                                 "not in value.")

#         if self.has_fit_dataset and self.fit_dataset_name not in value:
#             raise RuntimeError(f"Fit Dataset name '{self.fit_dataset_name}' "
#                                 "not in value.")       

#         y_data = value[self.y_dataset_name]
#         if self.has_x_dataset:
#             x_data = value[self.x_dataset_name]
#         else:
#             x_data = np.arange(len(y_data))
        
#         if self.has_fit_dataset:
#             fit_data=value[self.fit_dataset_name]
        
#         # If x_data and y_data have different lengths, wait one update cycle
#         # to see if the other has updated to the right length. Else raise an error.
#         if x_data.size != y_data.size:
#             if not self.waiting_for_size_update:
#                 self.waiting_for_size_update = True
#                 return
#             else:
#                 raise RuntimeError(
#                     f"Size mismatch between x_data ({x_data.size}) "
#                     f"and y_data ({y_data.size})."
#                 )
        
#         # If we waited for a size update and sizes matched, unset this flag
#         elif self.waiting_for_size_update:
#             self.waiting_for_size_update = False

#         self.clear()
#         self.plot(x_data, y_data, pen=self.pen, symbol="o").setSymbolSize(5)
        
#         if self.has_fit_dataset:
#            self.plot(x_data, fit_data, pen='r')#, symbol='o').setSymbolSize(5)



def main():
    applet = SimpleApplet(PMTMonitor)
    #applet = TitleApplet(ExperimentMonitor)
    applet.add_dataset("pmt_count", "PMT_count")
    
    applet.run()


if __name__ == "__main__":
    main()
