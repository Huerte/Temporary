from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.utils.text import slugify
from django.conf import settings
import logging
import random


logger = logging.getLogger(__name__)

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True  # Enables auto-signup
    
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        logger.debug(f"User data: {sociallogin.account.extra_data}")
        
        if not user.username:
            base = slugify(user.first_name or sociallogin.account.extra_data.get("name", "user"))
            user.username = f"{base}{random.randint(1000, 9999)}"
        
        if not user.email:
            user.email = sociallogin.account.extra_data.get("email", f'{user.username}@autogen.local')
        
        logger.debug(f"User populated: {user}")
        return user

    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            logger.debug("User already exists. Skipping sign-up.")
            return  # User exists, skip sign-up process
        else:
            logger.debug("Proceeding with pre-social login.")
            user = sociallogin.user
            if user and not user.is_authenticated:
                sociallogin.connect(request, user)
            return sociallogin
        
    def get_signup_redirect_url(self, request):
        return settings.LOGIN_REDIRECT_URL