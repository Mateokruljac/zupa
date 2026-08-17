from django.urls import path

from . import api_views, views

app_name = 'pastoral'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('theme/save/', views.save_theme_view, name='save_theme'),
    path('api/parish-data/', api_views.parish_data_api, name='parish_data'),
    path('api/search/', api_views.search_api, name='search_api'),
    path('api/action/', api_views.parish_action_api, name='parish_action'),
    path('api/otp/send/', api_views.send_otp_api, name='send_otp_api'),
    path('api/liturgical/year/<int:year>/', api_views.liturgical_year_api, name='liturgical_year'),
    path('api/liturgical/day/<str:iso>/', api_views.liturgical_day_api, name='liturgical_day'),
    path('api/liturgical/romcal/day/<str:iso>/', api_views.liturgical_romcal_day_api, name='liturgical_romcal_day'),
    path('api/liturgical/compare/<str:iso>/', api_views.liturgical_compare_api, name='liturgical_compare'),
    path('api/liturgical/v1/', api_views.liturgical_v1_info_api, name='liturgical_v1_info'),
    path('api/liturgical/v1/day/<str:iso>/', api_views.liturgical_v1_day_api, name='liturgical_v1_day'),
    path('api/liturgical/month/<int:year>/<int:month>/', api_views.liturgical_month_api, name='liturgical_month'),
    path('app/', views.app_view, name='app'),
    path('pages/<slug:page>/', views.admin_page_view, name='page'),
    path('public/', views.public_index_view, name='public_index'),
    path('public/<slug:form>/', views.public_form_view, name='public_form'),
    path('login.html', lambda r: views.legacy_redirect(r, 'login.html')),
    path('app.html', lambda r: views.legacy_redirect(r, 'app.html')),
    path('index.html', lambda r: views.legacy_redirect(r, 'index.html')),
    path('pages/<slug:page>.html', lambda r, page: views.legacy_redirect(r, f'pages/{page}.html')),
    path('public/index.html', lambda r: views.legacy_redirect(r, 'public/index.html')),
    path('public/<slug:form>.html', lambda r, form: views.legacy_redirect(r, f'public/{form}.html')),
]
