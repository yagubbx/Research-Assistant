@echo off
setlocal
cd /d "%~dp0"
set "IMAGE=vertex-research:1.1.0"
set "CHECK_CONTAINER=vertex-check-%RANDOM%"
set "CONTAINER_STARTED="
set "RESULT=artefacts\docker-verification.txt"
echo Docker acceptance for Research Assistant v1.1.0 > "%RESULT%"
docker version >> "%RESULT%" 2>&1
if errorlevel 1 goto failed
echo Building image. This can take several minutes.
docker build -t "%IMAGE%" . >> "%RESULT%" 2>&1
if errorlevel 1 goto failed
docker run --rm --network none "%IMAGE%" >> "%RESULT%" 2>&1
if errorlevel 1 goto failed
docker run --rm --network none "%IMAGE%" doctor --offline >> "%RESULT%" 2>&1
if errorlevel 1 goto failed
docker run -d --name "%CHECK_CONTAINER%" -p 127.0.0.1:18501:8501 --entrypoint python "%IMAGE%" -m streamlit run researcher/web_ui.py --global.developmentMode false --server.address 0.0.0.0 --browser.gatherUsageStats false >> "%RESULT%" 2>&1
if errorlevel 1 goto failed
set "CONTAINER_STARTED=1"
powershell -NoProfile -Command "$ok=$false; for($i=0;$i -lt 30;$i++){try{$r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:18501/_stcore/health' -TimeoutSec 2; if($r.StatusCode -eq 200){$ok=$true; break}}catch{}; Start-Sleep -Seconds 2}; if(-not $ok){exit 1}" >> "%RESULT%" 2>&1
if errorlevel 1 goto failed
docker image inspect "%IMAGE%" --format "Image ID: {{.Id}} Size bytes: {{.Size}}" >> "%RESULT%" 2>&1
docker rm -f "%CHECK_CONTAINER%" >> "%RESULT%" 2>&1
echo RESULT: PASS - build, five-question offline CLI, doctor and container UI health >> "%RESULT%"
echo PASSED. Results saved in %RESULT%
pause
exit /b 0
:failed
if defined CONTAINER_STARTED docker logs "%CHECK_CONTAINER%" >> "%RESULT%" 2>&1
if defined CONTAINER_STARTED docker rm -f "%CHECK_CONTAINER%" >> "%RESULT%" 2>&1
echo RESULT: FAIL - inspect the first error above >> "%RESULT%"
echo Check failed. See %RESULT%
pause
exit /b 1
