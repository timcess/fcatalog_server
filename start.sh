#!/bin/bash

exec sudo -H -u ufcatalog /home/ufcatalog/ufcatalog_env/bin/python \
                /home/ufcatalog/bin/fcatalog_server 0.0.0.0 1337
