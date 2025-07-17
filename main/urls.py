from django.urls import re_path
from . import views

app_name = 'main'

urlpatterns = [
    # Home page
    re_path(r'^$', views.HomeView.as_view(), name='home'),
    
    # Company info
    re_path(r'^about/$', views.AboutView.as_view(), name='about'),
    
    # News
    re_path(r'^news/$', views.ArticleListView.as_view(), name='news'),
    re_path(r'^news/(?P<pk>\d+)/$', views.ArticleDetailView.as_view(), name='article_detail'),
    
    # Dictionary
    re_path(r'^faq/$', views.FAQListView.as_view(), name='faq'),
    
    # Contacts
    re_path(r'^contacts/$', views.ContactsView.as_view(), name='contacts'),
    
    # Privacy policy
    re_path(r'^privacy/$', views.PrivacyPolicyView.as_view(), name='privacy'),
    
    # Jobs
    re_path(r'^jobs/$', views.JobVacancyListView.as_view(), name='jobs'),
    
    # Reviews
    re_path(r'^reviews/$', views.ReviewListView.as_view(), name='reviews'),
    re_path(r'^reviews/add/$', views.ReviewCreateView.as_view(), name='add_review'),
    
    # Promos
    re_path(r'^promos/$', views.PromoListView.as_view(), name='promos'),
    
    # Cars
    re_path(r'^cars/$', views.CarListView.as_view(), name='car_list'),
    re_path(r'^cars/(?P<pk>\d+)/$', views.CarDetailView.as_view(), name='car_detail'),
    re_path(r'^cars/add/$', views.CarCreateView.as_view(), name='car_create'),
    re_path(r'^cars/(?P<pk>\d+)/edit/$', views.CarUpdateView.as_view(), name='car_update'),
    re_path(r'^cars/(?P<pk>\d+)/delete/$', views.CarDeleteView.as_view(), name='car_delete'),
    
    # Rentals
    re_path(r'^rentals/$', views.RentalListView.as_view(), name='rental_list'),
    re_path(r'^rentals/add/$', views.RentalCreateView.as_view(), name='rental_create'),
    re_path(r'^rentals/(?P<pk>\d+)/$', views.RentalDetailView.as_view(), name='rental_detail'),
    re_path(r'^rentals/(?P<pk>\d+)/complete/$', views.complete_rental, name='complete_rental'),
    re_path(r'^rentals/(?P<pk>\d+)/cancel/$', views.cancel_rental, name='cancel_rental'),
    
    # User profile
    re_path(r'^profile/$', views.ProfileView.as_view(), name='profile'),
    re_path(r'^profile/edit/$', views.ProfileEditView.as_view(), name='edit_profile'),
    re_path(r'^profile/change-password/$', views.ChangePasswordView.as_view(), name='change_password'),
    re_path(r'^profile/delete-account/$', views.DeleteAccountView.as_view(), name='delete_account'),
    
    # Authentication
    re_path(r'^login/$', views.CustomLoginView.as_view(), name='login'),
    re_path(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    re_path(r'^register/$', views.RegisterView.as_view(), name='register'),
    
    # Statistics
    re_path(r'^statistics/$', views.StatisticsView.as_view(), name='statistics'),

    # Employee URLs
    re_path(r'^employee/register/$', views.EmployeeRegisterView.as_view(), name='employee_register'),
    re_path(r'^employee/dashboard/$', views.EmployeeDashboardView.as_view(), name='employee_dashboard'),
    re_path(r'^employee/rentals/$', views.EmployeeRentalListView.as_view(), name='employee_rentals'),
    re_path(r'^employee/rentals/create/$', views.employee_rental_create, name='employee_rental_create'),
    re_path(r'^employee/rentals/(?P<pk>\d+)/update/$', views.EmployeeRentalUpdateView.as_view(), name='employee_rental_update'),
    re_path(r'^employee/clients/$', views.EmployeeClientListView.as_view(), name='employee_clients'),
    re_path(r'^employee/clients/create/$', views.employee_client_create, name='employee_client_create'),
    re_path(r'^employee/clients/(?P<pk>\d+)/$', views.EmployeeClientDetailView.as_view(), name='employee_client_detail'),

    # Car model management URLs
    re_path(r'^car-models/add/$', views.CarModelCreateView.as_view(), name='car_model_create'),
    re_path(r'^car-models/(?P<pk>\d+)/edit/$', views.CarModelUpdateView.as_view(), name='car_model_update'),
    
    # Car type management URLs
    re_path(r'^car-types/add/$', views.CarTypeCreateView.as_view(), name='car_type_create'),
    re_path(r'^car-types/(?P<pk>\d+)/edit/$', views.CarTypeUpdateView.as_view(), name='car_type_update'),

    # Debug URL
    re_path(r'^debug/user-info/$', views.debug_user_info, name='debug_user_info'),
] 