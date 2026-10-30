# K7 프리미어 한국형 Gen5W 포팅 작업 안내

현재 상태: **실제 자료 기반 시험 빌드 준비 완료, 실차 미검증**. 최신 [추출 자료 분석 결과](K7_CAPTURE_RESULT_ko.md)를 먼저 확인하세요. 아래에는 자료 수집 및 개발 재현 절차도 함께 유지합니다.

## 1. 확인된 차량과 아직 확인할 항목

| 항목 | 현재 근거 / 상태 |
|---|---|
| 차량 | 사용자 설명: 2020 K7 프리미어 3.0 GDI, 한국 사양 |
| AVN 모델 | 사용자 화면: `YGAS.S5BMC.KR` |
| 소프트웨어 | 사용자 화면: `YGPE.KOR.S5W_M.V039.001.260902` |
| MICOM | 사용자 화면: `YGPE.KOR.302.260318.MICOM.D` (변경 대상 아님) |
| NEMESIS | 사용자 확인: 1.15 설치 완료 |
| Wi-Fi | 사용자 보고: 모듈 있음. 실제 키트: wl 어댑터 미검출, wlan 없음. 물리적 부재를 단정할 수 없고 연결도 아직 미확인 |
| `ro.build.product` / `ro.mobis.targetdir` | `YGPE.KOR.0000.V039.001.260902` / `/system/onebin/ygpe_kr` 실측 |
| Leafia 실차 검증 / Kia Connect 유지 | 미확인 |

개발용 프로필은 [`../profiles/k7pe.json`](../profiles/k7pe.json)에 있습니다. 실측 제품 ID와 지역 폴더를 반영했습니다. `patches/cars`와 포크의 호환성 DB에 현재 펌웨어용 시험 세트를 등록했으며 상태는 `testing`입니다. 상위 프로젝트 공식 지원을 뜻하지 않습니다.

## 2. 차에 가서 할 일

1. **설치 패키지가 아닌 `leafia-kit-port.zip`**을 준비합니다. [현재 저장소의 키트](downloads/leafia-kit-port.zip)를 사용하거나 소스에서 `sh tools/build-kit.sh port`로 빌드합니다. 파일 이름에 `port`가 있는지뿐 아니라 압축 내부 `LEAFIA-LEVEL`의 내용이 `port`인지 확인합니다.
2. exFAT/FAT32 USB를 준비하고 여유 공간을 최소 200MB 확보합니다. 다른 NEMESIS 설치 파일은 섞지 않습니다. 압축 내부의 `NEMESIS.data`, `NEMESIS.sh`, `LEAFIA-LEVEL`, `lpatch`, `recipes/` 등을 **모두 USB 최상위**에 풉니다.
3. 주차한 상태에서 차량 전원을 안정적으로 유지하고 실행합니다. 기존 키트 안내의 Ready 권장은 전기차 기준이며, 이 K7은 내연기관 차량입니다. 시동을 유지한다면 환기되는 장소에서 작업합니다.
4. USB를 연결하고 NEMESIS 실행을 승인합니다. 성공 메시지를 기다린 후 USB를 제거합니다. 키트는 시스템 파일을 패치하지 않지만 USB 출력과 임시 실행 파일을 만들며, NEMESIS는 이미 설치되어 있어야 합니다.
5. PC에서 **생성된 `LEAFIA` 폴더**가 있는지 확인합니다. 키트 ZIP 자체와 차량에서 생성된 결과물은 다릅니다. 원본 결과물은 따로 복사해 보관합니다.
6. 이 대화에 우선 `LEAFIA/public/`와 `LEAFIA/private/stock/`을 하나의 ZIP으로 첨부합니다. 문제가 있으면 `private/logs/`를 추가로 검토합니다. **`private/keys/`는 이번 앱 포팅의 필수 입력이 아니므로 우선 제외해도 됩니다.** 공개 GitHub 이슈·커밋·릴리스에는 비공개 폴더를 올리지 않습니다.

기대 구조:

```text
LEAFIA/
  public/
    LEAFIA-REPORT.txt
    summary.txt
  private/
    collected.txt
    stock/
      build.prop
      app/          # APK + ODEX, 특히 GPM / DiPO / iAP2 / Navi
      framework/    # 전체 framework 파일
      lib/          # Android Auto, CarPlay, 코덱 라이브러리
      etc/
      onebin/
    logs/           # 필요할 때 비공개 검토
    keys/           # 우선 전달 불필요, 절대 공개하지 않음
```

키트는 원래 이름이 같은 파일을 같은 출력 폴더에 복사합니다. 여러 차량이나 여러 SW 버전의 수집 결과를 한 `LEAFIA` 폴더에 합치지 마세요. 추출에 실패한 파일은 `collected.txt`의 `FAIL`과 보고서에서 확인합니다.

## 3. 자료를 받은 뒤의 작업

### 수집 자료 검사

아래 명령은 개발 PC(Linux/WSL)에서 실행합니다. 차량에서 실행하지 않습니다.

```sh
mkdir -p private
python3 tools/k7-intake.py /path/to/LEAFIA > private/k7-intake.json
```

검사 항목:

- 보고서 형식·종료 표식, 실측 제품 ID·지역 폴더, `build.prop`의 제품 ID 일치 여부
- 핵심 APK/ODEX, 프레임워크 BOOTCLASSPATH 파일, 지역 `featurexml.cfg` 존재 여부
- 추출 파일과 보고서의 실기기 MD5 일치 여부 및 추출 파일 SHA256 목록
- 기존 EV6·아이오닉 5·한국 K5 등의 순정 체크섬과 일치/불일치 목록
- 누락 파일·링크 파일 차단. 키·비공개 로그 내용은 열지 않음

종료 코드 0과 `collection_complete: true`는 **수집 검사 통과**일 뿐입니다. `install_ready`는 항상 `false`이며 Wi-Fi 작동, 포팅 완료, Kia Connect 정상 동작을 의미하지 않습니다. 펌웨어 버전 문자열과 Wi-Fi 드라이버 증거, 설치된 패키지 목록은 별도로 검토합니다.

### 포팅 경로 결정

1. **무선 Android Auto만 필요:** 기존 설치기는 미등록 차량에서도 조건이 맞으면 `1_projection`만 설치하는 기본 모드를 제공합니다. 차종 패치가 없다고 AA 활성화가 반드시 불가능한 것은 아닙니다. 기본 모드 또한 기능 설정과 네트워크 상태를 변경하므로 실제 연결·기존 기능 검증은 필요합니다.
2. **K7 앱 코드가 기존 차종과 동일:** 체크섬과 `.lpd` 입력 조건을 대조합니다. 동일한 ODEX라도 APK 포장이나 프레임워크가 다를 수 있으므로 차종 이름만 바꿔 설치하지 않습니다.
3. **다른 앱 코드:** `tools/port.py`로 기준 차량의 순정 코드 → 수정 코드 변화량을 K7 코드에 옮깁니다. 충돌은 수동 분석합니다.
4. **Android Auto 네이티브 라이브러리가 다름:** 기존 라이브러리 패치를 억지로 적용하지 않습니다. 별도 분석으로 수정본을 만들고 `--lib-build`로 전달해야 합니다. CarPlay 레시피의 `NATIVE`/`PATCHABLE`/`MISMATCH`도 각각 검토합니다.

**중요한 추가 입력:** 기존 `port.py`는 K7 자료 외에 기준 차량의 순정 앱·동일 버전 프레임워크·수정 APK 빌드를 요구합니다. 저장소의 `.lpd`는 원본을 복원하는 파일이 아닙니다. 따라서 K7 키트만으로 반드시 자동 포팅이 완료된다고 약속할 수 없습니다. 한국 K5(`dl3hev`, 260902)는 비교 후보이며, 버전 번호만으로 호환된다고 판단하지 않습니다. 기준 차량 원본이 없다면 해당 자료 확보 또는 K7 직접 분석이 남습니다.

### 기준 차량 빌드 복원(해당 순정 파일을 확보한 경우)

기준 차량용 **정확한 원본**과 공개 차분 패치로 비공개 참조 빌드를 복원하는 호스트 도구를 추가했습니다. 다른 차종 파일로 대체하면 거부합니다.

```sh
cc -DHOST -O2 -Wall -o tools/lpatch/lpatch-host tools/lpatch/lpatch.c
python3 tools/rebuild-reference.py --variant dl3hev \
  --stock /path/to/reference/LEAFIA/private/stock \
  --out private/reference-builds/dl3hev
```

모든 원본 체크섬을 먼저 검사하고, 각 출력은 매니페스트의 MD5와 일치해야 합니다. 전체 성공 시에만 결과 디렉터리를 확정하며 기존 출력 폴더는 덮어쓰지 않습니다. 이것은 **기준 차량 파일 복원**이며 K7 설치본 생성이 아닙니다.

### K7 포팅 실행(입력 확인 후 개발자 작업)

환경은 [CONTRIBUTING](../CONTRIBUTING.md)을 따릅니다. `baksmali`/`smali` 실행 명령, Java, `diff`, `patch`, 호스트 `lpatch`, 해시 고정 Python 의존성이 필요합니다. `mkmenu.py`는 별도 JAR 설정을 사용하므로 두 도구의 설정을 혼동하지 않습니다.

```sh
python3 -m pip install --require-hashes -r tools/requirements.txt
# 아래 값은 실제 수집 자료와 분석으로 결정합니다. 복사해서 차량에 실행하지 않습니다.
python3 tools/port.py --variant k7pe_kr \
  --prefix '<observed-product-prefix.>' --name 'Kia K7 Premier (KR)' \
  --new-stock /path/to/K7/LEAFIA/private/stock \
  --new-fw /path/to/K7/LEAFIA/private/stock/framework \
  --ref-variant dl3hev \
  --ref-stock /path/to/reference/LEAFIA/private/stock \
  --ref-fw /path/to/reference/LEAFIA/private/stock/framework \
  --ref-builds private/reference-builds/dl3hev \
  --out-builds private/k7-builds --work private/k7-work
```

`--work`는 비어 있어야 합니다. 입력 펌웨어가 바뀌면 새 작업 폴더를 사용합니다. K7의 라이브러리가 기준 차량과 다르면 이 명령은 중단되며, 별도 포팅이 끝난 라이브러리를 `--lib-build`로 제공해야 합니다. 도구가 성공하면 `patches/k7pe_kr/`와 `patches/cars`가 변경되므로, 변경 결과를 검토하고 아래 검증 전에는 차량 설치본으로 배포하지 않습니다.

`5_menu`는 미국·캐나다의 기기 연결 메뉴 동작을 위한 선택적 수정입니다. 한국 K7에 필요한 메뉴 수정이라고 가정하지 않습니다.

## 4. 빌드와 검증 순서

```sh
python3 -m unittest discover -s tests -v
sh tools/build-package.sh
python3 tools/compat-built.py --check
sh tools/check-downloads.sh
```

위 명령으로 ZIP이 만들어지는 것만으로 K7용 포팅이 완료된 것은 아닙니다. 현재 빌드에는 실제 K7 원본과 일치하는 시험 패치 세트가 포함됩니다. 모의 Wi-Fi 성공은 실차 증거가 아닙니다.

실제 패치를 만든 뒤에는 수집 보고서의 제품 ID·지역 폴더·원본 트리로 아래 모의 설치를 수행합니다.

```sh
MOCK_SH=mksh MOCK_NEMESIS=1.15 MOCK_USB_DESCRIPTOR=1 \
  sh tools/mock/install-test.sh dist/HMG_Leafia_Plus_Wireless_CarPlay_AA.zip \
  '<observed-ro.build.product>' '<observed-region-folder>' /path/to/K7/LEAFIA/private/stock
```

- **전체 기능 포팅을 검증할 때에는 로그의 `full mode`를 확인합니다.** 기본 모드로 우회한 PASS는 전체 패치 검증이 아닙니다.
- 정상 설치·제거 시 `/system`이 바이트 단위로 원복되는지 확인합니다. Android 실행 중/중지 상태, USB 설치 파일 처리, Wi-Fi 클라이언트 미활성 기본 설정도 확인합니다.
- 모의 환경의 `dexopt`는 스텁입니다. 실제 Dalvik 검증·화면·무선 연결·CAN 전달·Kia Connect는 재현하지 못합니다.
- 실차 시험은 별도 단계입니다. 순정 내비·유선/무선 AA·Bluetooth·후방카메라·오디오·계기판 안내와 Kia Connect 상태조회/원격기능을 설치 전후 비교합니다. 설치·제거 로그와 복구 방법을 확보하고, 실제 성공 전에는 `supported`로 표시하지 않습니다.
- NEMESIS/Leafia 백업은 패키지가 수정한 파일의 복구용입니다. 서비스 계정, 모든 설정, OTA 동작이나 완전한 시스템 복구를 보장하는 백업이 아닙니다.

## 5. 이번 준비 변경의 범위

새 수집 검사·참조 빌드 복원 도구, K7 상태 프로필, 회귀 테스트를 추가했습니다. `port.py`는 프레임워크 분석 실패/빈 결과·이전 작업 캐시·자동 처리할 수 없는 클래스 삭제를 거부하며, 문서에 맞게 API 18·단일 스레드로 조립합니다.

실제 자료 분석 후 `k7pe_kr` 델타 참조 및 현재 SW용 차종 등록을 추가했습니다. 차량용 Wi-Fi 하드웨어 검사·순정 해시 검사·백업/제거 절차는 우회하지 않았습니다. MICOM·부트로더·모뎀·Kia Connect 인증서나 계정을 변경하는 작업은 포함하지 않습니다. 이번 작업은 무선 폰 프로젝션 포팅 준비이며, 차량 GPS를 휴대전화 AA로 보내거나 CAN 계기판 앱을 만드는 별도 프로젝트가 완성된 것은 아닙니다.

## 6. 시험 ZIP의 차량 설치 및 결과 수집

이 단계는 실차 검증용입니다. Wi-Fi와 Kia Connect 동작은 아직 보장하지 않습니다. NEMESIS 1.15가 설치된 해당 K7 / V039.001.260902에서만 시험합니다.

1. 다른 NEMESIS 파일이 없는 exFAT/FAT32 USB에 **시험 ZIP 내부**의 `NEMESIS.data`와 `packages/`를 풉니다. port 키트와 설치 ZIP을 같은 USB에 섞지 않습니다.
2. 주차·안정적인 차량 전원 상태에서 연결하고 설치 안내를 따릅니다. 설치가 거부되면 해시나 Wi-Fi 검사를 우회하지 않습니다.
3. 재부팅 시 USB를 제거합니다. 최초 부팅에서는 기다린 뒤 폰 프로젝션과 무선 Android Auto 연결을 확인합니다. Wi-Fi 클라이언트 옵션은 첫 시험에서 추가하지 않습니다.
4. 순정 기능 및 Kia Connect를 설치 전과 비교합니다. 문제가 있으면 NEMESIS Manager → Packages → 해당 패키지 → Uninstall 후 재시작합니다. 제거 불가/복구 오류는 반복 재설치보다 로그 확인이 우선입니다.
5. 무선 연결에 실패했다면 실패 직후 **별도 USB의 port 키트**로 새 `LEAFIA` 결과를 수집합니다. 설치 전 결과와 폴더를 분리하고 비공개로 전달합니다.
