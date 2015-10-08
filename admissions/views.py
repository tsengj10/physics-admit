from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from admissions.models import *
from admissions.forms import *
import json
import logging
import datetime

# Create your views here.

# Used for logging events
logger =  logging.getLogger(__name__)

def get_colleges_for_user(u):
    colleges = College.objects.all()
    if u.is_superuser or u.is_staff:
        return colleges
    return [c for g in u.groups.all() for c in colleges if g.name == c.adss_code]

def get_college_codes_for_user(u):
    if u.is_superuser or u.is_staff:
        return ['ALL']
    colleges = College.objects.all()
    clist = []
    for g in u.groups.all():
        for c in colleges:
            if g.name == c.adss_code:
                clist.append(c.adss_code)
    return clist

def get_college_keys_for_user(u):
    colleges = College.objects.all()
    clist = []
    if u.is_superuser or u.is_staff:
        for c in colleges:
            clist.append({ 'c':c.adss_code, 'k':c.key })
    else:
        for c in colleges:
            for g in u.groups.all():
                if g.name == c.adss_code:
                    clist.append({ 'c':g.name, 'k':c.key })
    return clist

#---------------------------------------------------------------
# front pages
#---------------------------------------------------------------

@login_required
def index(request):
    return render(request, 'admissions/consent.html', {});

@login_required
def notes(request):
    return render(request, 'admissions/notes.html', {});

@login_required
def college_list(request):
    colleges = College.objects.all()
    collegedata = {}
    for c in colleges:
        cdata = {
            'np': c.total_places - c.physphil_places,
            'npp': c.physphil_places,
            'op': 0,
            'opp': 0,
            'fp': 0,
            'fpp': 0,
            }
        collegedata[c.adss_code] = cdata
    offers = Offer.objects.all()
    for o in offers:
        c = o.college
        if c.adss_code != None and c.adss_code != '' and not o.deferred_entry:
            offerclass = 'o'
            if hasattr(o,'promoted') and o.promoted:
              offerclass = 'f'
            if o.course_type == Candidate.COURSE_PHYSPHIL_ONLY:
                offertype = 'pp'
            else:
                offertype = 'p'
            collegedata[c.adss_code][offerclass+offertype] = \
                    collegedata[c.adss_code][offerclass+offertype] + 1
    template_values = {
        'colleges': colleges,
        'data': json.dumps(collegedata),
        #'year': present_interview_year(),
        }
    return render(request, 'admissions/colleges.html', template_values);

#---------------------------------------------------------------
# main browsing pages
#---------------------------------------------------------------

@login_required
def all_applicants(request):
  college = { "name": "All including W/D", "adss_code": "APP" }
  return applicant(request, college)

@login_required
def active_applicants(request):
  college = { "name": "All active", "adss_code": "ALL" }
  return applicant(request, college)

@login_required
def college_applicants(request, college_code):
  college = get_object_or_404(College, adss_code=college_code.upper())
  return applicant(request, college)

def applicant(request, college_spec):
  state = OverallState.objects.current()
  ranking_phase = OverallState.objects.current_ranking_phase()
  template_values = {
    'path':request.path,
    'user_colleges':json.dumps(get_college_codes_for_user(request.user)),
    'can_edit':request.user.is_superuser,
    'college':college_spec,
    'present_interview_year':present_interview_year(),
    'state':state,
    'ranking_phase':ranking_phase,
    'state_longlist':(state in [OverallState.LONGLIST,
                                OverallState.DEVELOPMENT]),
    'state_enter_interview_marks':(state in [OverallState.SHORTLIST,
                                             OverallState.DEVELOPMENT]),
    'state_enter_offers':(state in [OverallState.OFFERS,
                                    OverallState.DEVELOPMENT])
    }
  if state == OverallState.SHORTLIST:
    template_values['college_key_list'] = json.dumps(get_college_keys_for_user(request.user))
  return render(request, 'admissions/applicants.html', template_values)

#---------------------------------------------------------------
# college
#---------------------------------------------------------------

@login_required
def view_or_edit_college(request, college_code, return_to=None):
  if not return_to:
    return_to = request.REQUEST.get('next', reverse('admissions:colleges'))
  c = College.objects.get(adss_code=college_code.upper())
  if request.user.has_perm('admissions.change_college') and c in get_colleges_for_user(request.user):
    return edit_college(request, college_code, return_to)
  return view_college(request, college_code, return_to)

@login_required
def view_college(request, college_code, return_to='admissions:colleges'):
  college = College.objects.get(adss_code=college_code.upper())
  template_values = {
      'return_to': return_to,
      'college': college,
      }
  return render(request, 'admissions/view_college.html', template_values)

@permission_required('admissions.change_college')
def edit_college(request, college_code, return_to='admissions:colleges'):
  college = College.objects.get(adss_code=college_code.upper())
  if request.method == 'POST':
    if college not in get_colleges_for_user(request.user):
      return redirect('admissions:edit_teams', **kwargs)
    college_form = CollegeForm(request.POST, instance=college)
    if college_form.is_valid():
      college_form.save()
    kwargs = {
        'college_code': college_code,
        'return_to': return_to,
        }
    all_valid = college_form.is_valid()
    if all_valid:
      return redirect('admissions:edit_college', **kwargs)
  else:
    college_form = CollegeForm(instance=college)
  template_values = {
      'return_to': return_to,
      'college': college,
      'college_form': college_form,
      }
  return render(request, 'admissions/edit_college.html', template_values)

#===============================================================
# API
#===============================================================
#---------------------------------------------------------------
# college list
#---------------------------------------------------------------

def api_get_colleges(request):
    logger.info("api_get_colleges")
    #serializers.serialize('json', colleges, stream=response)
    res = []
    for c in College.objects.all():
        res.append({ 'name': c.name,
                     'adss_code': c.adss_code })
    #logger.info("res = {}".format(res))
    response = JsonResponse({'data':res})
    #logger.info("about to return response")
    return response

#---------------------------------------------------------------
# extract student state from database into array.
# this method shouldn't be accessible outside (so not in urls)
#---------------------------------------------------------------

def extract_student_state(candidate, user):
    #logger.info("extract_student_state")
    overallstate = OverallState.objects.current()
    #logger.info("  overall state = {}".format(overallstate))
    data = {}
    data['pk'] = candidate.pk
    data['id'] = candidate.ucas_id
    if (candidate.course_type == Candidate.COURSE_PHYSPHIL_ONLY or \
        candidate.course_type == Candidate.COURSE_PHYSPHIL_WITH_FALLBACK):
      data['course'] = candidate.course_type
    #logger.info("  pk = {}, ucas_id = {}".format(candidate.pk, candidate.ucas_id))
    cstate = ranked_offers(candidate)
    if cstate == '':
        cstate = candidate.state
        if cstate != Candidate.STATE_WITHDRAWN:
            if cstate == candidate.STATE_APPLIED:
                cstate = ''
            elif cstate == candidate.STATE_SUMMONED:
                cstate = '+' if overallstate == OverallState.LONGLIST else ''
            elif cstate == Candidate.STATE_DESUMMONED:
              cstate = 'Desum'
            if candidate.rescued:
                cstate = cstate + 'R'
            if candidate.reserved:
                cstate = cstate + 'S'

    data['state'] = cstate
    clist = get_college_codes_for_user(user)
    incol1 = "ALL" in clist or candidate.college1 == None or candidate.college1.adss_code in clist
    incol2 = "ALL" in clist or candidate.college2 == None or candidate.college2.adss_code in clist
    visstate = overallstate not in [ OverallState.LONGLIST, OverallState.SHORTLIST ]
    if visstate or incol1:
        if candidate.interview1 > 0:
            data['i1'] = "{}".format(candidate.interview1)
        if candidate.interview2 > 0:
            data['i2'] = "{}".format(candidate.interview2)
        if candidate.interview4 > 0:
            data['i4'] = "{}".format(candidate.interview4)
    if visstate or incol2:
        if candidate.interview3 > 0:
            data['i3'] = "{}".format(candidate.interview3)
        if candidate.interview5 > 0:
            data['i5'] = "{}".format(candidate.interview5)
    if candidate.comments.count() > 0:
        cmts = []
        for c in candidate.comments.all():
            cd = {}
            cd['who'] = c.commenter.get_full_name()
            cd['when'] = "{}".format(c.time)
            cd['t'] = c.text
            cmts.append(cd)
        data['comments'] = cmts
    #logger.info("extract returns {}".format(data))
    return data

def offer_string(offer):
  if hasattr(offer,'promoted') and offer.promoted:
      return '(' + offer.college.adss_code.lower() + ') '
  else:
      return offer.course_type + '[' + offer.college.adss_code + '] '

def ranked_offers(candidate):
    oc = candidate.offer.filter(final=True)
    s = []
    for offer in oc:
      s.append(offer_string(offer))
    ss = ''.join(s)
    if oc.count() > 1:
      logger.error("More than one final offer on candidate " + candidate.ucas_id)
      return "<br>" + ss + "!!!</br>"
    elif oc.count() == 1:
      return ss
    else:
      # one or more offers, but none final
      s = []
      if candidate.course_type == Candidate.COURSE_THREEYEAR or \
         candidate.course_type == Candidate.COURSE_FOURYEAR:
        # physics-only ranking
        ranked_choices = [ '', '', '', '', '', '' ]
        for offer in candidate.offer.order_by('time'):
          c = offer.college
          offs = offer_string(offer)
          #logger.info('offer for ' + candidate.info.surname + ': ' + offs)
          if hasattr(offer,'promoted') and offer.promoted:
            ranked_choices.append(offs)
          else:
            if c == candidate.college1:
              ranked_choices[0] = offs
            elif c == candidate.college2:
              ranked_choices[1] = offs
            elif c == candidate.college3:
              ranked_choices[2] = offs
            elif c == candidate.college4:
              ranked_choices[3] = offs
            elif c == candidate.college5:
              ranked_choices[4] = offs
            elif c == candidate.college6:
              ranked_choices[5] = offs
            else:
              ranked_choices.append(offs)
        return ''.join(ranked_choices).strip()
      else:
        # physphil ranking
        ranked_physphil = [ '', '', '', '', '', '' ]
        ranked_phys = [ '', '', '', '', '', '' ]
        for offer in candidate.offer.order_by('time'):
          c = offer.college
          offs = offer_string(offer)
          if c == candidate.college1:
            if offer.course_type == Candidate.COURSE_PHYSPHIL_ONLY:
              ranked_physphil[0] = offs
            else:
              ranked_phys[0] = offs
          elif c == candidate.college2:
            if offer.course_type == Candidate.COURSE_PHYSPHIL_ONLY:
              ranked_physphil[1] = offs
            else:
              ranked_phys[1] = offs
          elif c == candidate.college3:
            if offer.course_type == Candidate.COURSE_PHYSPHIL_ONLY:
              ranked_physphil[2] = offs
            else:
              ranked_phys[2] = offs
          elif c == candidate.college4:
            if offer.course_type == Candidate.COURSE_PHYSPHIL_ONLY:
              ranked_physphil[3] = offs
            else:
              ranked_phys[3] = offs
          elif c == candidate.college5:
            if offer.course_type == Candidate.COURSE_PHYSPHIL_ONLY:
              ranked_physphil[4] = offs
            else:
              ranked_phys[4] = offs
          elif c == candidate.college6:
            if offer.course_type == Candidate.COURSE_PHYSPHIL_ONLY:
              ranked_physphil[5] = offs
            else:
              ranked_phys[5] = offs
          else:
            if offer.course_type == Candidate.COURSE_PHYSPHIL_ONLY:
              ranked_physphil.append(offs)
            else:
              ranked_phys.append(offs)
        # now handle the special cases
        #logger.info("physphil offers:  {}".format(''.join(ranked_physphil)))
        #logger.info("    phys offers:  {}".format(''.join(ranked_phys)))
        ss = []
        ss.append(ranked_physphil[0])
        if candidate.interview5 > 0:
          # second college philosophy interview
          ss.append(ranked_physphil[1])
          ss.append(ranked_phys[0])
        else:
          ss.append(ranked_phys[0])
          ss.append(ranked_physphil[1])
        ss.append(ranked_phys[1])
        ss.append(''.join(ranked_physphil[2:]))
        ss.append(''.join(ranked_phys[2:]))
        return ''.join(ss).strip()

#---------------------------------------------------------------
# amend student state from array
#---------------------------------------------------------------

def amend_student_state(candidate, data, user, selected_college):
    # note we need to bolster checks:
    # * that user has permission to change these states
    # * that the values are valid (such as the state string)
    # (this method can't change comments - use normal django form for that)
    logger.info("amend with user " + user.last_name)
    clist = get_college_codes_for_user(user)
    logger.info("amend with clist {}".format(clist))
    #logger.info("Amend col1={}, col2={}, clist={}".format(ap.college1.adss_code,ap.college2.adss_code,clist))
    #logger.info("amend with selected college " + selected_college)
    incol1 = "ALL" in clist or (candidate.college1 and candidate.college1.adss_code in clist)
    incol2 = "ALL" in clist or (candidate.college2 and candidate.college2.adss_code in clist)
    overallstate = OverallState.objects.current()
    longlist = overallstate in [ OverallState.DEVELOPMENT, OverallState.LONGLIST ]
    shortlist = overallstate in [ OverallState.DEVELOPMENT, OverallState.SHORTLIST ]
    ranking = overallstate in [ OverallState.DEVELOPMENT,
                                OverallState.OFFERS ]
    msg = []
    save_info = False
    for e in data['f']:
        ef = e['n']
        ev = e['v']
        logger.info("amend field " + ef + " to value " + ev)
        okay = False # indicates whether amendemnt was authorized
        if ef in [ 'sel', 'i1', 'i2', 'i3', 'i4', 'i5', 'crs' ]:
            ev = ev.upper()
            field = ef
            if field == 'sel' and incol1:
                okay = True
                field = 'state'
                if ev == 'R' and longlist: # rescue
                    candidate.rescued = True
                    continue # no state change - let extract() calculate displayed state flag
                elif ev == 'T' and longlist: # unrescue
                    candidate.rescued = False
                    continue
                elif ev == 'S' and longlist: # save
                    candidate.reserved = True
                    continue
                elif ev == 'U' and longlist: # unsaved
                    candidate.reserved = False
                    continue
                elif ev == 'W': # withdraw
                    ev = Candidate.STATE_WITHDRAWN
                elif ev == 'A': # unwithdraw - change to implied value for overall state
                    if shortlist or ranking:
                        ev = Candidate.STATE_SUMMONED
                    else:
                        ev = Candidate.STATE_APPLIED
                elif ev == 'P': # if physphil, change Q to P
                    if candidate.course_type == Candidate.COURSE_PHYSPHIL_WITH_FALLBACK:
                        candidate.course_type = Candidate.COURSE_PHYSPHIL_ONLY
                        save_info = True
                        #logger.info("Found Q->P");
                        continue
                elif ev == 'Q': # if physphil, change P to Q
                    if candidate.course_type == Candidate.COURSE_PHYSPHIL_ONLY:
                        candidate.course_type = Candidate.COURSE_PHYSPHIL_WITH_FALLBACK
                        save_info = True
                        #logger.info("Found P->Q");
                        continue
            elif field == 'i1' and incol1 and shortlist:
                okay = True
                field = 'interview1'
            elif field == 'i2' and incol1 and shortlist:
                okay = True
                field = 'interview2'
            elif field == 'i3' and incol2 and shortlist:
                okay = True
                field = 'interview3'
            elif field == 'i4' and incol1 and shortlist:
                okay = True
                field = 'interview4'
            elif field == 'i5' and incol2 and shortlist:
                okay = True
                field = 'interview5'
            elif field == 'crs' and ranking:
                okay = True
                # TODO:  letters designate transitions
                # q - physics offer
                # p - PhysPhil offer
                # 0 - revoke
                # this actually creates an OfferRank object
                # TODO: but we also need to add this to instantaneous state information
                #   to read crs-# in savestate, to read it back in fillstate.
                #   visibility:  in ranking, anonymous offers; in offers, need to list college with it
                oc = get_colleges_for_user(user)
                #info = candidate.info
                if len(oc) == 1:
                    sc = oc[0]
                elif len(oc) > 1:
                    if selected_college == "" or selected_college == None:
                        logger.error("User has multiple college affiliation but no selected college")
                        msg.append("User has multiple college affiliation but no selected college")
                        continue
                    else:
                        sc = College.objects.get(adss_code=selected_college)
                if ev == 'Q': # physics
                    logger.info("Physics-only offer")
                    if candidate.course_type == Candidate.COURSE_THREEYEAR:
                        ct = Candidate.COURSE_THREEYEAR
                    else:
                        ct = Candidate.COURSE_FOURYEAR
                    flag = False
                elif ev == 'P':
                    logger.info("PhysPhil offer")
                    # don't give P offer to physics-only candidate!
                    ct = candidate.course_type
                    if ct == Candidate.COURSE_PHYSPHIL_WITH_FALLBACK:
                        ct = Candidate.COURSE_PHYSPHIL_ONLY
                    flag = False
                elif ev == 'F':
                    ct = candidate.course_type
                    flag = True
                elif ev == '0':
                    # revoke offer
                    logger.info("Revoke offer")
                    Offer.objects.filter(candidate=candidate).filter(college=sc).all().delete()
                    continue
                else:
                    logger.error("Invalid course offer " + ev)
                    msg.append("Invalid course offer " + ev)
                    continue
                # revoke any previous offers
                #logger.info("Revoke any previous offers")
                Offer.objects.filter(candidate=candidate).filter(college=sc).delete()
                #logger.info("New offer")
                offer = Offer(college=sc,
                              candidate=candidate,
                              deferred_entry=candidate.info.deferred_entry,
                              course_type=ct,
                              )
                if hasattr(offer,'promoted'):
                  offer.promoted = flag
                offer.save()
                #logger.info("Offer saved")
                continue
            if okay:
                setattr(candidate,field,ev)
            else:
                logger.error("Unauthorized amendment of field " + field + " by " + user.get_full_name())
                msg.append("Unauthorized amendment of field " + field + " by " + user.get_full_name())
        elif ef == 'comment':
            # create StudentComment hee
            sc = Comment(candidate=candidate, commenter=user, text=ev)
            #logger.info("Comment logged on " + candidate.ucas_id + " by " + user.get_full_name())
            sc.save()
    candidate.save()
    if save_info:
        candidate.info.save()
    return '; '.join(msg) if len(msg) > 0 else None

#---------------------------------------------------------------
# get or post student states
#---------------------------------------------------------------

@login_required
def api_student_states(request, college_code=None):
    # whether POST or GET, response is to update the state information
    since = request.REQUEST.get('t')
    #logger.info("api_student_states:  year {}, id {}, since {}".format(year, student_id, since))
    res = []
    msg = [] # messages to return to user
    if request.method == "POST":
        selected_college = ""
        data = json.loads(request.body)
        for d in data:
            if d['pk'] == 0:
                selected_college = d['scol']
                #logger.info("selected college found " + selected_college)
            else:
                try:
                    s = Candidate.objects.get(pk=d['pk'])
                    logger.info("call amend on pk = {}".format(d['pk']))
                    es = amend_student_state(s, d, request.user, selected_college)
                    if es:
                        msg.append(es)
                except ObjectDoesNotExist:
                    logger.error("Illegal Student pk = " + d['pk'])

    #logger.info("Now handle get response")
    # now handle GET or POST response
    kw = {}
    if year:
        kw['info__interview_year'] = year
    if since:
        base = datetime.datetime.utcfromtimestamp(int(since))
        kw['modification_timestamp__gt'] = base
    if OverallState.objects.current() in [ OverallState.LONGLIST, OverallState.SHORTLIST ]:
        kw['state'] = Candidate.STATE_SUMMONED

    if college_code:
        c1 = Candidate.objects.filter(college1__adss_code=college_code.upper(), **kw).select_related('comments').select_related('offer')
        c2 = Candidate.objects.filter(college2__adss_code=college_code.upper(), **kw).select_related('comments').select_related('offer')
        candidates = c1 | c2
    else:
        if len(kw) == 0:
            candidates = Candidate.objects.select_related('comments').select_related('offer')
        else:
            candidates = Candidate.objects.filter(**kw).select_related('comments').select_related('offer')

    #logger.info("Extract state on {} candidates".format(candidates.count()))
    for s in candidates:
        res.append(extract_student_state(s, request.user))
    if len(msg) > 0:
        res.append({ "pk":0, "msg": msg })

    #logger.info("Send back response")
    response = HttpResponse(json.dumps(res), content_type='application/json')
    return response

