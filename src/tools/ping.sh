#!/usr/bin/env bash

host=$1
ping -c 1 $host | grep time | awk -F= '{print $4}' | sed -e 's/ ms//g'
