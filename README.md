# HMG Leafia Plus

> **K7 프리미어 시험 빌드:** 실제 V039.001.260902 추출 자료와 일치하는 패치 세트를 등록했습니다. 호환성 상태는 `testing`입니다. 모의 전체 설치·제거 및 정적 검사 통과, 실차 무선 연결·Kia Connect는 미검증이며 현재 키트에서 Wi-Fi 어댑터가 검출되지 않았습니다. [추출 자료 분석 결과](docs/K7_CAPTURE_RESULT_ko.md) · [K7 작업 안내](docs/K7_PORTING_ko.md)

[![GitHub에서 후원하기](https://img.shields.io/badge/Sponsor_on_GitHub-%E2%9D%A4-bf3989?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/VysseCodes)
[![Ko-fi에서 커피 후원하기](https://img.shields.io/badge/Buy_me_a_coffee-Ko--fi-FF5E5B?style=for-the-badge&logo=kofi&logoColor=white)](https://ko-fi.com/vyssecodes)

> **HMG Leafia Plus는 무료입니다.** 서비스센터 방문을 줄이거나 주행 환경을 더 편리하게 만드는 데 도움이 되었다면, [GitHub Sponsors](https://github.com/sponsors/VysseCodes) 또는 [Ko-fi](https://ko-fi.com/vyssecodes)를 통한 후원을 고려해 주세요. 후원금은 테스트와 새로운 차종 지원 개발을 이어가는 데 사용됩니다.

[NEMESIS](https://github.com/xwtk/hmg_nemesis) 패키지를 통해 현대·기아·제네시스 **Gen5W** 헤드유닛(AVN)의 기능을 개선하는 커뮤니티 도구입니다. 첫 번째 목표는 가능한 한 많은 헤드유닛에서 무선 CarPlay와 Android Auto를 사용할 수 있도록 하는 것입니다.

**호환성 확인 페이지:** https://vyssecodes.github.io/HMG-Leafia-Plus/

## 작동 원리

펌웨어는 차종·지역·버전에 따라 다르기 때문에 차량 간에 파일 전체의 체크섬이 일치하는 경우는 드뭅니다. HMG Leafia Plus는 **실제로 변경할 바이트 영역만 검사**합니다.

- **레시피**(`recipes/*.recipe`)에는 각 패치에 사용할 새 바이트와 해당 위치 주변 영역의 해시가 들어 있습니다. 기아·현대 원본 파일에서 가져온 바이트는 포함하지 않습니다.
- **`lpatch`**(`tools/lpatch/`)는 헤드유닛에서 실행되는 작은 정적 링크 ARM 도구입니다. 검사 대상 영역이 모두 순정 상태의 해시와 일치할 때만 패치를 적용합니다. 따라서 파일의 나머지 부분이 다르더라도 패치 대상 위치가 동일한 펌웨어라면 같은 레시피를 사용할 수 있습니다.
- **기본 탑재 기능도 인식합니다.** 일부 펌웨어에는 필요한 기능이 이미 들어 있습니다. 예를 들어 한국 V039 빌드는 이미 Wi-Fi CarPlay 세션을 수락하며 실제 AAC/Opus 변환기도 포함합니다. 레시피는 이러한 파일을 `native`로 표시하며, 해당 파일에는 패치를 적용하지 않습니다.

| 구성 요소 | 기능 | 적용 방식 |
|---|---|---|
| 무선 폰 프로젝션 | 해당 헤드유닛의 지역 폴더에서 무선 CarPlay/AA 기능 플래그를 활성화합니다. 기본적으로 핫스팟만 사용하며, Wi-Fi 클라이언트나 추가 Wi-Fi 메뉴는 활성화하지 않습니다. | 기능 파일 및 설정 수정. 제거 시 모두 복원 |
| CarPlay Wi-Fi 세션 | `libCarPlayCore`가 Wi-Fi 세션을 수락하도록 합니다. | `carplay-core-wifi.recipe` |
| CarPlay 무선 오디오 | Wi-Fi 연결에서 AAC(음악)와 Opus(Siri·통화·마이크)를 제공하고, 헤드유닛 자체 코덱으로 디코딩합니다. | `carplay-audio-formats.recipe`, `carplay-utils-converter.recipe` + `libev6aac.so` |
| 폰 프로젝션 설정 메뉴 | 미국·캐나다 헤드유닛에서 순정 펌웨어처럼 설정 > 폰 프로젝션을 누르면 기기 연결 화면(CarPlay 분할 화면·연결된 휴대전화)이 열리도록 유지합니다. 수정 대상과 일치하는 순정 Bluetooth 설정 앱에만 적용합니다. | `patches/common/optional` (`HKMC_BtSettings`) |
| CarPlay Bluetooth 브리지 | Bluetooth/iAP2를 통해 무선 CarPlay 연결을 시작합니다. | 헤드유닛의 순정 앱을 바탕으로 기기에서 다시 빌드 (`patches/<car>`) |
| 턴바이턴 안내 | 폰 프로젝션의 내비게이션 안내를 계기판과 HUD에 표시합니다. | 헤드유닛의 순정 앱을 바탕으로 기기에서 다시 빌드 (`patches/<car>`). 표준 계기판 호출만 사용하므로 HUD가 없는 차량에서도 사용할 수 있습니다. 펌웨어에 필요한 호출이 하나라도 없으면 설치를 거부합니다. |

아직 패치 세트가 없는 차량에는 **기본 모드(basic mode)**가 적용됩니다. 무선 폰 프로젝션 부분만 활성화하며, Wi-Fi 모듈이 있는 Gen5W 헤드유닛에서 무선 Android Auto를 사용할 수 있도록 합니다. 설치 프로그램은 해당 차량의 전체 기능 지원 버전을 개발할 수 있도록 보고서도 저장합니다.

## 설치

1. 헤드유닛에 [NEMESIS](https://github.com/xwtk/hmg_nemesis) **1.15 이상**을 설치합니다.
2. Leafia 키트를 사용해 [호환성 페이지](https://vyssecodes.github.io/HMG-Leafia-Plus/)에서 차량의 호환성을 확인합니다.
3. [최신 릴리스](../../releases/latest)에서 **HMG_Leafia_Plus_Wireless_CarPlay_AA-<version>.zip**을 내려받습니다. 또는 `tools/build-package.sh`로 직접 빌드할 수 있습니다. 각 릴리스에는 SHA256 체크섬이 안내되어 있습니다.
4. 비어 있는 exFAT 또는 FAT32 USB 드라이브의 최상위 폴더에 압축을 풉니다(`NEMESIS.data`와 `packages/`가 위치해야 합니다).
5. 차량을 켠 상태에서 USB 드라이브를 연결하고 설치를 승인합니다. 가능하면 Ready 상태를 유지하세요(아래 주의 사항 참고). 설치에는 몇 분이 걸립니다. 설치 중에는 일부만 변경된 파일을 앱이 읽는 일이 없도록 CarPlay·Android Auto·내비게이션·Bluetooth 설정을 중지하며, 재부팅 전에 다시 실행합니다.
6. **헤드유닛이 재부팅되면 USB 드라이브를 제거합니다.** 꽂아 둔 상태에서는 첫 CarPlay 또는 Android Auto 연결이 되지 않을 수 있습니다. 설치 프로그램은 실수로 다시 실행되지 않도록 `NEMESIS.data`의 이름을 `NEMESIS.data.installed`로 변경합니다.
7. **제거**하려면 NEMESIS Manager에서 Packages → Uninstall을 선택한 다음 재부팅합니다. 원문 안내에 따르면 패키지가 변경한 모든 파일이 순정 상태로 복원됩니다.

**선택 사항: Wi-Fi 클라이언트 기능(테스트 중).** 기본적으로 헤드유닛의 Wi-Fi는 무선 CarPlay/Android Auto용 핫스팟으로만 작동합니다. Wi-Fi 메뉴를 표시하고 다른 네트워크에 접속하려면(예: 집 Wi-Fi를 통한 ADB 연결), 설치 USB에서 `NEMESIS.data` 옆에 `LEAFIA-WIFI-CLIENT`라는 이름의 빈 파일을 만듭니다. 이 헤드유닛들은 Wi-Fi 무선 장치가 하나이므로, 집 네트워크 접속과 무선 폰 프로젝션의 동시 사용 가능 여부는 아직 테스트 중입니다. 패키지를 제거하면 이 기능도 다시 꺼집니다.

### 알려진 특이 사항 및 주의점

- **USB 드라이브와 Android Auto:** 순정 펌웨어에서는 USB 드라이브를 연결하면 헤드유닛이 유선 Android Auto 연결을 시도하고, 재부팅할 때까지 무선 Android Auto 연결을 막습니다. Leafia 설치 후에는 Android Auto가 USB 드라이브와 허브를 무시합니다. 설치가 완료되기 전이나 v1.0.4 이하 버전에서는 헤드유닛이 재부팅되면 USB 드라이브를 제거하세요.
- **차량 시동을 껐다 켜는 것만으로는 헤드유닛이 재부팅되지 않습니다.** 운전석 문을 열거나 일정 시간이 지날 때까지 켜져 있습니다. 실제로 재시작하려면 차량을 끄고 운전석 문을 연 뒤 화면이 꺼질 때까지 기다리거나, 헤드유닛 전원 버튼을 약 10초 동안 길게 누릅니다.
- **설치 후 무선 CarPlay 또는 Android Auto가 연결되지 않는 경우:** “Phone not responding”이 표시되거나 휴대전화가 차량 Wi-Fi에 연결된 뒤 아무 반응이 없다면, 위 방법으로 헤드유닛을 재시작합니다. 그래도 연결되지 않으면 처음부터 다시 페어링합니다. 휴대전화의 Android Auto(또는 CarPlay) 설정·Bluetooth·Wi-Fi에서 차량을 삭제하고, 차량에서도 휴대전화를 삭제합니다.
- **설치가 중단된 경우:** 차량을 끄거나 USB 드라이브를 빼서 중단되었다면 설치를 다시 실행합니다. 설치가 완료되든 실패하든, 각 실행이 끝날 때 CarPlay·Android Auto·내비게이션·Bluetooth 설정을 다시 실행합니다.
- **장시간 작업 시 12V 배터리:** 전기차는 Ready 상태에서만 12V 배터리가 충전됩니다. Ready 상태가 아닌 채 차량을 켜 두고 설치·테스트를 오래 진행하면 배터리가 방전되므로 Ready 상태를 유지하세요.
- **내비게이션에 표시되는 “Activate” 또는 Kia Connect 안내:** 이 패키지가 아니라 차량의 커넥티드 서비스에서 발생하는 안내입니다.
- **Leafia 키트에서 확인할 수 있는 Android 로그는 최근 약 1분 정도입니다.** 문제를 보고할 때는 문제가 발생한 직후에 키트를 실행하세요.

문제가 있나요? [문제 보고 양식](../../issues/new?template=problem.yml)으로 이슈를 작성하세요. 양식에서 Leafia 키트 사용 절차를 안내합니다.

## 패키지

- **`packages/wireless-carplay-aa`:** 무선 CarPlay/AA용 NEMESIS 패키지의 소스입니다. 수정된 순정 파일 자체는 배포하지 않습니다. 네이티브 라이브러리는 헤드유닛에서 `lpatch` 레시피로 패치하며, 폰 프로젝션 앱은 `patches/`의 패치 세트를 사용해 해당 기기의 순정 파일로 기기에서 다시 빌드합니다.

## 지원 헤드유닛

[호환성 페이지](https://vyssecodes.github.io/HMG-Leafia-Plus/)를 확인하세요. 호환성 데이터는 `docs/data/compat.json`(지원 빌드가 있는 차량)과 `docs/data/wanted.json`(지원을 추가하고 싶은 Gen5W 차량)에 있습니다.

**최신 펌웨어만 지원합니다.** 각 차량·지역의 최신 헤드유닛 소프트웨어를 지원합니다. 원문 기준으로 미국은 **260507**, 캐나다는 **260206**입니다. 이전 펌웨어에서는 무선 Android Auto만 설치하는 기본 모드가 적용되며 업데이트를 요청합니다. 무료 현대·기아·제네시스 Navigation Updater로 업데이트한 뒤 다시 설치하세요.

**순정 내비게이션 탑재 사양만 지원합니다.** Gen5W는 내장 내비게이션이 있는 사양에 장착되는 헤드유닛입니다. 내비게이션이 없는 사양은 다른 헤드유닛을 사용합니다. 예를 들어 투싼의 “Display Audio Gen2V” 같은 “Display Audio” 기기는 NEMESIS와 이 패키지에서 지원하지 않습니다.

**한국:** 한국 헤드유닛의 보고서를 받고 있지만, 아직 정상 작동이 확인된 한국 차량은 한 대도 없습니다. 지금까지 확인한 한국 헤드유닛에는 모두 무선 CarPlay와 Android Auto에 필요한 Wi-Fi 하드웨어가 없었습니다.

## Leafia 키트(USB 드라이브에서 NEMESIS를 통해 실행)

읽기 전용 키트 하나(`kits/leafia`)로 차량 호환성 확인·문제 보고·새 차종 지원 작업을 수행합니다. 같은 소스에서 수집 범위가 다른 네 가지 버전을 만들며, 각 다운로드에 포함된 `LEAFIA-LEVEL` 파일이 수집 범위를 지정합니다.

| 다운로드 | 수집 항목 | 용도 |
|---|---|---|
| [leafia-kit-quick.zip](https://vyssecodes.github.io/HMG-Leafia-Plus/downloads/leafia-kit-quick.zip) | `public/`만 수집 | 차량 호환성 확인(수 초) |
| [leafia-kit.zip](https://vyssecodes.github.io/HMG-Leafia-Plus/downloads/leafia-kit.zip) | 위 항목 + `private/logs`(최근 크래시 기록), `private/keys` | 문제 보고 |
| [leafia-kit-port.zip](https://vyssecodes.github.io/HMG-Leafia-Plus/downloads/leafia-kit-port.zip) | 위 항목 + `private/stock`(약 90MB) | 새 차종 지원 추가 |
| [leafia-kit-full.zip](https://vyssecodes.github.io/HMG-Leafia-Plus/downloads/leafia-kit-full.zip) | 위 항목 + 모든 크래시 기록 | 요청받은 경우의 심층 디버깅 |

USB 드라이브의 `LEAFIA/` 폴더에 다음 내용을 저장합니다.

| 폴더 | 내용 | 공유 범위 |
|---|---|---|
| `public/` | `LEAFIA-REPORT.txt`(펌웨어 식별 정보·체크섬·패치 검사 결과. 호환성 페이지에 파일을 끌어다 놓아 사용), `summary.txt`(NEMESIS 및 패키지 상태·핫스팟·크래시 기록 파일명), 프로젝트 설치 로그 | 이슈에 공개 가능 |
| `private/logs/` | Android·커널 로그, NEMESIS 로그, 크래시 덤프, 네트워크 상태. 휴대전화 이름이나 Bluetooth 주소가 포함될 수 있음 | **요청받았을 때만 비공개로 공유** |
| `private/stock/` | 패키지를 해당 차종에 맞게 이식하는 데 사용하는 순정 프레임워크·CarPlay/폰 프로젝션 앱·라이브러리(현대·기아 파일) | **요청받았을 때만 비공개로 공유** |
| `private/keys/` | 펌웨어 키 파일 | **요청받았을 때만 비공개로 공유하며, 절대 공개 게시하지 않음** |

### 데이터 정책

- **공개 가능(이슈·저장소):** 키트의 `public/` 폴더, 레시피, 체크섬, 호환성 데이터.
- **비공개 전용(이 저장소에 커밋 금지):** 키트의 `private/` 폴더(로그·순정 펌웨어 파일·펌웨어 키 파일)와 수정된 앱의 전체 빌드 결과물. 저장소에는 해당 기기의 순정 파일로 앱을 다시 빌드하는 패치 세트만 보관합니다.
- **수집하지 않는 항목:** NEMESIS 자체 폴더·크래시 로그·핫스팟 주소 임대 정보를 제외한 `/data` 내 모든 항목(계정·페어링된 휴대전화·Wi-Fi 비밀번호 포함), 차량 보안 파티션(모뎀 및 커넥티드 서비스 인증서), VIN 및 일련번호.

## 기여하기

새 기능 아이디어가 있나요? [여기에서 제안](../../issues/new?template=feature.yml)하거나, [이미 제안된 아이디어](../../issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)에 👍 반응을 남겨 주세요.

새로운 차량의 보고서, 실제 차량 테스트, 코드 기여를 모두 환영합니다. 개발 환경 설정·빌드·모의 헤드유닛 테스트·새 차종 추가·프로젝트 규칙은 [CONTRIBUTING.md](CONTRIBUTING.md)를 확인하세요. 보안 문제는 [SECURITY.md](SECURITY.md)를 참고하세요.

## 저작자 및 라이선스

- HMG Leafia Plus의 라이선스는 GPL-3.0입니다(`LICENSE` 참고).
- xwtk가 개발한 [NEMESIS](https://github.com/xwtk/hmg_nemesis)를 통해 실행되며, NEMESIS의 라이선스는 AGPL-3.0입니다. NEMESIS 패키지에서 파생된 부분은 `NOTICE.md`에 명시되어 있으며 원래 라이선스를 유지합니다.
- 프로젝트에 도움을 준 [W-Floyd](https://github.com/W-Floyd)에게 감사드립니다.
- 현대·기아·제네시스·Apple·Google과 공식적인 관련이 없습니다. 헤드유닛 수정에 따른 위험과 책임은 사용자에게 있습니다.
