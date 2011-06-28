from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^media/(?P<path>.*)', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^otus/update/$', 'webui.otus.views.update'),                               
    (r'^otus/dashboard/(?P<dashboardname>.*)$', 'webui.otus.views.indexDashboard'),                           
    (r'^otus/(?P<view_id>.*)$', 'webui.otus.views.index'),                        
)
