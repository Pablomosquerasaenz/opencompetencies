from django.conf.urls import patterns, url

from competencies import views

urlpatterns = patterns('',
    # My urls

    # --- Open Competencies home page ---

    url(r'^$', views.index, name='index'),


    # --- Simple views of competency system; no opportunity to modify system ---

    # schools: List of all schools participating in Open Competencies
    url(r'^schools/$', views.schools, name='schools'),

    # school: Detail view for a school, showing subject areas.
    url(r'^schools/(?P<school_id>\d+)/$', views.school, name='school'),

    # sa_summary/id: Show a GSP-style summary for a given subject area.
    url(r'^sa_summary/(?P<sa_id>\d+)/$', views.sa_summary, name='sa_summary'),


    # --- Edit system pages ---

    # edit_sa_summary/id: Edit a GSP-style summary for a given subject area.
    url(r'^edit_sa_summary/(?P<sa_id>\d+)/$', views.edit_sa_summary, name='edit_sa_summary'),                       


    # --- New element pages ---

    # new_school: Create a new school.
    url(r'^new_school/$', views.new_school, name='new_school'),

    # new_sa: Create a new sa, for a specific school.
    url(r'^new_sa/(?P<school_id>\d+)/$', views.new_sa, name='new_sa'),

    # new_sda: Create a new sda, for a specific subject area.
    url(r'^new_sda/(?P<sa_id>\d+)/$', views.new_sda, name='new_sda'),

    # new_gs: Create a new grad std, for a specific general subject area.
    url(r'^new_gs/(?P<sa_id>\d+)/$', views.new_gs, name='new_gs'),

    # new_sda_gs: Create a new grad std, for a specific subdiscipline area.
    url(r'^new_sda_gs/(?P<sda_id>\d+)/$', views.new_sda_gs, name='new_sda_gs'),

    # new_pi: Create a new perf ind(eu), for a specific grad standard (ca).
    url(r'^new_pi/(?P<ca_id>\d+)/$', views.new_pi, name='new_pi'),
                       

    # --- Authorization pages ---

    # no_edit_permission: Message that user does not have permission required to edit current elements.
    url(r'^no_edit_permission/(?P<school_id>\d+)/$', views.no_edit_permission, name='no_edit_permission'),


)
