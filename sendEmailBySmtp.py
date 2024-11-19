import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
global smtp_config
import mysqlDB as msq
smtp_config = {
    'smtp_server': msq.connect_to_database(f'SELECT config_smtp_server FROM newsletter_setting;')[0][0],
    'smtp_port': msq.connect_to_database(f'SELECT config_smtp_port FROM newsletter_setting;')[0][0],  # Domyślny port dla TLS
    'smtp_username': msq.connect_to_database(f'SELECT config_smtp_username FROM newsletter_setting;')[0][0],
    'smtp_password': msq.connect_to_database(f'SELECT config_smtp_password FROM newsletter_setting;')[0][0]
}



def send_html_email(subject, plain_body, to_email):
    try:
        # Utwórz wiadomość
        message = MIMEMultipart()
        smtp_server = smtp_config['smtp_server']
        smtp_port =smtp_config['smtp_port']
        smtp_username = smtp_config['smtp_username']
        smtp_password = smtp_config['smtp_password']
        message["From"] = smtp_username
        message["To"] = to_email
        message["Subject"] = subject
        

        # Dodaj treść plain
        message.attach(MIMEText(plain_body, "plain"))

        # Utwórz połączenie z serwerem SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Rozszerzenie STARTTLS
            server.starttls()
            # Zaloguj się do konta SMTP
            server.login(smtp_username, smtp_password)

            # Wyślij wiadomość
            server.sendmail(smtp_username, to_email, message.as_string())
        return f'success'
    except Exception as e:
        return f'Wysyłanie maila do {to_email} nieudane: {e}'


