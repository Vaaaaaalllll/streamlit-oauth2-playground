from .google_analytics import GoogleAnalyticsProvider
from .facebook import FacebookProvider

__all__ = ['GoogleAnalyticsProvider', 'FacebookProvider']

PROVIDERS = {
    'Google Analytics': GoogleAnalyticsProvider,
    'Facebook': FacebookProvider,
}
