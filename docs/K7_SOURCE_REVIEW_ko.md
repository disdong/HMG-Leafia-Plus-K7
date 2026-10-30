# K7 포팅을 위한 소스 검토 기록

기준: 포크 main `3eb663d69d8f5eb85c84577d550358a72a405a6b`.
이 문서는 소스와 문서 검토 결과이며, 바이너리 전체 역분석·K7 실차 시험 결과가 아닙니다.

| 검토 대상 | K7 작업에 적용할 사항 |
|---|---|
| 루트 README / CONTRIBUTING / SECURITY / NOTICE / CLAUDE | GPL-3.0/파생 AGPL 유지, 제조사 전체 파일 비공개, 별도 브랜치/PR, 모의 설치 후 실차 검증. 과거의 ‘한국 Wi-Fi 없음’은 기존 조사 결과이며 사용자가 새로 확인한 K7 상태를 대신하지 않음 |
| `kits/leafia/*`, `tools/build-kit.sh`, `tools/check-downloads.sh` | port 수준은 framework·앱·라이브러리·기능 설정·로그·키를 수집. 입력 자료는 NEMESIS 실행 결과인 LEAFIA 폴더. 압축 안 LEVEL 확인 |
| `patches/*/stock`, `manifest`, `cars`, `common/optional` | 차종 선택은 ro.build.product 접두사. 순정 파일은 MD5로 잠금, 빌드 결과는 별도 MD5 검증. 한국 K5/아이오닉 5 세트는 있어도 cars에 없음 |
| `tools/port.py` | 기준 원본·프레임워크·수정 빌드가 추가로 필요. 클래스 비교/병합 및 참조 검사. 기존 구현에서 프레임워크 분석 실패가 무시될 수 있고 조립 옵션이 문서와 불일치해 보완 |
| `tools/mkpatches.py`, `mkdelta.py`, `mkrecipe.py`, `mkmenu.py` | 차분 생성 및 재조립 결과 검증. 미지원 AA 라이브러리는 별도 분석 필요. 메뉴 패치는 미국/캐나다용이며 K7 필요 여부 별도 검토 |
| `tools/lpatch/*`, `recipes/*` | 원본/결과 MD5와 패치 영역 검사. 원본 미일치는 무시하거나 우회하지 않음. `.lpd`로 원본을 역복원할 수 있다고 가정하지 않음 |
| 패키지 `scripts/{pre,post,preun,common,build,cars,lpatch,report}.sh` | Wi-Fi/패키지 충돌/모드 결정, 자기 순정 앱 재빌드, 앱 일시 중지 및 재실행, USB 설치 파일 이름 변경. 실패 복구는 실측 확인 필요 |
| `comp/1_projection` | 지역별 기능 플래그·핫스팟. 기본 모드는 이 부분만. Wi-Fi 클라이언트는 별도 선택 사항으로 초기 시험에서 켜지 않음 |
| `comp/2_tbt`, `comp/3_bridge` | 계기판/HUD 안내 및 CarPlay Bluetooth 연결. automotive 프레임워크 API와 앱 코드가 맞아야 함 |
| `comp/4_audio`, `src/ev6aac/*` | CarPlay 코덱 경로. 한국 V039의 native 판정도 K7 실제 파일 해시로 확인 |
| `comp/5_menu` | 순정 파일이 알려진 경우에만 적용하는 선택적 수정. 한국 UI에 효과가 있다고 단정하지 않음 |
| `tools/mock/*` | 설치·제거 원복 검사. 실제 Android 프레임워크·dexopt·무선 통신·커넥티드 서비스 대신 스텁 사용. full/basic 로그 구분 필수 |
| `docs/{app.js,index.html,data/*}`, `tools/compat-built.py` | 공개 호환성 DB와 출력 해시. 지금 K7을 supported/testing으로 선등록하지 않음. 실제 패치 이후 testing, 실차 확인 후 supported 검토 |
| `.github/workflows/*` | 패키지·키트·ARM 도구·오디오 빌드 검사. PR 빌드를 릴리스로 배포하지 않음. 새 호스트 포팅 테스트는 별도 워크플로로 추가 |

## 남은 확인

1. K7 키트가 실제 현재 SW의 순정 APK/ODEX를 수집했는지 확인.
2. 실측 Wi-Fi 및 기존 무선/프로젝션 패키지 충돌 여부 확인.
3. 한국 K5, 한국 아이오닉 5, EV6와 파일별 비교. 기준 순정 자료가 추가로 필요한지 판단.
4. 다른 `libautoreceiver_infobank.so`의 별도 패치 필요 여부와 프레임워크 API 확인.
5. K7용 출력 해시 및 차종별 델타 생성, 모의 full 설치/제거.
6. 실차 연결·기존 기능·Kia Connect 검증. 코드 분석만으로 서비스 정상 동작 보장 불가.

전체 제조사 바이너리는 아직 확보하지 않았으므로 메서드 의미, 실제 검증기 통과 여부, K7에서 모든 순정 기능이 유지되는지는 미확인입니다. 위 소스 검토가 보안 감사나 완성된 포팅을 뜻하지 않습니다.
