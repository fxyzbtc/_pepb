from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtWidgets import QApplication, QMainWindow
import sys
from lib.mainUi import Ui_Sync

import logging
from lib.utils import logger

class LogEmittedConn(QtCore.QObject):
    signal = QtCore.Signal(str)

class GuiLoggerHandler(logging.Handler):

    def __init__(self, parent):
        super().__init__()

        fmt = logging.Formatter('%(asctime)s|file:%(filename)s|line:%(lineno)d|%(message)s')
        self.setFormatter(fmt)
        self.plainTextEdit_log = parent.plainTextEdit_log
        self.setLevel(logging.DEBUG)
        self.logEmittedConn = LogEmittedConn()

    def emit(self, record):
        # 重写handler的emit事件，触发Signal -> connected to TextEdit.append
        msg = self.format(record)
        self.logEmittedConn.signal.emit(msg)
        
from PySide2.QtWidgets import QDialog        
class AboutWindow(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        import lib.aboutUi as aboutUi
        self.child= aboutUi.Ui_Dialog_about()
        self.child.setupUi(self)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # 重定向所有的输出
        # https://stackoverflow.com/questions/55050685/how-to-correctly-redirect-stdout-logging-and-tqdm-into-a-pyqt-widget
        # https://stackoverflow.com/questions/28655198/best-way-to-display-logs-in-pyqt
        # 
        #sys.stdout = EmittingStream()
        #sys.stdout.textWritten.connect(self.onLogEmitted)

        # 运行子程序的pool，必须在__init__阶段初始化，在sync时会进入子进程造成阻塞
        self.pool = QtCore.QThreadPool()
        self.pool.setMaxThreadCount(1)

        #装载UI界面      
        self.ui = Ui_Sync()
        self.ui.setupUi(self)
        
        #绑定事件
        self.ui.pushButton_run.clicked.connect(self.sync)
        self.ui.checkBox_debug.stateChanged.connect(self.setLogLevel)
        
        #绑定logging.handler的emit -> Signal到TextEdit
        guih = GuiLoggerHandler(parent=self.ui)
        guih.logEmittedConn.signal.connect(self.onLogEmitted)
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger().addHandler(guih)

        logging.info('启动进程成功') 

    @QtCore.Slot()
    def onLogEmitted(self, text):
        self.ui.plainTextEdit_log.appendPlainText(text)
        from PySide2.QtGui import QTextCursor
        self.ui.plainTextEdit_log.moveCursor(QTextCursor.End)

    def __del__(self):
        # Restore sys.stdout
        sys.stdout = sys.__stdout__

    def setLogLevel(self):
        # 更新日志级别
        if self.ui.checkBox_debug.isChecked():
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO) 

    def sync(self):
        from lib.sync import UpdateFund
        from lib.sync import UpdateIndice
        from lib.sync import UpdatePePb

        #import pdb;pdb.set_trace()

        if not (self.ui.checkBox_fund.isChecked() or self.ui.checkBox_indice.isChecked() or self.ui.checkBox_pepb.isChecked()):
            logger.info('请选择要更新的内容')

        else:
            if self.ui.checkBox_fund.isChecked():
                updateFund = UpdateFund()
                updateFund.progConn.signal.connect(self.onCountChanged)
                self.pool.start(updateFund)

            if self.ui.checkBox_indice.isChecked():
                updateIndice = UpdateIndice()
                updateIndice.progConn.signal.connect(self.onCountChanged)
                self.pool.start(updateIndice)

            if self.ui.checkBox_pepb.isChecked():
                updatePePb = UpdatePePb()
                updatePePb.progConn.signal.connect(self.onCountChanged)
                self.pool.start(updatePePb)
            
            self.ui.pushButton_run.setEnabled(False)
        #if not self.pool.activeThreadCount():
       
    @QtCore.Slot(float)
    def onCountChanged(self, value):
        self.ui.progressBar.setValue(value)
        if value == 100:
            self.ui.pushButton_run.setEnabled(True)
        else:
            self.ui.pushButton_run.setEnabled(False)

def to_login(next_window):

    def _verify():
        import hashlib
        from datetime import datetime
        day = datetime.today().strftime('%Y%m')
        #signature = hashlib.sha256('jiedanjishiben'+day).hexdigest()[:6]
        signature = day
        password = loginUi.lineEdit_password.text()

        if password == signature:
            loginDialog.close()
            next_window.show()
            return True
        else:
            from PySide2.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap("media/icons/cookie--plus.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
            msg.setWindowIcon(icon)
            msg.setText("请重新输入")
            msg.setInformativeText("或者添加公众号获取密码")
            msg.setWindowTitle("密码错误")
            msg.setDetailedText("公众号: \n小鱼量化\n结丹记事本儿")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            retval = msg.exec_()
            return retval
            #msg.buttonClicked.connect(msgbtn)    

    from lib.LoginUi import Ui_Dialog_password
    loginUi = Ui_Dialog_password()
    loginDialog = QDialog()
    loginUi.setupUi(loginDialog)
    loginUi.pushButton_login.clicked.connect(_verify)
    loginDialog.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    aboutWindow = AboutWindow()
    QtCore.QObject.connect(mainWindow.ui.pushButton_about,QtCore.SIGNAL("clicked()"),aboutWindow.show)
    
    to_login(next_window = mainWindow)

    sys.exit(app.exec_())