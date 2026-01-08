from .google_analytics import GoogleAnalyticsProvider

__all__ = ['GoogleAnalyticsProvider']

PROVIDERS = {
    'Google Analytics': GoogleAnalyticsProvider,
}
