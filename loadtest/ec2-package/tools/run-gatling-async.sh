#!/bin/bash
TEST_ID=$1
shift
NUM_INSTANCES=$1
shift

set -eu

echo "This script is used to run the gatling scenarios."

exec 1>${HOME}/normal.log
exec 2>&1

LOG_DIR="/var/log/ltctl/gatling"

echo "This is the test id $TEST_ID"
echo "This is the num instances $NUM_INSTANCES"

# Min/max JVM heap size should be 60% of available system memory
JVM_HEAP=$(grep MemTotal /proc/meminfo | awk '{ print int(($2 / 100) * 60)}')

# Size of the JVM heap for the young generation should be half total heap
JVM_YOUNG=$(( JVM_HEAP / 2 ))

GAT_OPTS=""
# Supress java.net.ConnectException: handshake alert:  unrecognized_name
GAT_OPTS+=" -Djsse.enableSNIExtension=false"
GAT_OPTS+=" -DnumEC2Instances=${NUM_INSTANCES}"
# Stop Java's weird in memory DNS caching which prevents round robin DNS load
# balancing (that the ELBs use). Note this doesn't disable OS DNS cachine.
GAT_OPTS+=" -Dsun.net.inetaddr.ttl=0"
GAT_OPTS+=" -DfailedReqLog=/var/log/ltctl/log/failed_req.${TEST_ID}.log"

cd ~/gatling

JAVA_OPTS=" -Xms${JVM_HEAP}k -Xmx${JVM_HEAP}k -Xmn${JVM_YOUNG}k ${GAT_OPTS}" \
./bin/gatling.sh -nr \
-rf "${LOG_DIR}/" \
-on "$TEST_ID" \
"$@"

echo "------------------------------------ waiting for tests to complete -----------"


cur_time=$(date --utc +%FT%TZ)
aws cloudwatch put-metric-data --region eu-west-2 --namespace UGC_GATLING_SIMULATION --metric-name "RESULTS" --timestamp $cur_time --value 1


