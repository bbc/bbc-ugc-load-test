#!/bin/bash

EXCLUSION=("Engine.scala" "IDEPathHelper.scala" "Recorder.scala")
readarray -t files < <(find ../ugc/src/test/scala/uk/co/bbc/ugc/loadtest  -maxdepth 1 -type f  -printf '%P\n')

let i=1
for file in "${files[@]}"; do
    if [[ ! " ${EXCLUSION[@]} " =~ " ${file} " ]]; then
        # whatever you want to do when arr doesn't contain value
        cmd="cp ../ugc/src/test/scala/uk/co/bbc/ugc/loadtest/${file} ec2-package/scenarios/ugc/${file}"
        $cmd
    fi
done
