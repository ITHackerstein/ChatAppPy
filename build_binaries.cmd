@echo off
IF EXIST binaries (
	set /P answer="An old 'binaries' folder has been found. Do you want to remove it? (y/n) "
	IF %answer%==y (
		rmdir /S /Q binaries
	) ELSE (
		EXIT /B 0
	)
)
mkdir binaries && cd binaries && pyinstaller -D -F --name ChatAppPy_Client ..\client.py && pyinstaller -D -F --name ChatAppPy_Server ..\server.py && cd .. && echo Binaries built! You can find them in the binaries\dist folder. && EXIT /B 0
echo Error while building binaries!
EXIT /B 1

