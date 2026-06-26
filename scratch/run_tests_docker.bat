@echo off
echo Starting unit tests in AstrBot Docker environment...
echo.

echo [1/2] Running AstrBot plugin load integration test on host...
py scratch/test_astrbot_load.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: AstrBot plugin load integration test failed!
    exit /b 1
)
echo.

echo [2/2] Running all unit tests inside container...
docker exec -w /AstrBot/data/plugins/astrbot_plugin_text_roguelike -e PYTHONPATH=/AstrBot/data/plugins/astrbot_plugin_text_roguelike -t astrbot-test-env python /AstrBot/data/plugins/astrbot_plugin_text_roguelike/scratch/test_flow.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Unit tests failed!
    exit /b 1
)
echo.

echo ==================================================
echo All AstrBot environment tests passed successfully!
echo ==================================================
