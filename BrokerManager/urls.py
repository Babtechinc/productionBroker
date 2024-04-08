"""
URL configuration for productionBroker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import path

from BrokerManager import views

urlpatterns = [
    path('start-production/', views.start_production, name='start_production'),
    path('single-report/', views.singlereport_production, name='singlereport_production'),
    path('report/full', views.fullreport_production, name='fullreport_production'),
    path('single-report/<str:node>', views.singlereport_production_node, name='singlereport_production_node'),
    path('single-report/label/<str:nodeid>', views.singlereport_production_label, name='singlereport_production_label'),
    path('single-report/label/<str:nodeid>/action', views.singlereport_production_label_action, name='singlereport_production_label_action'),
    path('start-production/node/all', views.start_all_node_production, name='start_all_node_production'),
    path('start-production/node', views.start_one_node_production, name='start_one_node_production'),
    path('logistics-dashboard/', views.logistics_dashboard_view, name='logistics_dashboard'),

]