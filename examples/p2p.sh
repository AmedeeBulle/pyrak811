#!/bin/bash
# Simple demo of the RAK811 in P2P mode using the CLI interface
# 
# This simple script sends random packets at random interval and
# listen the rest of the time.
#
# Start this script on 2 or more nodes an observe the packets flowing.
#
# Copyright 2019 Philippe Vanhaesendonck
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

# Exit on errors
set -e

# Send packet every P2P_BASE + (0..P2P_RANDOM) seconds
P2P_BASE=30
P2P_RANDOM=60

# Magic key to recognize our messages
P2P_MAGIC="cafe"

# Reset the module and set mode to P2P
rak811 -v hard-reset
rak811 -v mode LoRaP2P

# Set the RF configuration
# - Avoid LoRaWan channels (You will get quite a lot of spurious packets!)
# - Respect local regulation (frequency, power, duty cycle)
rak811 -v rf-config sf=7 freq=869.800 pwr=16
# Display RF config
rak811 -v rf-config

# Enter the send/recieve loop
COUNTER=0
while true
do
  # Calculate next message send timestamp
  NOW=$(date +%s)
  NEXT_MESSAGE=$(( NOW + P2P_BASE + ( RANDOM % P2P_RANDOM ) ))
  # Set module in receive mode
  rak811 -v rxc
  while [ $(date +%s) -lt ${NEXT_MESSAGE} ]
  do
	# Remaining time until next message
  	NOW=$(date +%s)
	REMAIN=$(( NEXT_MESSAGE - NOW ))
	echo "Waiting on message for ${REMAIN} seconds"
	MESSAGE=$(rak811 -v rx-get ${REMAIN})
	if echo "${MESSAGE}" | grep -q ${P2P_MAGIC}
	then
	  echo "Received valid message:"
	  echo "${MESSAGE}"
	elif echo "${MESSAGE}" | grep -q Data
	then
	  echo "Got foreign message"
	else
	  echo "${MESSAGE}"
	fi
  done
  # Exit receive mode
  rak811 -v rx-stop
  # Send a message
  COUNTER=$(( COUNTER + 1 ))
  MESSAGE=$(printf '%s%08x' ${P2P_MAGIC} ${COUNTER})
  rak811 -v txc --binary ${MESSAGE}
done
