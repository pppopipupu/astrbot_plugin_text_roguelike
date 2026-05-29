@echo off
echo Starting unit tests in AstrBot Docker environment...
echo.

echo [1/5] Running AstrBot plugin load integration test on host...
py scratch/test_astrbot_load.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: AstrBot plugin load integration test failed!
    exit /b 1
)
echo.

echo [2/5] Running query unit test inside container...
docker exec -t astrbot-test-env python /AstrBot/data/plugins/astrbot_plugin_text_roguelike/scratch/test_query_monster.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Query unit test failed!
    exit /b 1
)
echo.

echo [3/5] Running shortcut unit test inside container...
docker exec -t astrbot-test-env python /AstrBot/data/plugins/astrbot_plugin_text_roguelike/scratch/test_shortcut.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Shortcut unit test failed!
    exit /b 1
)
echo.

echo [4/5] Running rogue mode unit test inside container...
docker exec -t astrbot-test-env python /AstrBot/data/plugins/astrbot_plugin_text_roguelike/scratch/test_rogue_mode.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Rogue mode unit test failed!
    exit /b 1
)
echo.

echo [5/5] Running game flow unit test inside container...
docker exec -t astrbot-test-env python /AstrBot/data/plugins/astrbot_plugin_text_roguelike/scratch/test_flow.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Game flow unit test failed!
    exit /b 1
)
echo.

echo ==================================================
echo All AstrBot environment tests passed successfully!
echo ==================================================
