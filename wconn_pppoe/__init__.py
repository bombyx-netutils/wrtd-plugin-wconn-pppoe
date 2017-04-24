#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import time
import fcntl
import socket
import struct
import logging
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
        _Util.setInterfaceUpDown(self.cfg["interface"], False)

    def get_out_interface(self):
        return "wrt-ppp-wan"

    def interface_appear(self, ifname):
        if ifname != self.cfg["interface"]:
            return False

        assert self.proc is None
        _Util.setInterfaceUpDown(self.cfg["interface"], True)
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


class _Util:

    @staticmethod
    def setInterfaceUpDown(ifname, upOrDown):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            ifreq = struct.pack("16sh", ifname.encode("ascii"), 0)
            ret = fcntl.ioctl(s.fileno(), 0x8913, ifreq)
            flags = struct.unpack("16sh", ret)[1]                   # SIOCGIFFLAGS

            if upOrDown:
                flags |= 0x1
            else:
                flags &= ~0x1

            ifreq = struct.pack("16sh", ifname.encode("ascii"), flags)
            fcntl.ioctl(s.fileno(), 0x8914, ifreq)                  # SIOCSIFFLAGS
        finally:
            s.close()
