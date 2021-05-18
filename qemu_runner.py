#!/user/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Armink, <armink.ztl@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0
#
# Change Logs:
# Date           Author       Notes
# 2020-01-26     armink       the first version
#
import argparse
import os
import platform
import signal
import subprocess
import sys
import threading
import logging
import time

from utest import Utest

LOG_LVL = logging.DEBUG
LOG_TAG = 'qemu_runner'
logger = logging.getLogger(LOG_TAG)


class QemuRunner:
    def __init__(self, machine, elf_path, sd_path, delay):
        logging.basicConfig(level=LOG_LVL, format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt=None)
        self.machine = machine
        self.elf_path = elf_path
        self.sd_path = sd_path
        self.delay = delay
        self.env_version = ''
        self.sub_proc = None
        self.log_recorder = None
        self.log_recorder_alive = False
        self.logs = []
        self.logs_lock = threading.Lock()
        self.is_executing = False

    def check_env(self):
        def exec_cmd(cmd):
            text = ''
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            out, err = p.communicate()
            for line in out.splitlines():
                text += str(line, encoding="utf8") + '\r\n'
            return text

        result = exec_cmd('qemu-system-arm --version')
        check_ok = (result.find('version') != -1)
        if check_ok:
            self.env_version = result
        return check_ok

    def run(self):
        if self.check_env():
            logger.info("QEMU environment check OK.")
            logger.debug(self.env_version)
        else:
            logger.error("QEMU environment check FAILED.")
            return
        # starting the new process for running QEMU
        cmd = 'qemu-system-arm -nographic -M {} -kernel {}'.format(self.machine, self.elf_path)
        
        if self.sd_path != "None" :
            cmd = cmd + ' -sd ' + self.sd_path

        if platform.system() == "Windows":
            self.sub_proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0,
                                             creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            self.sub_proc = subprocess.Popen("exec " + cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0,
                                             shell=True)
        event = threading.Event()

        # RT-Thread console log recorder with QEMU process
        def log_recorder_entry():
            with open('rtt_console.log', 'w') as log_file:
                for line in iter(self.sub_proc.stdout.readline, b'\n'):
                    if line:
                        line = str(line, encoding="utf8").replace('\n', '').replace('\r', '')
                        log_file.write(line + '\n')
                        self.logs_lock.acquire()
                        self.logs.append(line)
                        self.logs_lock.release()
                        if self.is_executing and line.find('[ utest    ] finished') != -1:
                            event.set()
                    elif self.log_recorder_alive is False:
                        return

        self.log_recorder_alive = True
        self.log_recorder = threading.Thread(target=log_recorder_entry)
        self.log_recorder.start()

        def exec_utest_cmd(name, timeout):
            self.logs_lock.acquire()
            self.logs.clear()
            self.logs_lock.release()
            self.is_executing = True

            # send command to qemu
            cmb_str = name + '\r\n'
            for s in cmb_str:
                self.sub_proc.stdin.write(bytes(s, encoding='utf8'))
                # delay for wait qemu UART device receive finish
                time.sleep(0.001)
            self.sub_proc.stdin.flush()

            # wait command execute finish
            event.clear()
            signaled = event.wait(timeout=timeout)
            self.is_executing = False

            self.logs_lock.acquire()
            logs = self.logs
            self.logs_lock.release()
            return signaled, logs

        time.sleep(self.delay)
        utest = Utest(exec_utest_cmd)
        success = utest.test_all()
        self.destroy()

        return success

    def destroy(self):
        self.log_recorder_alive = False
        if platform.system() == "Windows":
            # os.kill(self.sub_proc.pid, signal.CTRL_BREAK_EVENT)
            self.sub_proc.kill()
        else:
            self.sub_proc.kill()
            # os.killpg(os.getpgid(self.sub_proc.pid), signal.SIGTERM)
        time.sleep(0.5)
        logger.info("QEMU runner destroy")


def main():
    parser = argparse.ArgumentParser(description='QEMU runner for RT-Thread utest', prog=os.path.basename(sys.argv[0]))
  
    parser.add_argument('--machine',
                        metavar='machine',
                        help='virtualize machine for running QEMU',
                        default="vexpress-a9",
                        type=str,
                        required=False)

    parser.add_argument('--elf',
                        metavar='path',
                        help='elf file path for running QEMU',
                        required=True)

    parser.add_argument('--sd',
                        metavar='path',
                        help='SD filesystem binary file for QEMU',
                        default="None",
                        type=str,
                        required=False)

    parser.add_argument('--delay',
                        metavar='seconds',
                        help='delay some seconds for QEMU running finish',
                        default=5,
                        type=int,
                        required=False)

    args = parser.parse_args()
    runner = QemuRunner(args.machine, args.elf, args.sd, args.delay)
    if not runner.run():
        sys.exit(-1)


if __name__ == '__main__':
    main()
