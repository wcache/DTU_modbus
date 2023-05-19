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
@file      :demo.py
@author    :elian.wang@quectel.com
@brief     :dtu main function
@version   :0.1
@date      :2022-05-18 09:12:37
@copyright :Copyright (c) 2022
"""

import _thread
import modem
import osTimer
from usr.modules.common import Singleton
from usr.modules.mqttIot import MqttIot
from usr.modules.socketIot import Socket

from usr.settings import settings
from usr.modules.serial import Serial
from usr.modules.logging import getLogger
from usr.dtu_transaction import DownlinkTransaction, OtaTransaction, UplinkTransaction
from usr.modules.remote import RemotePublish, RemoteSubscribe
from usr.settings import PROJECT_NAME, PROJECT_VERSION, DEVICE_FIRMWARE_NAME, DEVICE_FIRMWARE_VERSION

log = getLogger(__name__)

_thread.stack_size(8192)


class Dtu(Singleton):
    """Dtu main function call
    """
    def __init__(self):
        self.__ota_timer = osTimer()
        self.__ota_transaction = None

    def __cloud_init(self, protocol):

        if protocol.startswith("mqtt"):
            cloud_config = settings.current_settings.get("mqtt_private_cloud_config")
            client_id = cloud_config["client_id"] if cloud_config.get("client_id") else modem.getDevImei()

            cloud = MqttIot(cloud_config.get("server", None),
                            int(cloud_config.get("qos", 0)),
                            int(cloud_config.get("port", 1883)),
                            cloud_config.get("clean_session"),
                            client_id,
                            cloud_config.get("username"),
                            cloud_config.get("password"),
                            cloud_config.get("publish"),
                            cloud_config.get("subscribe"),
                            cloud_config.get("keep_alive"))
            cloud.init(enforce=True)
            return cloud
        elif protocol.startswith("tcp"):
            cloud_config = settings.current_settings.get("tcp_private_cloud_config")
            cloud = Socket(ip_type=cloud_config.get("ip_type"),
                           keep_alive=cloud_config.get("keep_alive"),
                           domain=cloud_config.get("server"),
                           port=int(cloud_config.get("port")),
                           )
            cloud.init(enforce=True)
            return cloud
        else:
            raise Exception("cloud not supported!")
    
    def __periodic_ota_check(self, args):
        """Periodically check whether cloud have an upgrade plan"""
        self.__ota_transaction.ota_check()

    def start(self):
        """Dtu init flow
        """
        log.info("PROJECT_NAME: %s, PROJECT_VERSION: %s" % (PROJECT_NAME, PROJECT_VERSION))
        log.info("DEVICE_FIRMWARE_NAME: %s, DEVICE_FIRMWARE_VERSION: %s" % (DEVICE_FIRMWARE_NAME, DEVICE_FIRMWARE_VERSION))

        uart_setting = settings.current_settings["uart_config"]

        # Serial initialization
        serial = Serial(int(uart_setting.get("port")),
                        int(uart_setting.get("baudrate")),
                        int(uart_setting.get("databits")),
                        int(uart_setting.get("parity")),
                        int(uart_setting.get("stopbits")),
                        int(uart_setting.get("flowctl")),
                        uart_setting.get("rs485_direction_pin"))

        # Cloud initialization
        cloud = self.__cloud_init(settings.current_settings["system_config"]["cloud"])

        # UplinkTransaction initialization
        up_transaction = UplinkTransaction()
        up_transaction.add_module(serial)

        # DownlinkTransaction initialization
        down_transaction = DownlinkTransaction()
        down_transaction.add_module(serial)
        # OtaTransaction initialization
        ota_transaction = OtaTransaction()

        # RemoteSubscribe initialization
        remote_sub = RemoteSubscribe()
        remote_sub.add_executor(down_transaction, 1)
        remote_sub.add_executor(ota_transaction, 2)
        cloud.addObserver(remote_sub)

        # RemotePublish initialization
        remote_pub = RemotePublish()
        remote_pub.add_cloud(cloud)
        up_transaction.add_module(remote_pub)
        ota_transaction.add_module(remote_pub)
            
        # Send module release information to cloud. After receiving this information, 
        # the cloud server checks whether to upgrade modules
        ota_transaction.ota_check()
        # Periodically check whether cloud have an upgrade plan
        self.__ota_transaction = ota_transaction
        self.__ota_timer.start(1000 * 600, 1, self.__periodic_ota_check)

        # Start uplink transaction
        try:
            up_transaction.start_uplink_main()
        except:
            raise self.Error(self.error_map[self.ErrCode.ESYS])


if __name__ == "__main__":
    dtu = Dtu()
    dtu.start()

