# 패치 세트

K7 프리미어 작업은 [K7 포팅 안내](../docs/K7_PORTING_ko.md)를 먼저 확인하세요. 아직 K7 패치 세트는 없으며, 아래 범용 절차는 기준 차량의 비공개 순정 자료와 수정 빌드도 필요합니다.

차종별 폴더와 공통 폴더인 `common/`으로 구성됩니다. 헤드유닛은 이 패치 세트를 사용해 자체 순정 파일로 수정된 폰 프로젝션 앱을 다시 빌드합니다(`packages/wireless-carplay-aa/scripts/build.sh` 참고). 따라서 수정된 앱 자체는 배포하지 않습니다.

| 폴더 | 차량 | 펌웨어 |
|---|---|---|
| `ev6/` | 기아 EV6, 미국 사양(`CVEV.USA.*`) | 260507 |
| `ev6_ca/` | 기아 EV6, 캐나다 사양(`CVEV.CAN.*`). 미국 EV6와 코드가 같으므로, 매니페스트에서 `ev6/` 패치를 지정해 캐나다 사양의 순정 APK에 적용합니다. | 260206 |
| `neev/` | 현대 아이오닉 5, 미국 사양(`NEEV.USA.*`, `NEEV23.USA.*`) | 260507 |
| `neev_ca/` | 현대 아이오닉 5, 캐나다 사양(`NEEV.CAN.*`). Android Auto 라이브러리가 미국 사양과 달라 자체 라이브러리 차분 패치를 포함합니다. | 260206 |
| `dl3hev/` | 기아 K5 하이브리드, 한국 사양. 패치 세트는 보관하지만 `cars`에는 등록하지 않았습니다(지금까지 확인한 한국 헤드유닛에서 Wi-Fi 하드웨어가 발견되지 않음). | 260902 |
| `neev_kr/` | 현대 아이오닉 5, 한국 사양. 위와 같은 이유로 패치 세트는 보관하지만 `cars`에는 등록하지 않았습니다. | 260902 |
| `common/` | 미국 사양의 순정 라이브러리와 동일한 파일을 사용하는 모든 차량에 적용할 `libautoreceiver_infobank.so` 패치입니다. 다른 라이브러리를 사용하는 차량은 해당 차종 폴더에 별도 차분 패치를 둡니다. `optional`에는 순정 파일이 일치하는 경우에만 적용하는 수정 사항이 들어 있습니다. | |

`cars`는 펌웨어의 제품 ID 접두사(`ro.build.product`)를 폴더 및 차량 이름과 연결합니다. 설치 프로그램이 이 파일을 읽으므로, 차량을 추가할 때 스크립트를 수정할 필요는 없습니다.

## 파일 구성

- `<App>.tbt.lpd`: 순정 `<App>.odex`를 바탕으로 턴바이턴 안내 기능을 추가한 앱 코드를 다시 빌드합니다.
- `<App>.bridge.lpd`: CarPlay 브리지 기능을 추가한 버전을 다시 빌드합니다. 턴바이턴 안내 기능도 포함합니다.
- `stock`: 해당 차량에 필요한 각 순정 파일의 MD5 값입니다(`<file name> <md5>`).
- `manifest`: 출력 결과물마다 한 줄씩 기록합니다. 형식은 `<part> <app|file> <name> <patch> <md5 of the result>`입니다.

`.lpd`에는 패치에 필요한 정확한 순정 파일의 MD5와 패치 결과물의 MD5가 들어 있습니다. `lpatch delta`는 두 값이 모두 일치하는 경우에만 결과물을 기록합니다.

## 새 차량 추가

새 차량의 소유자에게 **port 버전** Leafia 키트(`leafia-kit-port.zip`)를 실행하고 `LEAFIA/private` 폴더를 비공개로 전달해 달라고 요청합니다. `stock/`에는 폰 프로젝션 앱과 프레임워크가 들어 있습니다. 그런 다음 아래 명령을 실행합니다.

```
tools/port.py --variant <name> --prefix <product prefix> --name "<car name>" --new-stock <dir> --new-fw <LEAFIA/private/stock/framework> --ref-stock <EV6 stock dir> --ref-fw <EV6 framework> --ref-builds <builds dir> --out-builds <dir>
```

`<dir>`에는 새 차량의 `app/<App>.apk`, `app/<App>.odex`, `lib/libautoreceiver_infobank.so` 파일이 있어야 합니다.

도구는 새 차량의 앱과 EV6의 앱을 클래스별로 비교합니다.

- 동일한 클래스나, 서로 다르더라도 이 프로젝트의 수정 사항이 적용되지 않은 클래스는 그대로 사용합니다.
- 이 프로젝트의 수정 사항이 적용된 클래스가 서로 다른 경우, 차이가 멤버 이름 변경뿐이거나(펌웨어 간 난독화 차이), 수정 사항을 3방향 병합 패치로 충돌 없이 적용할 수 있으면 자동으로 병합합니다.
- 그 외의 차이는 이식 작업을 중단하고, 사람이 직접 병합할 수 있도록 목록으로 표시합니다.

이후 모든 결과물을 검사합니다. 앱 내부의 각 참조가 올바른 대상을 가리켜야 하며, 모든 시스템 호출이 새 차량의 프레임워크에 존재해야 합니다. 검사를 모두 통과하면 `patches/<name>/`을 생성하고 차량을 `cars`에 추가합니다. `--out-builds`에 저장되는 전체 빌드 결과물은 비공개로 유지합니다.

이 방식으로 이식한 아이오닉 5의 결과물은 수작업으로 만든 패치 세트와 바이트 단위로 일치하며, K5 하이브리드의 결과물은 클래스 단위로 일치합니다.

## 선택적 수정 사항(`common/optional`)

특정 차종의 폰 프로젝션 앱에 종속되지 않는 수정 사항입니다. `common/optional`에 매니페스트와 같은 한 줄 형식으로 나열합니다. 헤드유닛은 순정 파일이 해당 `.lpd`를 만들 때 사용한 파일과 정확히 일치하는 경우에만 수정 사항을 적용합니다. 일치하지 않으면 건너뛰었다는 로그를 남기고 설치를 계속합니다.

- `HKMC_BtSettings.menu.<stock md5 prefix>.lpd`(구성 요소 `5_menu`): Bluetooth 설정 앱의 순정 버전별로 하나씩 만듭니다. 이 프로젝트의 무선 기능을 활성화하면 설정 > 폰 프로젝션에서 무선 폰 프로젝션 페이지가 열리는데, 이 페이지에는 CarPlay 분할 화면 옵션이 없고 이 프로젝트의 브리지로 페어링한 휴대전화도 표시되지 않습니다. 이 수정 사항은 미국·캐나다 헤드유닛에서 미국 순정 펌웨어처럼 기기 연결 화면이 열리도록 유지합니다. `tools/mkmenu.py <stock dir>`로 해당 차량용 패치를 만들면 이 목록에 항목이 추가됩니다. 헤드유닛은 보유한 순정 파일과 일치하는 첫 번째 항목을 사용합니다.

## 수작업으로 패치 세트 만들기

차량의 순정 파일(`app/<name>.apk`, `app/<name>.odex`, `lib/libautoreceiver_infobank.so`), `2_tbt/<files>` 및 `3_bridge/<files>` 구조로 배치한 수정 빌드 결과물, 호스트에서 실행할 `lpatch`(`tools/lpatch/build.sh`)가 필요합니다. 또한 `pip install --require-hashes -r tools/requirements.txt`로 의존성을 설치해야 합니다.

```
tools/mkpatches.py <ev6|neev|dl3hev> <stock dir> <builds dir> patches
```

설치 프로그램의 순정 파일 체크섬(`comp/2_tbt`)과 예상 앱 체크섬(`comp/3_bridge`)은 새 패치 세트와 일치해야 합니다.
