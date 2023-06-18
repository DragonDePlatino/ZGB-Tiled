setx ZGB_PATH "%cd%\common"

if exist "%LocalAppData%\Tiled\extensions" (
	xcopy /s /y "%cd%\extensions" "%LocalAppData%\Tiled\extensions"
) else (
	exit 1
)
