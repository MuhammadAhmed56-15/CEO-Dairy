from django.urls import path
from . import views

urlpatterns = [

    # Log Book URLs
    path('', views.logbook_list, name='logbook_list'),
    path('create/', views.create_logbook, name='create_logbook'),
    path('<int:logbook_id>/', views.logbook_detail, name='logbook_detail'),
    path('<int:logbook_id>/add-entry/', views.add_logbook_entry, name='add_logbook_entry'),

    # Vehicle URLs
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/create/', views.vehicle_create, name='vehicle_create'),
    path('vehicles/<int:pk>/edit/', views.vehicle_edit, name='vehicle_edit'),
    path('vehicles/<int:pk>/delete/', views.vehicle_delete, name='vehicle_delete'),
    # Vehicle LogBook & Pages URLs
    path('vehicles/<int:vehicle_id>/logbook/', views.vehicle_logbook, name='vehicle_logbook'),
    path('vehicles/<int:vehicle_id>/add-page/', views.add_logbook_page, name='add_logbook_page'),
    path('vehicles/<int:vehicle_id>/print-all/', views.print_all_logbook_pages, name='print_all_logbook_pages'),
    path('pages/<int:page_id>/', views.logbook_page_detail, name='logbook_page_detail'),
    path('pages/<int:page_id>/add-entry/', views.add_page_entry, name='add_page_entry'),
    path('pages/<int:page_id>/delete/', views.delete_logbook_page, name='delete_logbook_page'),

    # Driver URLs
    path('drivers/', views.driver_list, name='driver_list'),
    path('drivers/create/', views.driver_create, name='driver_create'),
    path('drivers/<int:pk>/edit/', views.driver_edit, name='driver_edit'),
    path('drivers/<int:pk>/delete/', views.driver_delete, name='driver_delete'),

]

