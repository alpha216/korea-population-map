# Korea Population Map

대한민국의 **1992~2025년 주민등록인구 변화**를 연속형 인구 카토그램으로 보여주는 한국어 웹사이트입니다.

인구가 많은 지역이 넓어지도록 해안선과 행정구역 경계, 지리 격자를 함께 변형합니다. 연도 슬라이더와 자동 재생, 지역별 인구 추이, 실제 지형 비교, CSV 내려받기를 제공합니다.

## 기술 구성

HTML, CSS, JavaScript, D3 v7과 정적 JSON 데이터로 작동합니다. **웹사이트 실행 및 배포에는 Python, Node.js 서버, API 키 또는 빌드 과정이 필요하지 않습니다.** D3는 프로젝트에 포함되어 있습니다. 글꼴은 Google Fonts를 사용하며 연결되지 않으면 시스템 글꼴을 사용합니다.

## 파일 구조

```text
korea-population-map/
├── dist/                        # 그대로 배포하는 정적 웹사이트
│   ├── index.html
│   ├── .nojekyll
│   ├── assets/
│   │   ├── css/style.css
│   │   ├── js/app.js
│   │   └── vendor/d3.min.js
│   └── data/
│       ├── population.json      # 연도별 인구·미리 계산한 변형 격자
│       └── boundaries.geojson   # 2013년 행정구역 경계
├── scripts/
│   ├── prepare_cartogram.py     # 데이터 재생성용; 실행·배포에는 불필요
│   └── requirements.txt
├── .github/workflows/pages.yml  # GitHub Pages 자동 배포
├── .gitignore
└── README.md
```

## 로컬 실행

정적 서버에서 `dist`를 제공하면 됩니다. Node.js가 있다면 다음 명령을 사용할 수 있습니다.

```sh
npx --yes serve dist
```

출력된 주소를 브라우저에서 여세요. JSON을 `fetch`로 불러오므로 HTML 파일을 더블클릭하는 방식 대신 HTTP 서버를 사용합니다. VS Code Live Server로 `dist/index.html`을 열어도 됩니다.

## GitHub Pages 배포

1. 이 프로젝트를 GitHub 저장소의 `main` 브랜치에 올립니다.
2. 저장소의 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 선택합니다.
3. `main`에 변경 사항을 푸시하거나 Actions에서 **Deploy Korea Population Map**을 수동 실행합니다.
4. 성공한 작업의 `github-pages` 환경에서 배포 주소를 확인합니다.

GitHub Pages를 사용할 수 있는 저장소/요금제가 필요합니다. 워크플로는 `dist`만 업로드하며 Python을 실행하지 않습니다. 프로젝트 하위 경로에서도 작동하도록 자산 경로는 상대 경로입니다.

Cloudflare Pages 등 다른 정적 호스팅에서도 빌드 명령 없이 출력 폴더를 `dist`로 설정하면 됩니다.

## 데이터 출처와 해석

- 인구: 행정안전부 「주민등록인구현황」, KOSIS 통계표 [DT_1B040A3](https://kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1B040A3&conn_path=I3), 제공된 Final.xlsx의 1992~2025년 연말 자료. 외국인은 제외합니다.
- 경계: [southkorea-maps](https://github.com/southkorea/southkorea-maps)의 2013년 KOSTAT 시도 GeoJSON.
- 시각화 라이브러리: [D3](https://d3js.org/) v7. 포함 파일의 저작권 안내를 유지합니다. 데이터·경계의 재사용 조건은 각 출처를 확인하세요.

모든 연도의 지역별 인구 합계는 전국 인구와 일치합니다. 단, 지역 내부 인구밀도를 균일하다고 가정한 **근사 카토그램**이므로 지도 면적이 인구 비율과 정확히 같지는 않습니다. 초록색 격자는 변형된 지리 격자이며 칸마다 같은 인구 수를 뜻하지 않습니다.

인구는 각 연도의 집계 경계를 따르지만 지도에는 2013년 경계를 고정 사용합니다. 울산은 1997년, 세종은 2012년부터 별도 집계됩니다. 그 이전 지도에서는 각각 경남·충남의 밀도를 근사 적용합니다. 2010년부터 거주불명 등록자가 통계에 포함되는 집계 기준 변화도 있습니다.

## 데이터 다시 만들기 — 선택 사항

이미 생성된 JSON을 사용한다면 이 단계는 필요하지 않습니다. 인구 자료나 계산 방식을 바꿀 때만 실행합니다.

1. 원본 `Final.xlsx`를 프로젝트 루트에 둡니다. 두 전처리 스크립트는 이 파일만 읽습니다.
2. Python 가상 환경에 `scripts/requirements.txt`를 설치합니다.
3. 프로젝트 루트에서 실행합니다.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
python scripts/prepare_cartogram.py
```

스프레드시트는 `.gitignore`로 제외합니다. 재생성된 `dist/data/` 파일을 커밋하면 배포에 반영됩니다. 생성 스크립트는 현재 제공된 엑셀의 행·열 형식을 기준으로 합니다.

## 현재 지도 표시 단위

카토그램과 실제 지형 모두 시·도 단위입니다. 실제 지형은 시·도 총인구를 흰색~주홍색으로 표시하며 시·군·구 상세 색상 모듈은 로드하지 않습니다. 전 연도 고정 범례는 0~1,500만 명입니다. Final.xlsx가 인구 원본이며, 원본의 시·도 인구가 기존 값과 일치함을 확인한 뒤 카토그램 변형 격자를 재사용합니다.

상세 지역 자료와 전처리 스크립트는 추후 검토용으로 보관되어 있지만 현재 지도 실행에 필요하지 않습니다.

## 실제 지형의 이동자 수

지도 도구 오른쪽의 인구 수 / 이동자 수 버튼으로 색상을 전환합니다. 이동 지표는 Movement.xlsx의 순이동(총전입−총전출)이며, 파랑=순유출, 흰색=0, 주홍=순유입입니다. 작은 변화도 구분하도록 −10만 명=하늘색, 0=흰색, +10만 명=주황색으로 설정하고 −40만 명=진한 남색, +40만 명=어두운 빨강으로 이어집니다. 모든 지역과 연도에 같은 기준을 적용합니다. 1992~2025년 공통 범례는 −40만~+40만 명입니다. 자료 변환은 `python scripts/prepare_movement.py`로 수행하며, 브라우저는 생성된 `dist/data/movement.json`만 읽습니다. 모든 연도에서 지역별 전입−전출=순이동과 전국 합계를 검증합니다. 카토그램은 계속 총인구를 기준으로 합니다.
