@echo off
chcp 65001 >nul
echo ================================================
echo   寮犻洩宄版櫤鑳藉織鎰跨櫨绉?路 鐧惧害AI澧炲己鐗?echo ================================================
echo.
echo   鍚姩鏈湴寮€鍙戞湇鍔″櫒...
echo.

:: 妫€鏌ヤ緷璧?python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo [瀹夎] 姝ｅ湪瀹夎渚濊禆...
    pip install -r requirements.txt
)

:: 璁剧疆鐜鍙橀噺锛堝彲閫夛紝涓嶈缃篃鑳界敤锛?if not defined BAIDU_API_KEY echo [鎻愮ず] 鏈缃?BAIDU_API_KEY锛岀櫨搴I鍚庣涓嶅彲鐢?if not defined BAIDU_SECRET_KEY echo [鎻愮ず] 鏈缃?BAIDU_SECRET_KEY锛岀櫨搴I鍚庣涓嶅彲鐢?
echo.
echo   鎵撳紑娴忚鍣ㄨ闂? http://localhost:5000
echo   鎸?Ctrl+C 鍋滄鏈嶅姟
echo.

python app.py

pause
