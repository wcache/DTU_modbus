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

import _thread
from usr.modules.logging import getLogger
from usr.modules.common import Observable, CloudObserver


log = getLogger(__name__)


class RemoteSubscribe(CloudObserver):
    """This class is for distribute cloud downlink messages"""
    def __init__(self):
        self.__executor = None
        self.__ota_executor = None

    def __raw_data(self, *args, **kwargs):
        """Handle cloud transparent data transmission."""
        return self.__executor.downlink_main(*args, **kwargs) if self.__executor else False

    def __query(self, *args, **kwargs):
        """Handle cloud object model quering message"""
        return self.__executor.event_query(*args, **kwargs) if self.__executor else False

    def __ota_plain(self, *args, **kwargs):
        """Handle cloud OTA plain"""
        return self.__ota_executor.event_ota_plain(*args, **kwargs) if self.__ota_executor else False

    def __thread_execute(self, option_fun, opt_args, opt_kwargs):
        return option_fun(*opt_args, **opt_kwargs)

    def add_executor(self, executor, executor_id):
        """Add cloud downlink messages executor"""
        if executor:
            if executor_id == 1:
                self.__executor = executor
                return True
            elif executor_id == 2:
                self.__ota_executor = executor
                return True
        return False

    def execute(self, observable, *args, **kwargs):
        """Get cloud downlink messages from cloud.
        1. observable: Cloud Iot Object.
        2. args[1]: Cloud DownLink Data Type.
        2.1 query: Query Cloud Object Model.
        2.2 ota_plain: OTA Plain Info.
        2.3 raw_data: Passthrough Data.
        3. args[2]: Cloud DownLink Data(List Or Dict).
        """
        opt_attr = "__" + args[1]
        opt_args = args[2] if not isinstance(args[2], dict) else ()
        opt_kwargs = args[2] if isinstance(args[2], dict) else {}

        if hasattr(self, opt_attr):
            option_fun = getattr(self, opt_attr)
            _thread.start_new_thread(self.__thread_execute, (option_fun, opt_args, opt_kwargs))
        else:
            log.error("RemoteSubscribe Has No Attribute [%s]." % opt_attr)


class RemotePublish(Observable):
    """This class is for post data to cloud"""
    def __init__(self):
        """
        cloud:
            CloudIot Object
        """
        super().__init__()
        self.__cloud = None

    def __cloud_conn(self, enforce=False):
        """Cloud connect"""
        return self.__cloud.init(enforce=enforce) if self.__cloud else False

    def __cloud_post(self, data, topic_id):
        """Cloud publish object model data"""
        log.debug("cloud post data: {},{}".format(topic_id, data))
        try:
            return self.__cloud.through_post_data(data, topic_id) if self.__cloud else False
        except Exception as e:
            log.error("cloud post fault:", str(e))

    def add_cloud(self, cloud):
        """Add Cloud object"""
        if hasattr(cloud, "init") and \
                hasattr(cloud, "post_data") and \
                hasattr(cloud, "ota_request") and \
                hasattr(cloud, "ota_action"):
            self.__cloud = cloud
            return True
        return False

    def cloud_ota_check(self):
        """Check ota plain"""
        return self.__cloud.ota_request() if self.__cloud else False

    def cloud_ota_action(self, action=1, module=None):
        """Confirm ota upgrade"""
        return self.__cloud.ota_action(action, module) if self.__cloud else False

    def cloud_device_report(self):
        """Device & project version report"""
        return self.__cloud.device_report() if self.__cloud else False

    def post_data(self, data, topic_id):
        res = True
        if self.__cloud_conn():
            if not self.__cloud_post(data, topic_id):
                if self.__cloud_conn(enforce=True):
                    if not self.__cloud_post(data, topic_id):
                        res = False
                else:
                    log.error("Cloud Connect Failed.")
                    res = False
        else:
            log.error("Cloud Connect Failed.")
            res = False

        return res
