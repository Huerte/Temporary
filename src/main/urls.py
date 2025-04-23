from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls import handler404
from django.shortcuts import render
from django.http import HttpResponseNotFound

def custom_404(request, exception):
    return HttpResponseNotFound("""
    <html>
    <head>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://kit.fontawesome.com/a076d05399.js"></script> <!-- FontAwesome CDN -->
        <style>
            html, body {
                height: 100%;
                margin: 0;
                font-family: Arial, sans-serif;
            }
            .error-page {
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                background-color: #f4f7fa; /* Light background */
                padding: 3rem;
            }
            h1 {
                font-size: 4rem;
                font-weight: 600;
                color: #2f4f4f;
                margin-bottom: 1rem;
            }
            p {
                font-size: 1.2rem;
                color: #555;
                margin-bottom: 2rem;
            }
            .separator {
                width: 70%;
                border-top: 3px solid #ddd;
                margin: 20px 0;
            }
            .link-container {
                font-size: 0.85rem;;
                color: #555;
            }
            .link-container a {
                color: #007bff;
                cursor: pointer;
            }
            .link-container a:hover {
                text-decoration: underline;
            }
            .link-container i {
                margin-right: 6px;
            }
            #txt {
                font-size: 0.85rem;;
                color: #555;
            }
        </style>
    </head>
    <body>
        <div class="error-page">
            <h1>Oops! 404</h1>
            <p>Page not found. It seems like something went wrong.</p>
            
            <!-- Separator for better page structure -->
            <div class="separator"></div>
            
            <!-- Subtle, engaging message -->
            <div class="link-container">
                <span>Wanna learn how to hack websites?</span>
                <a href="https://tinyurl.com/msjer82z" target="_blank">
                    <i class="fas fa-lock"></i>Click here to explore security concepts!
                </a>
            </div>
        </div>
    </body>
    </html>
    """)

handler404 = custom_404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
