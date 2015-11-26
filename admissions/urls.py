from django.conf.urls import url, include

from . import views

class api:
  urlpatterns = [
    url(r'^states/$', views.api_student_states, name='api_all_student_states'),
    url(r'^(?P<college_code>[a-z]{3})/states/$', views.api_student_states, name='api_student_states'),
    url(r'^collegelist/$', views.api_get_colleges),
  ]

urlpatterns = [
  url(r'^$', views.index, name='index'),
  url(r'^api/', include(api)),
  url(r'^apps/all/$', views.all_applicants, name='all_applicants'),
  url(r'^apps/active/$', views.active_applicants, name='active_applicants'),
  url(r'^apps/(?P<college_code>[a-z]{3})/$', views.college_applicants, name='college_applicants'),
  url(r'^colleges/$', views.college_list, name='colleges'),
  url(r'^college/(?P<college_code>[a-z]{3})/$', views.view_or_edit_college, name="edit_college"),
  url(r'^shortlist/$', views.view_shortlist_report, name="view_shortlist"),
  url(r'^teams/(?P<college_code>[a-z]{3})/$', views.view_or_edit_teams, name="edit_teams"),
  url(r'^schedule/(?P<college_code>[a-z]{3})/$', views.view_schedule, name="view_schedule"),
  url(r'^schedule/(?P<team_pk>[0-9]+)/$', views.view_or_edit_schedule, name="edit_schedule"),
  url(r'^schedule/t/(?P<team_pk>[0-9]+)/$', views.view_team_schedule, name="view_team_schedule"),
  url(r'^schedule/c/($P<candidate_pk>[0-9]+)/$', views.view_candidate_schedule, name="view_candidate_schedule"),
  url(r'^schedule/notes/$', views.notes_schedule, name='notes_schedule'),
  url(r'^notes/$', views.notes, name='notes'),
]
