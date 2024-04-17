#!/usr/bin/env python3

'''
This file contains functions to get the names of active processes and the active window.
'''

import sys
import psutil

# pylint: disable=import-error
if sys.platform in ['linux', 'linux2']:
    import Xlib
    import Xlib.display
    display = Xlib.display.Display()
    root = display.screen().root
elif sys.platform in ['Windows', 'win32', 'cygwin']:
    import win32gui
elif sys.platform in ['Mac', 'darwin', 'os2', 'os2emx']:
    from AppKit import NSWorkspace
else:
    print("Unknown platform: " + sys.platform)

def get_active_processes():
    '''
    Get the names of all running processes.
    '''
    return {p.name() for p in psutil.process_iter(["name"])}

# Adapted from Martin Thoma on stackoverflow
# https://stackoverflow.com/a/36419702/8068814
def get_active_window():
    '''
    Get the name of the active window.
    '''
    active_window_name = None
    try:
        if sys.platform in ['linux', 'linux2']:
            window_id = root.get_full_property(display.intern_atom('_NET_ACTIVE_WINDOW'), Xlib.X.AnyPropertyType).value[0]
            window = display.create_resource_object('window', window_id)
            return window.get_wm_class()[0]
        if sys.platform in ['Windows', 'win32', 'cygwin']:
            window = win32gui.GetForegroundWindow()
            active_window_name = win32gui.GetWindowText(window)
        elif sys.platform in ['Mac', 'darwin', 'os2', 'os2emx']:
            active_window_name = NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
    except Exception:
        print("Could not get active window: ", sys.exc_info()[0])
    return active_window_name
