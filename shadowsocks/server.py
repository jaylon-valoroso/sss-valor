#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 clowwindy
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import, division, print_function, \
    with_statement

import sys
import os
import logging
import signal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))
from shadowsocks import shell, daemon, eventloop, tcprelay, udprelay, \
    asyncdns, manager, utils

def main():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-4s:%(filename)s %(lineno)d %(funcName)s %(message)s')
    logging.info("main exec...")

    # a = "123456"
    # b = []
    # b.append(a)
    #
    # logging.info("a:%s" % a[2:])
    # logging.info("b:%s" % type(b))
    #
    # s = utils.encode(b[0])
    # logging.info(s)
    # b = utils.decode(s)
    # logging.info(b)

    shell.check_python()

    config = shell.get_config(False)

    daemon.daemon_exec(config)

    if config['port_password']:
        if config['password']:
            logging.warn('warning: port_password should not be used with '
                         'server_port and password. server_port and password '
                         'will be ignored')
    else:
        config['port_password'] = {}
        server_port = config['server_port']
        if type(server_port) == list:
            for a_server_port in server_port:
                logging.info('a_server_port:%s' % str(a_server_port))
                config['port_password'][a_server_port] = config['password']
        else:
            logging.info('server_port:%s' % str(server_port))
            config['port_password'][str(server_port)] = config['password']

    if config.get('manager_address', 0):
        logging.info('entering manager mode')
        manager.run(config)
        return

    tcp_servers = []
    udp_servers = []

    if 'dns_server' in config:  # allow override settings in resolv.conf
        logging.info("dns_server in config")
        dns_resolver = asyncdns.DNSResolver(config['dns_server'],
                                            config['prefer_ipv6'])
    else:
        logging.info("dns_server not in config")
        dns_resolver = asyncdns.DNSResolver(prefer_ipv6=config['prefer_ipv6'])

    port_password = config['port_password']
    logging.info("port_password:%s" % str(port_password))

    del config['port_password']
    for port, password in port_password.items():
        a_config = config.copy()
        a_config['server_port'] = int(port)
        a_config['password'] = password
        logging.info("starting server at %s:%d" %
                     (a_config['server'], int(port)))
        tcp_servers.append(tcprelay.TCPRelay(a_config, dns_resolver, False))
        udp_servers.append(udprelay.UDPRelay(a_config, dns_resolver, False))

    logging.info('config type:' + str(type(config)))

    def run_server():
        logging.info("run_server enters")

        def child_handler(signum, _):
            logging.warn('received SIGQUIT, doing graceful shutting down..')
            list(map(lambda s: s.close(next_tick=True),
                     tcp_servers + udp_servers))
        signal.signal(getattr(signal, 'SIGQUIT', signal.SIGTERM),
                      child_handler)

        def int_handler(signum, _):
            sys.exit(1)
        signal.signal(signal.SIGINT, int_handler)

        try:
            loop = eventloop.EventLoop()
            dns_resolver.add_to_loop(loop)
            list(map(lambda s: s.add_to_loop(loop), tcp_servers + udp_servers))

            daemon.set_user(config.get('user', None))
            loop.run()
        except Exception as e:
            shell.print_exception(e)
            sys.exit(1)

    if int(config['workers']) > 1:
        if os.name == 'posix':
            children = []
            is_child = False
            for i in range(0, int(config['workers'])):
                r = os.fork()
                if r == 0:
                    logging.info('worker started')
                    is_child = True
                    logging.info("run_server enters - 3")
                    run_server()
                    break
                else:
                    children.append(r)
            if not is_child:
                def handler(signum, _):
                    for pid in children:
                        try:
                            os.kill(pid, signum)
                            os.waitpid(pid, 0)
                        except OSError:  # child may already exited
                            pass
                    sys.exit()
                signal.signal(signal.SIGTERM, handler)
                signal.signal(signal.SIGQUIT, handler)
                signal.signal(signal.SIGINT, handler)

                # master
                for a_tcp_server in tcp_servers:
                    a_tcp_server.close()
                for a_udp_server in udp_servers:
                    a_udp_server.close()
                dns_resolver.close()

                for child in children:
                    os.waitpid(child, 0)
        else:
            logging.warn('worker is only available on Unix/Linux')
            logging.info("call run_server - 1")
            run_server()
    else:
        logging.info("call run_server enters - 2")
        run_server()


if __name__ == '__main__':
    main()
