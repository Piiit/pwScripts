#!/bin/sh

sudo rmmod iwlmvm iwlwifi && sudo modprobe iwlwifi && exit 0

exit 1
