from django.conf.urls import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # My urls
    url(r'^', include('competencies.urls', namespace='competencies')),
                       
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # Auth urls
    url(r'^login/', 'django.contrib.auth.views.login', name='login'),
    url(r'^logout/', 'competencies.views.logout_view', name='logout_view'),
)

# heroku static files:
urlpatterns += patterns('',
    (r'^static/(.*)$', 'django.views.static.serve',
     {'document_root': settings.STATIC_ROOT}),
)
