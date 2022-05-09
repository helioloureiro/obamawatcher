#! /usr/bin/python3 -u
# -*- coding: utf-8 -*-

"""
Not only Obamas _is_ watching you...

Based in:
http://stackoverflow.com/questions/15870619/python-webcam-http-streaming-and-image-capture
"""


import pygame
import pygame.camera
import time
import random
import sys
import os
import notify2
import enum

# graphical support
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *


USER      = os.environ.get("USER")
SAVEDIR   = f"/home/{USER}/Pictures/Webcam"
CAMERA    = "/dev/video0"
SIZE      = "1280x720"
PCTG      = 5
HOURSTART = 9
HOURSTOP  = 17
STATUSON  = "images/obama-recording.png"
STATUSOFF = "images/obama-watching.png"

def debug(*msg):
    if "DEBUG" in os.environ:
        print(*msg)


class Status(enum.Enum):
    """
    Icon status.
    """
    ON  = 1
    OFF = 2


class ObamaWatcher(QApplication):
    def __init__(self):
        """
        Initialize ObamaWatcher QT application.
        """
        # to get icons properly in place
        programFile=sys.argv[0]
        programPath=os.path.dirname(programFile)
        programPath=os.path.abspath(programPath)
        os.chdir(programPath)

        # if not there, create SAVEDIR
        if not os.path.exists(SAVEDIR):
            os.makedirs(SAVEDIR)


        QApplication.__init__(self)
        self.setQuitOnLastWindowClosed(False)

        self.CWD = os.path.abspath(".")

        # Adding item on the menu bar
        self.tray = QSystemTrayIcon()
        self.setStatus(Status.OFF)
        self.tray.setVisible(True)

        self.webcam = WebcamMonitoring(parent=self)
        self.webcam.start()

        menu = QMenu()

        # manual photo option
        photo = QAction("Photo now!")
        photo.triggered.connect(self.getPhoto)
        menu.addAction(photo)

        # To quit the app
        quit = QAction("Quit")
        quit.triggered.connect(self.quit)
        menu.addAction(quit)

        # Adding options to the System Tray
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("ObamaWatcher is watching you 👀!")
        self.exec_()

    def setStatus(self, status):
        """
        Update menu icon if up or down.
        """
        debug("ObamaWatcher: setStatus received:", status)
        if status == Status.ON:
            picture = STATUSON
        else:
            picture = STATUSOFF
        picture = f"{self.CWD}/{picture}"
        debug("ObamaWatcher: got the picture:", picture)
        icon = QIcon(picture)
        self.tray.setIcon(icon)

    def getPhoto(self):
        debug("ObamaWatcher: called getPhoto()")
        self.webcam.getPhoto()

class WebcamMonitoring(QThread):
    def __init__(self, parent=None):
        """
        Initialize QThread and pygame.
        """
        QThread.__init__(self, parent)
        self.parent = parent
        pygame.init()
        pygame.camera.init()
        notify2.init("Obamawatcher is watching you 👀!")

    def getPictureSize(self):
        """
        Reads the configuration size in format AxB, and returns
        (int(A), int(B))
        """
        x, y = SIZE.split("x")
        return (int(x), int(y))

    def getCamera(self):
        """
        Returns the camera object from pygame, which device and picture size set.
        """
        debug("WebcamMonitoring: called getCamera()")
        return pygame.camera.Camera(CAMERA, self.getPictureSize())

    def getYourLuck(self):
        """
        Just to decide if take a shot or not.
        """
        debug("WebcamMonitoring: called GetYourLuck()")
        if (random.randrange(100) < PCTG):
            return True
        return False

    def getPhoto(self):
        """
        Take a picture, notify user (to avoid surprises) and save.
        """
        notify2.Notification("Smile! obamawatch is 👀... you do know the drill :)").show()
        # wait 3s to get notice (brain takes around 3s to react)
        QThread.sleep(3)

        self.parent.setStatus(Status.ON)
        webcam = self.getCamera()
        webcam.start()
        debug(" * getting image")
        image = webcam.get_image()
        webcam.stop()

        timestamp = time.strftime("%Y-%m-%d_%H%M%S", time.localtime())
        year = time.strftime("%Y", time.localtime())
        if not os.path.exists("%s/%s" % (SAVEDIR, year)):
            os.mkdir("%s/%s" % (SAVEDIR, year))
        filename = "%s/%s/%s.jpg" % (SAVEDIR, year, timestamp)

        #pynotify.Notification("Photo: saving into %s" % filename).show()
        debug(f"Photo: {filename}")
        pygame.image.save(image, filename)

        # wait 5s to show next message to avoid flood
        QThread.sleep(5)
        notify2.Notification("obamawatch saved your picture: %s :)" % filename).show()
        self.parent.setStatus(Status.OFF)

    def run(self):
        """
        Main thread that keep running.
        """
        debug("WebcamMonitoring: called start()")
        # give one minute for menu to start
        QThread.sleep(60)
        debug("WebcamMonitoring: starting the monitoring loop")
        while True:
            # skip at certain times
            if not self.getYourLuck():
                debug(" * bad luck... waiting")
                QThread.sleep(random.randrange(10) * 60)
                continue
            debug(" * luck boy!")

            hour = int(time.strftime("%H", time.localtime()))
            if hour < HOURSTART or hour > HOURSTOP:
                print(f"Not a good time: {hour}")
                continue

            self.getPhoto()


    def stop(self):
        """
        Terminating this thread.
        """
        debug("WebcamMonitoring: called stop()")
        self.terminate()


if __name__ == '__main__':
    try:
        ObamaWatcher()
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        pass
