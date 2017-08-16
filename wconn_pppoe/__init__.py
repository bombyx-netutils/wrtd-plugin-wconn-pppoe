#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import time
import logging
import pyroute2
import netifaces
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
    return _PluginObject(name)


class _PluginObject:

    def __init__(self, name):
        self.name = name
        if self.name == "generic-pppoe":
            self.bandwidth = None
        elif self.name == "cn-bj-gwbn-4m":
            self.bandwidth = 4 * 1024 / 8              # KB/s
        elif self.name == "cn-bj-gwbn-50m":
            self.bandwidth = 50 * 1024 / 8             # KB/s
        elif self.name == "cn-bj-gwbn-70m":
            self.bandwidth = 70 * 1024 / 8             # KB/s
        elif self.name == "cn-bj-gwbn-100m":
            self.bandwidth = 100 * 1024 / 8            # KB/s
        else:
            assert False

    def init2(self, cfg, tmpDir, ownResolvConf, upCallback, downCallback):
        self.cfg = cfg
        self.tmpDir = tmpDir
        self.ownResolvConf = ownResolvConf
        self.upCallback = upCallback
        self.downCallback = downCallback
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__ + "." + self.name)
        self.proc = None

    def get_interface(self):
        return "wrt-ppp-wan"

    def start(self):
        self.logger.info("Started.")

    def stop(self):
        if self.proc is not None:
            self.proc.terminate()
            self.proc.join()
            self.proc = None
            with pyroute2.IPRoute() as ip:
                idx = ip.link_lookup(ifname=self.cfg["interface"])[0]
                ip.link("set", index=idx, state="down")
            self.downCallback()
            self.logger.info("Interface \"%s\" unmanaged." % (self.cfg["interface"]))
        self.logger.info("Stopped.")

    def is_connected(self):
        return self.proc is not None

    def get_ip(self):
        assert self.is_connected()
        return netifaces.ifaddresses("wrt-ppp-wan")[netifaces.AF_INET][0]["addr"]

    def get_netmask(self):
        assert self.is_connected()
        return netifaces.ifaddresses("wrt-ppp-wan")[netifaces.AF_INET][0]["netmask"]

    def get_extra_prefix_list(self):
        assert self.is_connected()
        return []

    def get_business_attributes(self):
        assert self.is_connected()
        return {
            "bandwidth": self.bandwidth,
        }

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

        self.logger.info("Interface \"%s\" managed." % (self.cfg["interface"]))
        self.upCallback()
        return True

    def interface_disappear(self, ifname):
        assert ifname == self.cfg["interface"]
        if self.proc is not None:
            self.proc.terminate()
            self.proc.wait()
            self.proc = None
            self.downCallback()
            self.logger.info("Interface \"%s\" unmanaged." % (self.cfg["interface"]))
