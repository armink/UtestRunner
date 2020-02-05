#!/user/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020, Armink, <armink.ztl@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0
#
# Change Logs:
# Date           Author       Notes
# 2020-01-27     armink       the first version
#

import collections
import logging
import re

LOG_LVL = logging.DEBUG
LOG_TAG = 'utest'
logger = logging.getLogger(LOG_TAG)


class Utest:

    def __init__(self, exec_cmd):
        self.exec_cmd = exec_cmd
        self.testcases = collections.OrderedDict()
        signaled, tc_list_log = self.exec_cmd('utest_list', 1)
        for line in tc_list_log:
            if line.find('[testcase name]') != -1:
                # get the testcase name
                reg1 = re.compile(r'.*?\[testcase name\]:(.*?)[;]', re.S | re.M)
                tc_name = re.findall(reg1, line)[0]
                # get the testcase timeout
                reg2 = re.compile(r'\[run timeout\]:[0-9]+')
                match = reg2.search(line)
                timeout_str = match.group(0).replace(r'[run timeout]:', '')
                tc_timeout = int(timeout_str)
                # add to list
                self.testcases[tc_name] = tc_timeout
                # self.testcases.append(testcase)
                logger.debug('Get a testcase: ' + tc_name + ', timeout: ' + str(tc_timeout))

    def test(self, name):
        logger.info('Start test: ' + name)
        signaled, tc_list_log = self.exec_cmd('utest_run ' + name, self.testcases[name])
        for line in tc_list_log:
            if line.find('[ result   ] testcase (' + name + ')') != -1:
                if (line.find('PASSED')) != -1:
                    logger.info('Test passed')
                    return True
                else:
                    logger.error('Test failed')
                    return False

    def test_all(self):
        success = True
        for k, v in self.testcases.items():
            if not self.test(k):
                success = False
        return success
