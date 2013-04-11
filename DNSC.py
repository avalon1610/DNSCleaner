import sys
import win32api
import win32con
import win32gui_struct
import SysTrayIcon as TrayIcon
import dns
import threading

try:
	import winxpgui as win32gui
except ImportError:
	import win32gui

class CmdWindow():
	def __init__(self):
		self.hWnd = win32gui.GetForegroundWindow()

	def show(self,sysTrayIcon):
		win32gui.ShowWindow(self.hWnd,win32con.SW_RESTORE)

	def hide(self,sysTrayIcon):
		win32gui.ShowWindow(self.hWnd,win32con.SW_HIDE)


if __name__ == '__main__':
	import itertools,glob

	icons = 'icon.ico'
	hover_text = "Anti DNS Pollution Tool"
	w = CmdWindow()
	menu_options = (('Show',None,w.show),
					('Hide',None,w.hide),)

	def bye(sysTrayIcon): print 'Exit'

	t = threading.Thread(target = dns.RunServer)
	t.setDaemon(True)
	t.start()
	
	TrayIcon.SysTrayIcon(icons,hover_text,menu_options,on_quit=bye)
	
	