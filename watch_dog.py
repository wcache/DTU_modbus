import _thread
import time

import utime
from usr.modules.common import Singleton
from usr.modules.logging import getLogger

logger = getLogger(__name__)


class AutoLock(object):

    def __init__(self):
        self.__lock = _thread.allocate_lock()

    def __enter__(self):
        self.__lock.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__lock.release()


class Item(object):

    def __init__(self, thread_id, func, args=()):
        self.thread_id = thread_id
        self.func = func
        self.args = args
        self.update_time = None
        self.lock = AutoLock()
        self.update()

    def update(self):
        with self.lock:
            self.update_time = utime.time()

    def __str__(self):
        return "pass {}:{}".format(self.thread_id, self.func)


class WatchDog(Singleton):
    INTERVAL_SECONDS = 20

    def __init__(self):
        self.lock = AutoLock()
        self.items = []
        self.thread = _thread.start_new_thread(self.start, ())

    def start(self):
        while True:
            cur_time = utime.time()

            need_remove = []
            need_append = []
            for tmp in self.items:
                if tmp.update_time+self.INTERVAL_SECONDS < cur_time:
                    logger.info('out of time for {}.'.format(tmp.thread_id))
                    self.stop_thread(tmp)
                    need_remove.append(tmp)
                    new_thread_id = self.start_new_thread(tmp)
                    self.add_thread(new_thread_id, tmp.func, tmp.args)

            for remove_item in need_remove:
                self.items.remove(remove_item)

            for append_item in need_append:
                self.items.append(append_item)

            logger.debug('check at {}.'.format(cur_time))
            logger.debug('items: ', self.items)
            utime.sleep(self.INTERVAL_SECONDS)

    def start_new_thread(self, tmp):
        return _thread.start_new_thread(tmp.func, tmp.args)

    def stop_thread(self, tmp):
        try:
            _thread.stop_thread(tmp.thread_id)
        except Exception:
            pass

    def feed(self, thread_id):
        with self.lock:
            for tmp in self.items:
                if tmp.thread_id == thread_id:
                    tmp.update()

    def add_thread(self, thread_id, func, args):
        item = Item(thread_id, func, args)
        item.update()
        self.items.append(item)


dog = WatchDog()


if __name__ == '__main__':
    def work_fun(p1):
        for i in range(5):
            logger.debug('{} feed dog at {}, index {}'.format(_thread.get_ident(), utime.time(), i))
            dog.feed(_thread.get_ident())  # 线程内部需定时喂狗, 参数是当前线程id
            time.sleep(10)
        logger.debug('{} finished!'.format(_thread.get_ident()))

    args = ('hello',)  # 线程执行函数参数
    t1_id = _thread.start_new_thread(work_fun, args)
    dog.add_thread(t1_id, work_fun, args)  # 看门狗添加监控线程，每20s检测线程状态。如果20s内线程状态未更新，则认为线程异常退出，重新拉起线程