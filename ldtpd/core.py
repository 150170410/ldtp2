'''
LDTP v2 Core.

@author: Eitan Isaacson <eitan@ascender.com>
@author: Nagappan Alagappan <nagappan@gmail.com>
@copyright: Copyright (c) 2009 Eitan Isaacson
@copyright: Copyright (c) 2009 Nagappan Alagappan
@license: LGPL

http://ldtp.freedesktop.org

This file may be distributed and/or modified under the terms of the GNU General
Public License version 2 as published by the Free Software Foundation. This file
is distributed without any warranty; without even the implied warranty of 
merchantability or fitness for a particular purpose.

See "COPYING" in the source distribution for more information.

Headers in this file shall remain intact.
'''

from pyatspi import findDescendant, Registry
import locale
import subprocess
from utils import Utils
from constants import abbreviated_roles
from waiters import ObjectExistsWaiter, GuiExistsWaiter, \
    GuiNotExistsWaiter, ObjectNotExistsWaiter, NullWaiter, \
    MaximizeWindow, MinimizeWindow, UnmaximizeWindow, UnminimizeWindow, \
    ActivateWindow, CloseWindow
from server_exception import LdtpServerException
import os
import re
import time
import pyatspi
import traceback

from menu import Menu
from text import Text
from mouse import Mouse
from table import Table
from value import Value
from generic import Generic
from combo_box import ComboBox
from page_tab_list import PageTabList

class Ldtpd(Utils, ComboBox, Table, Menu, PageTabList,
            Text, Mouse, Generic, Value):
    '''
    Core LDTP class.
    '''
    def __init__(self):
        Utils.__init__(self)
        self._states = {}
        self._get_all_state_names()


    def getapplist(self):
        '''
        Get all accessibility application name that are currently running
        
        @return: list of appliction name of string type on success.
        @rtype: list
        '''
        app_list = []
        for app in self._list_apps():
            if app.name != '<unknown>':
                app_list.append(app.name)
        return app_list

    def getwindowlist(self):
        '''
        Get all accessibility window that are currently open
        
        @return: list of window names in LDTP format of string type on success.
        @rtype: list
        '''
        window_list = []
        window_type = {}
        for gui in self._list_guis():
            window_name = self._ldtpize_accessible(gui)
            if window_name[1] == '':
                if window_name[0] in window_type:
                    window_type[window_name[0]] += 1
                else:
                    window_type[window_name[0]] = 0
                tmp_name = '%d' % window_type[window_name[0]]
            else:
                tmp_name = window_name[1]
            w_name = window_name = '%s%s' % (window_name[0], tmp_name)
            index = 1
            while window_name in window_list:
                window_name = '%s%d' % (w_name, index)
                index += 1
            window_list.append(window_name)
        return window_list

    def isalive(self):
        return True

    def _get_all_state_names(self):
        """
        This is used by client internally to populate all states
        Create a dictionary
        """
        for state in pyatspi.STATE_VALUE_TO_NAME.keys():
            self._states[state.__repr__()] = state
        return self._states

    def launchapp(self, cmd, args=[], delay = 5, env = 1):
        '''
        Launch application.

        @param cmdline: Command line string to execute.
        @type cmdline: string
        @param args: Arguments to the application
        @type args: list
        @param delay: Delay after the application is launched
        @type delay: int
        @param env: GNOME accessibility environment to be set or not
        @type env: int

        @return: PID of new process
        @rtype: integer

        @raise LdtpServerException: When command fails
        '''
        os.environ['NO_GAIL'] = '0'
        os.environ['NO_AT_BRIDGE'] = '0'
        if env:
            os.environ['GTK_MODULES'] = 'gail:atk-bridge'
            os.environ['GNOME_ACCESSIBILITY'] = '1'
        try:
            process = subprocess.Popen([cmd]+args, close_fds = True)
            # Let us wait so that the application launches
            try:
                time.sleep(int(delay))
            except ValueError:
                time.sleep(5)
        except Exception, e:
            raise LdtpServerException(str(e))
        os.environ['NO_GAIL'] = '1'
        os.environ['NO_AT_BRIDGE'] = '1'
        return process.pid

    def objectexist(self, window_name, object_name):
        '''
        Checks whether a window or component exists.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string

        @return: 1 if GUI was found, 0 if not.
        @rtype: integer
        '''
        return self.guiexist(window_name, object_name)

    def maximizewindow(self, window_name):
        '''
        Maximize a window using wnck
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string

        @return: 1 if window maximized, 0 if not.
        @rtype: integer
        '''
        waiter = MaximizeWindow(window_name)

        return int(waiter.run())

    def minimizewindow(self, window_name):
        '''
        Minimize a window using wnck
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string

        @return: 1 if window minimized, 0 if not.
        @rtype: integer
        '''
        waiter = MinimizeWindow(window_name)

        return int(waiter.run())

    def unmaximizewindow(self, window_name):
        '''
        Unmaximize a window using wnck
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string

        @return: 1 if window unmaximized, 0 if not.
        @rtype: integer
        '''
        waiter = UnmaximizeWindow(window_name)

        return int(waiter.run())

    def unminimizewindow(self, window_name):
        '''
        Unminimize a window using wnck
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string

        @return: 1 if window unminimized, 0 if not.
        @rtype: integer
        '''
        waiter = UnminimizeWindow(window_name)

        return int(waiter.run())

    def activatewindow(self, window_name):
        '''
        Activate a window using wnck
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string

        @return: 1 if window unminimized, 0 if not.
        @rtype: integer
        '''
        waiter = ActivateWindow(window_name)

        return int(waiter.run())

    def closewindow(self, window_name):
        '''
        Close a window using wnck
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string

        @return: 1 if window unminimized, 0 if not.
        @rtype: integer
        '''
        waiter = CloseWindow(window_name)

        return int(waiter.run())

    def guiexist(self, window_name, object_name=''):
        '''
        Checks whether a window or component exists.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string

        @return: 1 if GUI was found, 0 if not.
        @rtype: integer
        '''
        if object_name:
            waiter = ObjectExistsWaiter(window_name, object_name, 0)
        else:
            waiter = GuiExistsWaiter(window_name, 0)

        return int(waiter.run())

    def waittillguiexist(self, window_name, object_name='', guiTimeOut=30):
        '''
        Wait till a window or component exists.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string
        @param guiTimeOut: Wait timeout in seconds
        @type guiTimeOut: integer

        @return: 1 if GUI was found, 0 if not.
        @rtype: integer
        '''
        if object_name:
            waiter = ObjectExistsWaiter(window_name, object_name, guiTimeOut)
        else:
            waiter = GuiExistsWaiter(window_name, guiTimeOut)

        return int(waiter.run())

    def waittillguinotexist(self, window_name, object_name='', guiTimeOut=30):
        '''
        Wait till a window does not exist.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type object_name: string
        @param guiTimeOut: Wait timeout in seconds
        @type guiTimeOut: integer

        @return: 1 if GUI has gone away, 0 if not.
        @rtype: integer
        '''
        if object_name:
            waiter = \
                ObjectNotExistsWaiter(window_name, object_name, guiTimeOut)
        else:
            waiter = GuiNotExistsWaiter(window_name, guiTimeOut)

        return int(waiter.run())

    def getobjectsize(self, window_name, object_name):
        '''
        Get object size
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. Or menu heirarchy
        @type object_name: string

        @return: x, y, width, height on success.
        @rtype: list
        '''
        obj = self._get_object(window_name, object_name)

        _coordinates = self._get_size(obj)
        return [_coordinates.x, _coordinates.y, \
                    _coordinates.width, _coordinates.height]

    def getallstates(self, window_name, object_name):
        '''
        Get all states of given object
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: list of integers on success.
        @rtype: list
        '''
        if re.search(';', object_name):
            obj = self._get_menu_hierarchy(window_name, object_name)
        else:
            obj = self._get_object(window_name, object_name)

        _state = obj.getState()
        _current_state = _state.getStates()
        _obj_states = []
        for state in _current_state:
            _obj_states.append(state.real)
        _state.unref()
        return _obj_states

    def hasstate(self, window_name, object_name, state):
        '''
        has state
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        '''
        try:
            if re.search(';', object_name):
                obj = self._get_menu_hierarchy(window_name, object_name)
            else:
                obj = self._get_object(window_name, object_name)

            _state = obj.getState()
            _obj_state = _state.getStates()
            state = 'STATE_%s' % state.upper()
            if state in self._states and \
                    self._states[state] in _obj_state:
                return 1
        except:
            pass
        return 0

    def grabfocus(self, window_name, object_name):
        '''
        Grab focus.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        '''
        obj = self._get_object(window_name, object_name)
        self._grab_focus(obj)

        return 1

    def click(self, window_name, object_name):
        '''
        Click item.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        '''
        obj = self._get_object(window_name, object_name)
        self._grab_focus(obj)

        if obj.getRole() == pyatspi.ROLE_TOGGLE_BUTTON:
            self._click_object(obj, '(click|activate)')
        elif obj.getRole() == pyatspi.ROLE_COMBO_BOX:
            self._click_object(obj, '(click|press)')
        else:
            self._click_object(obj)

        return 1
    
    def press(self, window_name, object_name):
        '''
        Press item.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        '''
        obj = self._get_object(window_name, object_name)
        self._grab_focus(obj)

        self._click_object(obj, 'press')

        return 1
    
    def check(self, window_name, object_name):
        '''
        Check item.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        '''
        obj = self._get_object(window_name, object_name)
        self._grab_focus(obj)

        if self._check_state(obj, pyatspi.STATE_CHECKED) == False:
            self._click_object(obj)

        return 1

    def uncheck(self, window_name, object_name):
        '''
        Uncheck item.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success.
        @rtype: integer
        '''
        obj = self._get_object(window_name, object_name)
        self._grab_focus(obj)

        if self._check_state(obj, pyatspi.STATE_CHECKED):
            self._click_object(obj)

        return 1
    
    def verifytoggled(self, window_name, object_name):
        '''
        Verify toggle item toggled.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success 0 on failure.
        @rtype: integer
        '''
        return self.verifycheck(window_name, object_name)

    def verifycheck(self, window_name, object_name):
        '''
        Verify check item.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success 0 on failure.
        @rtype: integer
        '''
        try:
            obj = self._get_object(window_name, object_name)

            return int(self._check_state(obj, pyatspi.STATE_CHECKED))
        except:
            return 0

    def verifyuncheck(self, window_name, object_name):
        '''
        Verify uncheck item.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success 0 on failure.
        @rtype: integer
        '''
        try:
            obj = self._get_object(window_name, object_name)

            return int(not self._check_state(obj, pyatspi.STATE_CHECKED))
        except:
            return 0

    def stateenabled(self, window_name, object_name):
        '''
        Check whether an object state is enabled or not
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: 1 on success 0 on failure.
        @rtype: integer
        '''
        try:
            obj = self._get_object(window_name, object_name)

            return int(self._check_state(obj, pyatspi.STATE_ENABLED))
        except:
            return 0

    def getobjectlist(self, window_name):
        '''
        Get list of items in given GUI.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string

        @return: list of items in LDTP naming convention.
        @rtype: list
        '''
        obj_list = []
        gui = self._get_window_handle(window_name)
        if not gui:
            raise LdtpServerException('Unable to find window "%s"' % \
                                          window_name)
        for name, obj, obj_index in self._appmap_pairs(gui):
            obj_list.append(name)
        return obj_list

    def getobjectinfo(self, window_name, object_name):
        '''
        Get object properties.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: list of properties
        @rtype: list
        '''
        obj = self._get_object(window_name, object_name)

        props = \
            ['child_index', 'key', 'obj_index', 'parent', 'class', \
                 'children', 'label', 'label_by']

        return props

    def getobjectproperty(self, window_name, object_name, prop):
        '''
        Get object property value.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to look for, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string
        @param prop: property name.
        @type prop: string

        @return: list of properties
        @rtype: list
        '''
        if prop == 'child_index':
            obj = self._get_object(window_name, object_name)
            return obj.getIndexInParent()
        elif prop == 'key':
            obj = self._get_object(window_name, object_name) # A sanity check.
            return object_name # For now, we only match exact names anyway.
        elif prop == 'label':
            obj = self._get_object(window_name, object_name) # A sanity check.
            return obj.name
        elif prop == 'obj_index':
            role_count = {}
            for gui in self._list_guis():
                if self._match_name_to_acc(window_name, gui):
                    for name, obj, obj_index in self._appmap_pairs(gui):
                        role = obj.getRole()
                        role_count[role] = role_count.get(role, 0) + 1
                        if name == object_name:
                            return obj_index

            raise LdtpServerException(
                'Unable to find object name in application map')
        elif prop == 'parent':
            cached_list = []
            for gui in self._list_guis():
                if self._match_name_to_acc(window_name, gui):
                    for name, obj, obj_index in self._appmap_pairs(gui):
                        if name == object_name:
                            for pname, pobj in cached_list:
                                if obj in pobj: # avoid double link issues
                                    return pname
                            _parent = self._ldtpize_accessible(obj.parent)
                            return '%s%s' % (_parent[0], _parent[1])
                        cached_list.insert(0, (name, obj))

            raise LdtpServerException(
                'Unable to find object name in application map')
        elif prop == 'class':
            obj = self._get_object(window_name, object_name)
            return obj.getRoleName().replace(' ', '_')
        elif prop == 'children':
            children = []
            obj = self._get_object(window_name, object_name)
            for gui in self._list_guis():
                if self._match_name_to_acc(window_name, gui):
                    for name, child, obj_index in self._appmap_pairs(gui):
                        if child in obj:
                            children.append(name)
                    break
            return ' '.join(children)

        raise LdtpServerException('Unknown property "%s" in %s' % \
                                      (prop, object_name))

    def getchild(self, window_name, child_name='', role='', first=False):
        '''
        Gets the list of object available in the window, which matches 
        component name or role name or both.
        
        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param child_name: Child name to search for.
        @type child_name: string
        @param role: role name to search for, or an empty string for wildcard.
        @type role: string

        @return: list of matched children names
        @rtype: list
        '''
        matches = []
        for gui in self._list_guis():
            if self._match_name_to_acc(window_name, gui):
                for name, obj, obj_index in self._appmap_pairs(gui):
                    if child_name and role:
                        if obj.getRoleName() == role and \
                                (child_name == name or \
                                     self._match_name_to_acc(child_name, obj)):
                            matches.append(name)
                    elif role:
                        if obj.getRoleName() == role:
                            matches.append(name)
                    elif child_name:
                        if child_name == name or \
                                self._match_name_to_acc(child_name, obj):
                            matches.append(name)

                    #print matches, first
                    if matches and first:
                        # Return once we have a match
                        return matches
                
        if not matches:
            raise LdtpServerException('Could not find a child.')

        return matches

    def remap(self, window_name):
        '''
        For backwards compatability, does not do anything since we are entirely
        dynamic.

        @param window_name: Window name to look for, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string

        @return: 1
        @rtype: integer
        '''
        return 1

    def wait(self, timeout=5):
        '''
        Wait a given amount of seconds.

        @param timeout: Wait timeout in seconds
        @type timeout: integer

        @return: 1
        @rtype: integer
        '''
        waiter = NullWaiter(1, timeout)

        return waiter.run()

    def getstatusbartext(self, window_name, object_name):
        '''
        Get text value
        
        @param window_name: Window name to type in, either full name,
        LDTP's name convention, or a Unix glob.
        @type window_name: string
        @param object_name: Object name to type in, either full name,
        LDTP's name convention, or a Unix glob. 
        @type object_name: string

        @return: text on success.
        @rtype: string
        '''
        return self.gettextvalue(window_name, object_name)

    def setlocale(self, locale_str):
        '''
        Set the locale to the given value.

        @param locale_str: locale to set to.
        @type locale_str: string

        @return: 1
        @rtype: integer
        '''
        locale.setlocale(locale.LC_ALL, locale_str)
        return 1

    def getwindowsize (self, window_name):
        '''
        Get window size.
        
        @param window_name: Window name to get size of.
        @type window_name: string

        @return: list of dimensions [x, y, w, h]
        @rtype: list
        '''
        obj_list = []
        for gui in self._list_guis():
            if self._match_name_to_acc(window_name, gui):
                size = self._get_size(gui)
                return [size.x, size.y, size.width, size.height]

        raise LdtpServerException('Window does not exist')
