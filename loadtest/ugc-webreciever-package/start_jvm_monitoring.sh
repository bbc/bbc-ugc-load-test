#!/bin/bash
set -eux

exec 1>${HOME}/jvm-monitoring.log
exec 2>&1

sudo jcmd > /tmp/foo
declare pid=""
while read pidline ; do
     flag=`echo $pidline|awk '{print match($0,"ugc-web-receiver")}'`;
      if [ $flag -gt 0 ];then
           pidinfo=(${pidline/ / })
           pid=${pidinfo[0]}
      fi
done < /tmp/foo
mkdir -p monitoring
sudo jstat -class $pid 100ms &> monitoring/jvm-monitoring-class.log &
sudo jstat -gccause -h20 -t $pid 100ms &> monitoring/jvm-monitoring-gc.log &
