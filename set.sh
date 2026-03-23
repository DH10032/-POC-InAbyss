#!/bin/bash

# compile 방법
# g++ (컴파일 할 코드) -o (실해파일 이름) -l(라이브러리 이름)
# 예시) g++ render.cpp -o render -lSDL2 -lSDL_image -lSDL2_ttf

# Lock 파일 제거
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99 2>/dev/null

# 이미 실행 중인지 확인
if pgrep -x "Xvfb" > /dev/null; then
    echo "VNC가 이미 실행 중입니다."
# 패키지가 없으면 설치
else
    sudo apt-get update -qq
    # xvfb x11vnc novnc websockify -> remote 서버 연결
    if ! command -v x11vnc &> /dev/null; then
        sudo apt-get install -y xvfb x11vnc novnc websockify -qq
    fi
    
    # 서비스 시작
    Xvfb :99 -screen 0 1280x720x24 > /dev/null 2>&1 &
    sleep 1
    
    x11vnc -display :99 -nopw -listen 0.0.0.0 -xkb -forever > /dev/null 2>&1 &
    sleep 1
    
    # noVNC 경로 확인 후 실행
    if [ -d "/usr/share/novnc" ]; then
        websockify -D --web=/usr/share/novnc/ 6080 localhost:5900
    else
        # noVNC 없으면 web 옵션 없이 실행
        websockify 6080 localhost:5900 > /dev/null 2>&1 &
    fi
    
fi

echo "VNC 서버 시작 완료!"

# DISPLAY 설정 (중요: source로 실행해야 적용됨)
# 아래 실행하기 (!!! 이제 한번에 복붙 가능)
: '
\export DISPLAY=:99 &&
\export XDG_RUNTIME_DIR=/tmp/runtime-codespace &&
\export SDL_VIDEODRIVER=x11 &&
\mkdir -p $XDG_RUNTIME_DIR &&
\chmod 700 $XDG_RUNTIME_DIR
sudo apt-get install -y \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-render-util0 \
  libxcb-xinerama0 \
  libxcb-xkb1 \
  libxcb-cursor0 \
  libxcb-util1 \
  libxkbcommon0 \
  libxkbcommon-x11-0 \
  libegl1
'