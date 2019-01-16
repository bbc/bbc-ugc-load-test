#!/usr/bin/env bash
#!/bin/bash
set -e

sudo jcmd > /tmp/foo-1
declare pid=""
while read pidline ; do
     flag=`echo $pidline|awk '{print match($0,"ugc-web-receiver")}'`;
      if [ $flag -gt 0 ];then
           pidinfo=(${pidline/ / })
           pid=${pidinfo[0]}
      fi
done < /tmp/foo-1

ps -p $pid -o stime
