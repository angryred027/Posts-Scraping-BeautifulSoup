import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from html import escape
from datetime import datetime
from utils.time_convert import format_human_time

class EmailSender:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        sender: str,
        recipients: List[str],
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender
        self.recipients = recipients

    def send_email(self, subject: str, posts: List[Dict]):
        html_body = self._build_html(posts)

        msg = MIMEMultipart("alternative")
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        msg["Subject"] = subject

        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(self.host, self.port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(
                self.sender,
                self.recipients,
                msg.as_string()
            )

            log_debug(f"Sent email to {len(self.recipients)} recipients with subject: {subject}")

    def _build_html(self, posts: List[dict]) -> str:
        rows = []

        for post in posts:
            rows.append(f"""
                    <tr>
                        <td style="border-bottom: 1px solid #e5e7eb;">
                            <table width="100%" cellpadding="12" cellspacing="0" border="0">
                                <tr>
                                    <td valign="top" style="width: 50%; padding: 12px 16px;">
                                        <a href="{escape(post['url'])}" style="color: #4f7cba; font-size: 16px; text-decoration: none; font-weight: normal; display: block; margin-bottom: 6px;">
                                            {escape(post['title'])}
                                        </a>
                                        <div style="font-size: 12px; color: #6b7280; line-height: 1.5;">
                                            {escape(post['author'])}
                                        </div>
                                    </td>
                                    <td valign="top" style="width: 25%; padding: 12px 16px; text-align: right;">
                                        <div style="font-size: 12px; color: #4b5563; margin-bottom: 4px;">
                                            <span style="color: #6b7280;">Replies:</span> <strong>{escape(str(post['replies']))}</strong>
                                        </div>
                                        <div style="font-size: 12px; color: #4b5563;">
                                            <span style="color: #6b7280;">Views:</span> <strong>{escape(str(post['views']))}</strong>
                                        </div>
                                    </td>
                                    <td valign="top" style="width: 25%; padding: 12px 16px; text-align: right;">
                                        <div style="font-size: 12px; color: #4f7cba; margin-bottom: 4px;">
                                            {escape(format_human_time(post['published_at']))}
                                        </div>
                                        <div style="font-size: 12px; color: #6b7280;">
                                            Intent Score: {escape(str(post['intent_score']))}
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
            """)

        return f"""
          <!DOCTYPE html>
          <html lang="en">
          <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
          </head>
          <body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f3f4f6;">
                  <tr>
                      <td align="center" style="padding: 20px 10px;">
                          <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width: 1200px; background-color: #ffffff; border: 1px solid #e5e7eb;">
                              {''.join(rows)}
                          </table>
                      </td>
                  </tr>
              </table>
          </body>
          </html>
          """

       