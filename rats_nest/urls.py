"""rats_nest URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include


# # rs @ 27/11
# this is the root urlpatterns, and will be searched first
# having db_output here means that all all http://server/db_output/x
# will be routed to the db_output/urls.py file
# when we need another app (db_input? advanced_stats?) we can keep it separate

urlpatterns = [
    path('admin/', admin.site.urls),
    path('db_output/', include('db_output.urls'))
]
