# Jekyll용 Google Analytics

현재 Korea Population Map은 Jekyll 빌드 없이 `dist`를 정적으로 배포합니다. 실제 페이지의 태그는 `dist/index.html`에 이미 포함되어 있습니다. `dist/.nojekyll`은 빈 파일로 유지합니다.

별도의 Jekyll 사이트에 같은 측정 ID(`G-84H7RZYG6J`)를 적용하려면:

1. `_includes/google-analytics.html`을 대상 Jekyll 프로젝트의 `_includes/` 폴더에 복사합니다.
2. 공통 레이아웃 또는 head 템플릿의 `</head>` 바로 앞에 다음을 추가합니다.

```liquid
{% include google-analytics.html %}
```

한 페이지에 태그를 중복 삽입하지 마세요. 기존 테마가 같은 측정 ID의 Analytics 태그를 이미 삽입한다면 한 방식만 사용합니다.

이 폴더는 Jekyll용 템플릿이며 현재 정적 사이트 배포 과정에서는 사용하지 않습니다.
