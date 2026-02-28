import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY                = os.getenv('SECRET_KEY', 'fallback-secret')
    SQLALCHEMY_DATABASE_URI   = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY            = os.getenv('JWT_SECRET_KEY', 'fallback-jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 1800)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 604800)))
    JWT_TOKEN_LOCATION        = ['headers']
    JWT_COOKIE_SECURE         = False
    PAYSTACK_SECRET_KEY       = os.getenv('PAYSTACK_SECRET_KEY')
    PAYSTACK_BASE_URL         = os.getenv('PAYSTACK_BASE_URL', 'https://api.paystack.co')
    CELERY_BROKER_URL         = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND     = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CORS_ORIGINS              = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    JWT_COOKIE_SECURE = True

config = {
    'development':  DevelopmentConfig,
    'production':   ProductionConfig,
    'default':      DevelopmentConfig
}
