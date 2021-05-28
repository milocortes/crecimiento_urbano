#!/bin/bash

YELLOW='\033[0;33m'
NC='\033[0m' # No Color


cd source
python get_agebs.py "$1"
python distancias_agebs.py "$1"

echo "--------------------------------------------------------------------------------"
printf "${YELLOW}Los datos fueron generados{NC}\n"
echo "--------------------------------------------------------------------------------"
exit 1
