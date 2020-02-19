#!/user/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Armink, <armink.ztl@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0
#
# Change Logs:
# Date           Author       Notes
# 2020-01-25     armink       the first version
#
import os
import sys

import qemu_runner

if __name__ == '__main__':

    # test code
    os.environ['PATH'] += ';D:/Program/RTT/env/tools/qemu/qemu32'
    sys.argv = ['qemu_runner.py',
                '--elf', 'D:/Program/RTT/EasyFlashAutoTestBSP/Debug/rtthread.elf',
                '--sd', 'D:/Program/RTT/EasyFlashAutoTestBSP/sd.bin']
    qemu_runner.main()

    # runner = QemuRunner('D:/Program/RTT/rt-thread/bsp/qemu-vexpress-a9/Debug/rtthread.elf', 'D:/Program/RTT/rt-thread/bsp/qemu-vexpress-a9/sd.bin', 5)
    # if not runner.run():
    #     exit(-1)


