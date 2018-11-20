#!/usr/bin/env bash

exec 1>${HOME}/jvm-monitoring-fetch-log.log
exec 2>&1
sudo pkill jstat
sudo tar -czvf monitoring.tar.gz monitoring