# Copyright (c) Quectel Wireless Solution, Co., Ltd.All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file      :dtu_transaction.py
@author    :elian.wang@quectel.com
@brief     :Dtu transaction related interfaces
@version   :0.1
@date      :2022-08-04 11:33:23
@copyright :Copyright (c) 2022
"""


import log
import usys
import ujson
import utime
import _thread
from usr.modules.common import Singleton
from usr.modules.logging import getLogger
from usr.modules.serial import Serial
from usr.modules.remote import RemotePublish
from usr.settings import settings
from usr.settings import PROJECT_NAME, PROJECT_VERSION, DEVICE_FIRMWARE_NAME, DEVICE_FIRMWARE_VERSION

log = getLogger(__name__)


class DownlinkTransaction(Singleton):
    """Data downlink:Receive data from the cloud and send it to serial
    """
    def __init__(self):
        self.__serial = None

    def add_module(self, module, callback=None):
        if isinstance(module, Serial):
            self.__serial = module
            return True
        return False

    def __get_sub_topic_id(self, topic):
        """Locate the topic id from the cloud setting

        Args:
            topic (str): topic in mqtt protocol 

        Returns:
            str: topic id
        """
        cloud_name = settings.current_settings["system_config"]["cloud"]
        cloud_config = settings.current_settings.get(cloud_name + "_config")
        if cloud_config == None:
            raise Exception("Cloud config parameter error")
        for k, v in cloud_config.get("subscribe").items():
            if topic == v:
                return k

    def downlink_main(self, *args, **kwargs):
        """Parsing cloud data, send to serial port

        Args:
            args (tuple): Not use
            kwargs (dict): The data received by the cloud,contains topic and data
        """
        # Get mqtt protocol message id
        if isinstance(kwargs["data"], bytes):
            data = kwargs["data"].decode()
        elif isinstance(kwargs["data"], dict):
            data = ujson.dumps(kwargs["data"])
        elif isinstance(kwargs["data"], str):
            data = kwargs["data"]
        else:
            data = str(kwargs["data"])

        self.__serial.write(data)


class OtaTransaction(Singleton):
    """Device firmware OTA and project file OTA transaction
    """
    def __init__(self):
        self.__remote_pub = None

    def __remote_ota_check(self):
        if not self.__remote_pub:
            raise TypeError("self.__remote_pub is not registered.")
        return self.__remote_pub.cloud_ota_check()

    def __remote_ota_action(self, action, module):
        if not self.__remote_pub:
            raise TypeError("self.__remote_pub is not registered.")
        return self.__remote_pub.cloud_ota_action(action, module)

    def __remote_device_report(self):
        if not self.__remote_pub:
            raise TypeError("self.__remote_pub is not registered.")
        return self.__remote_pub.cloud_device_report()

    def add_module(self, module, callback=None):
        if isinstance(module, RemotePublish):
            self.__remote_pub = module
            return True
        return False

    def ota_check(self):
        """After powering on, release module information and check for update
        """
        try:
            if settings.current_settings["system_config"]["base_function"]["fota"]:
                self.__remote_ota_check()
                self.__remote_device_report()
                utime.sleep(1)
        except Exception as e:
            log.error("periodic_ota_check fault", e)

    def event_ota_plain(self, *args, **kwargs):
        """Determine the parameters and perform the OTA plan

        Args:
            args (tuple): Ota parameters sent from the cloud
            kwargs (dict): None
        """
        log.debug("ota_plain args: %s, kwargs: %s" % (str(args), str(kwargs)))
        # TODO: 此处检查是否需要执行升级计划
        self.__remote_ota_action(action=1, module=None)  # 通过RemotePublish执行器调用云对象启动OTA升级


class UplinkTransaction(Singleton):
    """Data uplink: read data from the serial and send it to cloud
    """
    def __init__(self):
        self.__remote_pub = None
        self.__serial = None
        self.__parse_data = ""
        self.__send_to_cloud_data = []

    def __remote_post_data(self, data=None, topic_id=None):
        if not self.__remote_pub:
            raise TypeError("self.__remote_pub is not registered.")
        return self.__remote_pub.post_data(data, topic_id)

    def __parse(self):
        """Recursive parse uart data
        """
        self.__send_to_cloud_data.append(("0", self.__parse_data))
        self.__parse_data = ""
        return

    def __mqtt_protocol_uart_data_parse(self, data):
        """When cloud is mqtt protocol, parse uart data.

        Args:
            data (str): Data read from uart

        Returns:
            list: topic_id and data tuple list
        """
        self.__parse_data += data
        self.__send_to_cloud_data = []
        try:
            self.__parse()
        except Exception as e:
            log.debug("parse error: {}".format(str(e)))
            self.__parse_data = ""
            self.__send_to_cloud_data = []

    def __send_mqtt_data(self, data):
        for send_data in data:
            self.__remote_post_data(data=send_data[1], topic_id=send_data[0])
            utime.sleep_ms(10)

    def __uplink_data(self, data):
        """Parsing uart data, send data to cloud

        Args:
            data (bytes): data read from uart
        """
        try:
            self.__mqtt_protocol_uart_data_parse(data)
            if len(self.__send_to_cloud_data) != 0:
                log.debug('send to cloud data: ', self.__send_to_cloud_data)
                _thread.start_new_thread(self.__send_mqtt_data, (self.__send_to_cloud_data,))
        except Exception as e:
            log.error(e)

    def add_module(self, module, callback=None):
        if isinstance(module, RemotePublish):
            self.__remote_pub = module
            return True
        elif isinstance(module, Serial):
            self.__serial = module
            return True
        return False

    def start_uplink_main(self):
        log.info('set up_transaction stop flag to false.')
        _thread.start_new_thread(self.uplink_main, ())
        log.info('start new up_transaction uplink main thread.')

    def uplink_main(self):
        """Read serial data, parse and upload to the cloud
        """
        # >>> 数据透传
        while True:
            # Read uart data
            read_byte = self.__serial.read(nbytes=1024, timeout=100)
            if read_byte:
                try:
                    self.__uplink_data(read_byte)
                except Exception as e:
                    usys.print_exception(e)
                    log.error("Parse uart data error: %s" % e)
        # <<<
