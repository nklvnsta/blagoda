# Шрифты для PDF-отчётов

PDF-рендерер ожидает в этой папке файл `DejaVuSans.ttf` (с поддержкой кириллицы).

## Где скачать

Официальный сайт DejaVu Fonts: https://dejavu-fonts.github.io/

Прямые ссылки на актуальный релиз:

- https://github.com/dejavu-fonts/dejavu-fonts/releases — архив `dejavu-fonts-ttf-2.37.zip`
- внутри архива: `ttf/DejaVuSans.ttf` (≈760 KB)

Положить файл как:

```
backend/core/reports/renderers/fonts/DejaVuSans.ttf
```

## Что будет, если шрифта нет

PDF всё равно сгенерируется (рендерер делает fallback на встроенный `Helvetica`),
но кириллические символы будут показаны как пустые квадратики. XLSX это не
затрагивает — он не использует TTF из этой папки.

## Лицензия

DejaVu Fonts распространяются под Bitstream Vera/DejaVu License — свободное
использование, в том числе коммерческое; см. `LICENSE` в архиве дистрибутива.
