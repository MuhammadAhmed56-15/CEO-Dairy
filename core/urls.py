# Add this to your urls.py file

from django.urls import path
from . import views
from .views import approve_commitment, reject_commitment

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboards
    path('ps/', views.ps_dashboard, name='ps_dashboard'),
    path('ceo/', views.ceo_dashboard, name='ceo_dashboard'),
    path('manager/', views.manager_dashboard, name='manager_dashboard'),

    # Chart Data API Endpoints
    path('api/chart-data/', views.get_chart_data, name='get_chart_data'),  # CEO Chart API
    path('api/ps-chart-data/', views.get_ps_chart_data, name='get_ps_chart_data'),  # PS Chart API
    
    # Commitments
    path('commitment/add/', views.add_commitment, name='add_commitment'),
    path('commitment/edit/<int:pk>/', views.edit_commitment, name='edit_commitment'),
    path('commitment/delete/<int:pk>/', views.delete_commitment, name='delete_commitment'),
    path('commitment/list/', views.commitment_list, name='commitment_list'),
    path('commitment/report/', views.commitment_report, name='commitment_report'),
    
    # Status Updates
    path('update-status/<int:pk>/<str:status>/', views.update_status, name='update_status'),
    path('approve/<int:id>/', approve_commitment, name='approve_commitment'),
    path('reject/<int:id>/', reject_commitment, name='reject_commitment'),
    
    # Manager Tasks
    path('manager/tasks/', views.manager_task_view, name='manager_tasks'),
    path('manager/add-remark/', views.add_remark_view, name='add_remark'),
    
    # Task Assignment
    path('assign-task/', views.assign_task_view, name='ceo_assign_task'),
    path('all-tasks/', views.all_tasks_view, name='all_tasks'),
    
    # CEO Feedbacks
    path('ceo/view-feedbacks/', views.ceo_view_feedbacks, name='ceo_view_feedbacks'),
    path('ceo/feedbacks/', views.ceo_view_feedbacks, name='ceo_view_feedbacks'),
]