#!/bin/bash
## Simple shell script that reboots the bot if it crashes
until python3 discordpy.py; do
        echo $(date +%H:%M:%S_%Y-%m-%d) "CRASH"
        sleep 1
done

