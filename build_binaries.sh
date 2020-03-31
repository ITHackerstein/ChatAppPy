#!/bin/bash

if [ -d "binaries" ]; then
	read -p "An old 'binaries' folder has been found. Do you want to remove it? (y/n) " answer
	if [ "$answer" == "y" ]; then
		rm -rf binaries
	else
		exit 0
	fi
fi

mkdir binaries && cd binaries && python -m PyInstaller -D -F --name ChatAppPy_Client ../client.py && python -m PyInstaller -D -F --name ChatAppPy_Server ../server.py && cd .. && echo "Binaries built\! You can find them in the binaries/dist folder." && exit 0
echo "Error during compilation\!"
exit 1
