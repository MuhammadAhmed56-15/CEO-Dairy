from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Include your app URLs (assuming your app is named 'core')
    path('', include('core.urls')),  
   path("", include("core.urls")),

 

]
