import os
import smtplib
from pathlib import Path
from datetime import datetime
from email.message import EmailMessage

import arabic_reshaper
from bidi.algorithm import get_display

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


class ReportManager:
    BASE_DIR = Path(__file__).resolve().parent
    REPORT_DIR = BASE_DIR / "reports"
    FONT_PATH = BASE_DIR / "assets" / "Vazirmatn-Regular.ttf"

    STORE_NAMES = {
        "digikala": "دیجی‌کالا",
        "torob": "ترب",
        "technolife": "تکنولایف",
    }

    def __init__(self, report_data):
        self.report_data = report_data
        self.pdf_path = None

    @staticmethod
    def shape_text(text):
        reshaped_text = arabic_reshaper.reshape(str(text))
        return get_display(reshaped_text)

    def generate_report(self):
        try:
            pdf_path = self.generate_pdf()

        except Exception as error:
            print(f"PDF generation failed: {error}")
            return None

        if self.email_is_configured():
            try:
                self.send_email(pdf_path)
            except Exception as error:
                print(f"Email sending failed: {error}")

        else:
            print("Email configuration not found. Skipping email delivery.")

        return pdf_path

    def generate_pdf(self):
        self.REPORT_DIR.mkdir(parents=True, exist_ok=True)

        if not self.FONT_PATH.exists():
            raise FileNotFoundError(
                f"Persian font not found: {self.FONT_PATH}"
            )

        if "PersianFont" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(
                TTFont("PersianFont", str(self.FONT_PATH))
            )

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.pdf_path = self.REPORT_DIR / f"price_report_{timestamp}.pdf"

        document = SimpleDocTemplate(
            str(self.pdf_path),
            pagesize=landscape(A4),
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "PersianTitle",
            parent=styles["Title"],
            fontName="PersianFont",
            fontSize=18,
            leading=25,
            alignment=TA_CENTER,
        )

        cell_style = ParagraphStyle(
            "PersianCell",
            fontName="PersianFont",
            fontSize=10,
            leading=15,
            alignment=TA_RIGHT,
        )

        header_style = ParagraphStyle(
            "PersianHeader",
            fontName="PersianFont",
            fontSize=10,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.white,
        )

        story = []

        title = self.shape_text("گزارش پایش قیمت محصولات")
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 8 * mm))

        report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        date_text = self.shape_text(f"تاریخ گزارش: {report_date}")

        story.append(Paragraph(date_text, cell_style))
        story.append(Spacer(1, 6 * mm))

        table_data = [[
            Paragraph(self.shape_text("نام محصول"), header_style),
            Paragraph(self.shape_text("دیجی‌کالا"), header_style),
            Paragraph(self.shape_text("ترب"), header_style),
            Paragraph(self.shape_text("تکنولایف"), header_style),
        ]]

        for product in self.report_data:
            row = [
                Paragraph(
                    self.shape_text(product["name"]),
                    cell_style
                )
            ]

            for store_name in self.STORE_NAMES:
                price = product.get(f"{store_name}_price")

                price_text = (
                    f"{price:,} تومان" if price is not None else "-"
                )

                row.append(
                    Paragraph(
                        self.shape_text(price_text),
                        cell_style
                    )
                )

            table_data.append(row)

        table = Table(
            table_data,
            colWidths=[85 * mm, 45 * mm, 45 * mm, 45 * mm],
            repeatRows=1,
        )

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495E")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5D8DC")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ]))

        story.append(table)

        document.build(story)

        print(f"PDF report saved: {self.pdf_path}")

        return self.pdf_path

    @staticmethod
    def email_is_configured():
        required_fields = (
            "SMTP_HOST",
            "SMTP_PORT",
            "SMTP_USERNAME",
            "SMTP_PASSWORD",
            "EMAIL_FROM",
            "EMAIL_TO",
        )

        return all(os.getenv(field) for field in required_fields)

    @staticmethod
    def send_email(pdf_path):
        message = EmailMessage()

        message["Subject"] = "Price Monitoring Report"
        message["From"] = os.getenv("EMAIL_FROM")
        message["To"] = os.getenv("EMAIL_TO")

        message.set_content(
            "Hello,\n\n"
            "Your latest price monitoring report is attached.\n"
        )

        with open(pdf_path, "rb") as file:
            message.add_attachment(
                file.read(),
                maintype="application",
                subtype="pdf",
                filename=Path(pdf_path).name,
            )

        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(
                os.getenv("SMTP_USERNAME"),
                os.getenv("SMTP_PASSWORD"),
            )
            server.send_message(message)

        print("Email sent successfully.")
