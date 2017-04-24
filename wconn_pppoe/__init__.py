#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import time
import logging
import pyroute2
import subprocess


def get_plugin_list():
    return [
        "generic-pppoe",
        "cn-bj-gwbn-4m",             # 中国北京长城宽带4M
        "cn-bj-gwbn-50m",            # 中国北京长城宽带50M
        "cn-bj-gwbn-70m",            # 中国北京长城宽带70M
        "cn-bj-gwbn-100m",           # 中国北京长城宽带100M
    ]


def get_plugin(name):
    if name == "generic-pppoe":
        return _PluginObject(None)
    if name == "cn-bj-gwbn-4m":
        return _PluginObject(4 * 1024 * 1024 / 8)
    if name == "cn-bj-gwbn-50m":
        return _PluginObject(50 * 1024 * 1024 / 8)
    if name == "cn-bj-gwbn-70m":
        return _PluginObject(70 * 1024 * 1024 / 8)
    if name == "cn-bj-gwbn-100m":
        return _PluginObject(100 * 1024 * 1024 / 8)
    else:
        assert False


class _PluginObject:

    def __init__(self, bandwidth):
        self.bandwidth = bandwidth              # byte/s

    def init2(self, cfg, tmpDir, ownResolvConf):
        self.cfg = cfg
        self.tmpDir = tmpDir
        self.ownResolvConf = ownResolvConf
        self.proc = None

    def start(self):
        pass

    def stop(self):
        if self.proc is not None:
            self.proc.terminate()
            self.proc.join()
            self.proc = None
        with pyroute2.IPRoute() as ip:
            idx = ip.link_lookup(ifname=self.cfg["interface"])[0]
            ip.link("set", index=idx, state="down")

    def get_out_interface(self):
        return "wrt-ppp-wan"

    def interface_appear(self, ifname):
        if ifname != self.cfg["interface"]:
            return False

        assert self.proc is None

        with pyroute2.IPRoute() as ip:
            idx = ip.link_lookup(ifname=self.cfg["interface"])[0]
            ip.link("set", index=idx, state="up")

        self.proc = subprocess.Popen([
            "/usr/bin/python3",
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "subproc_pppoe.py"),
            self.tmpDir,
            self.ownResolvConf,
            self.cfg["interface"],
            self.cfg.get("username", ""),
            self.cfg.get("password", ""),
        ])

        while not os.path.exists(os.path.join(self.tmpDir, "etc-ppp", "resolv.conf")):
            time.sleep(1.0)

        logging.info("WAN: Internet interface \"%s\" is managed." % (self.get_out_interface()))
        return True

    def interface_disappear(self, ifname):
        assert ifname == self.cfg["interface"]
        if self.proc is not None:
            self.proc.terminate()
            self.proc.wait()
            self.proc = None
