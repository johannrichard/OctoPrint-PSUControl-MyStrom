# coding=utf-8
from __future__ import absolute_import

__author__ = "Johann Richard <189003+johannrichard@users.noreply.github.com>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2024 Johann Richard, original TPLink PSU plugin Copyright 2021 Shawn Bruce - Released under terms of the AGPLv3 License"

import octoprint.plugin
import json
from struct import unpack
from builtins import bytes
import struct
import requests

class PSUControl_MyStrom(octoprint.plugin.StartupPlugin,
                        octoprint.plugin.RestartNeedingPlugin,
                        octoprint.plugin.TemplatePlugin,
                        octoprint.plugin.SettingsPlugin):

    def __init__(self):
        self.config = dict()

    def get_settings_defaults(self):
        return dict(
            address = '',
            token = ''
        )


    def on_settings_initialized(self):
        self.reload_settings()
        self._baseUrl = "http://{}/".format(self.config['address'])
        if self.config['token']:
            self._logger.debug('Using Token for access control')
            self._tokenHeader = {'Token': self.config['token']}
        else:
            self._tokenHeader = {}


    def reload_settings(self):
        for k, v in self.get_settings_defaults().items():
            if type(v) == str:
                v = self._settings.get([k])
            elif type(v) == int:
                v = self._settings.get_int([k])
            elif type(v) == float:
                v = self._settings.get_float([k])
            elif type(v) == bool:
                v = self._settings.get_boolean([k])

            self.config[k] = v
            self._logger.debug("{}: {}".format(k, v))


    def on_startup(self, host, port):
        psucontrol_helpers = self._plugin_manager.get_helpers("psucontrol")
        if not psucontrol_helpers or 'register_plugin' not in psucontrol_helpers.keys():
            self._logger.warning("The version of PSUControl that is installed does not support plugin registration.")
            return

        self._logger.debug("Registering plugin with PSUControl")
        psucontrol_helpers['register_plugin'](self)

    def change_psu_state(self, state):
        self._logger.debug("Change PSU state to {}".format(state))
        url = "{}/relay".format(self._baseUrl)
        requests.get(url, params = {'state': state }, headers = self._tokenHeader)
            
    def turn_psu_on(self):
        self._logger.debug("Switching PSU On")
        self.change_psu_state(1)


    def turn_psu_off(self):
        self._logger.debug("Switching PSU Off")
        self.change_psu_state(0)


    def get_psu_state(self):
        self._logger.debug("get_psu_state")
        url = "{}/report".format(self._baseUrl)
        
        result = False

        try:
            r = requests.get(url, headers = self._tokenHeader)
            report = r.json()
            self._logger.debug("Report: {}".format(report))
            result = bool(report['relay'])
        except KeyError:
            self._logger.error("Expecting report:relay, got sysinfo={}".format(KeyError))

        return result

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.reload_settings()


    def get_settings_version(self):
        return 1


    def on_settings_migrate(self, target, current=None):
        pass


    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]


    def get_update_information(self):
        return dict(
            psucontrol_mystrom=dict(
                displayName="PSU Control - MyStrom",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="johannrichard",
                repo="OctoPrint-PSUControl-MyStrom",
                current=self._plugin_version,

                # update method: pip w/ dependency links
                pip="https://github.com/johannrichard/OctoPrint-PSUControl-MyStrom/archive/{target_version}.zip"
            )
        )

__plugin_name__ = "PSU Control - MyStrom"
__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PSUControl_MyStrom()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
