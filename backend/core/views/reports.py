"""
GET /api/reports/<kind>/?format=xlsx|pdf&date_from=&date_to=&shop=

Один диспетчер — на четыре отчёта (sales / stock / forecast / xyz).
Возвращает файл (XLSX по умолчанию).
"""

from urllib.parse import quote

from django.http import Http404, HttpResponse
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.views import APIView

from core.reports import ForecastReport, SalesReport, StockReport, XYZReport
from core.reports.renderers import render_pdf, render_xlsx
from core.views.sales_common import resolve_period, validate_shop


KIND_TO_BUILDER = {
    "sales":    SalesReport,
    "stock":    StockReport,
    "forecast": ForecastReport,
    "xyz":      XYZReport,
}

ALLOWED_FORMATS = ("xlsx", "pdf")

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PDF_MIME = "application/pdf"


class ReportsView(APIView):
    def get(self, request: Request, kind: str) -> HttpResponse:
        builder_cls = KIND_TO_BUILDER.get(kind)
        if builder_cls is None:
            raise Http404(f"Неизвестный тип отчёта: {kind}")

        fmt = (request.query_params.get("format") or "xlsx").lower()
        if fmt not in ALLOWED_FORMATS:
            raise ValidationError(
                {"format": f"Допустимые значения: {list(ALLOWED_FORMATS)}"}
            )

        period = resolve_period(
            request.query_params.get("period"),
            request.query_params.get("date_from"),
            request.query_params.get("date_to"),
        )
        shop_id = request.query_params.get("shop") or None
        validate_shop(shop_id)

        builder = builder_cls(
            date_from=period.date_from,
            date_to=period.date_to,
            shop_id=shop_id,
        )
        report = builder.build()

        if fmt == "xlsx":
            content = render_xlsx(report)
            mime = XLSX_MIME
            ext = "xlsx"
        else:
            content = render_pdf(report)
            mime = PDF_MIME
            ext = "pdf"

        filename = f"{kind}_{period.date_from.isoformat()}_{period.date_to.isoformat()}.{ext}"
        encoded = quote(filename)

        response = HttpResponse(content, content_type=mime)
        response["Content-Disposition"] = (
            f"attachment; filename=\"{filename}\"; filename*=UTF-8''{encoded}"
        )
        response["Content-Length"] = str(len(content))
        return response
