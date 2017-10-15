# Sendgrid Configuration
import os

EMAIL_BACKEND = "sgbackend.SendGridBackend"

SENDGRID_USER = os.getenv('ASISTIA_SENDGRID_USERNAME')
SENDGRID_PASSWORD = os.getenv('ASISTIA_SENDGRID_PASSWORD')
