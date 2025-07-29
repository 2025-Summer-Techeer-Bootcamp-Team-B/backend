#!/bin/bash

# 스크립트가 있는 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 에러 발생 시 스크립트 중단
set -e

# 함수: 에러 메시지 출력
error_exit() {
    echo "Error: $1" >&2
    exit 1
}

# docker-compose 설치 여부 확인 및 설치
if ! [ -x "$(command -v docker-compose)" ]; then
    echo 'docker-compose가 설치되어 있지 않습니다. 설치를 시작합니다...' >&2
    
    # 최신 버전의 Docker Compose 설치
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose || error_exit "Docker Compose 다운로드 실패"
    
    # 실행 권한 부여
    sudo chmod +x /usr/local/bin/docker-compose || error_exit "Docker Compose 권한 설정 실패"
    
    # 설치 확인
    if ! [ -x "$(command -v docker-compose)" ]; then
        error_exit "docker-compose 설치에 실패했습니다."
    else
        echo 'docker-compose가 성공적으로 설치되었습니다.'
    fi
fi

# 필요한 디렉토리 생성
echo "### 필요한 디렉토리 구조를 생성합니다..."

# 현재 디렉토리 권한 확인
if [ ! -w "." ]; then
    error_exit "현재 디렉토리에 쓰기 권한이 없습니다. sudo로 실행해주세요."
fi

# docker-compose.yml 파일 존재 확인
if [ ! -f "docker-compose.yml" ]; then
    error_exit "docker-compose.yml 파일을 찾을 수 없습니다. 올바른 디렉토리에서 실행해주세요."
fi

# nginx 설정 파일 백업 (이미 존재하는 경우)
if [ -f "nginx/nginx.conf" ]; then
    echo "nginx.conf 파일을 백업합니다..."
    cp nginx/nginx.conf nginx.conf.backup || error_exit "nginx.conf 백업 실패"
fi

# 기존 디렉토리 제거 후 새로 생성
echo "기존 nginx, certbot 디렉토리를 정리합니다..."
rm -rf nginx certbot || error_exit "기존 디렉토리 제거 실패"

echo "새로운 디렉토리 구조를 생성합니다..."
mkdir -p nginx certbot/conf certbot/www || error_exit "디렉토리 생성 실패"

# nginx.conf 복원 (백업이 있는 경우)
if [ -f "nginx.conf.backup" ]; then
    echo "nginx.conf 파일을 복원합니다..."
    mv nginx.conf.backup nginx/nginx.conf || error_exit "nginx.conf 복원 실패"
fi

# 디렉토리 권한 확인
if [ ! -w "nginx" ] || [ ! -w "certbot" ]; then
    error_exit "생성된 디렉토리에 쓰기 권한이 없습니다."
fi

echo "디렉토리 구조가 성공적으로 생성되었습니다."

# SSL 인증서 설정
domains=(yosm-n.kro.kr www.yosm-n.kro.kr)    # SSL 인증서를 발급받을 도메인 이름
rsa_key_size=4096                  # SSL 키 크기 (4096비트 = 매우 강력한 보안)
data_path="./certbot"              # 인증서와 관련 파일들이 저장될 로컬 경로
email="dongan0618@naver.com"       # Let's Encrypt 알림을 받을 이메일 주소
staging=0                          # 테스트 모드 설정 (0: 실제 인증서, 1: 테스트 인증서)

# 이미 certbot 데이터가 있는 경우 사용자에게 확인
if [ -d "$data_path" ]; then
  read -p "Existing data found for $domains. Continue and replace existing certificate? (y/N) " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
fi

# SSL 설정에 필요한 추가 파일 다운로드
# options-ssl-nginx.conf: Nginx SSL 설정 파일
# ssl-dhparams.pem: DH 파라미터 (SSL/TLS 보안 강화)
if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
  echo "### Downloading recommended TLS parameters ..."
  mkdir -p "$data_path/conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
  echo
fi

# 임시 SSL 인증서 생성
# Let's Encrypt가 실제 인증서를 발급하기 전까지 사용할 자체 서명 인증서
echo "### Creating dummy certificate for $domains ..."
path="/etc/letsencrypt/live/$domains"
mkdir -p "$data_path/conf/live/$domains"
docker-compose run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo

# Nginx 시작 (임시 인증서 사용)
echo "### Starting nginx ..."
docker-compose up --force-recreate -d nginx
echo

# 임시 인증서 제거
echo "### Deleting dummy certificate for $domains ..."
docker-compose run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/$domains && \
  rm -Rf /etc/letsencrypt/archive/$domains && \
  rm -Rf /etc/letsencrypt/renewal/$domains.conf" certbot
echo

# Let's Encrypt에서 실제 SSL 인증서 발급 요청
echo "### Requesting Let's Encrypt certificate for $domains ..."
# 도메인 인자 준비
domain_args=""
for domain in "${domains[@]}"; do
  domain_args="$domain_args -d $domain"
done

# 이메일 설정 (이메일이 없는 경우 --register-unsafely-without-email 사용)
case "$email" in
  "") email_arg="--register-unsafely-without-email" ;;
  *) email_arg="--email $email" ;;
esac

# 테스트 모드 설정
if [ $staging != "0" ]; then staging_arg="--staging"; fi

# certbot을 사용하여 실제 인증서 발급
docker-compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    $email_arg \
    $domain_args \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal" certbot
echo

# 새로운 인증서를 적용하기 위해 Nginx 재시작
echo "### Reloading nginx ..."
docker-compose exec nginx nginx -s reload 