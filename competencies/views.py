from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.forms.models import modelform_factory, modelformset_factory, inlineformset_factory
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db.models.loading import get_model
from django.contrib.auth import logout
from django.contrib.auth.views import password_change
from django.contrib.auth.decorators import login_required

from copy import copy
from collections import OrderedDict

from competencies.models import *


def index(request):
    return render_to_response('competencies/index.html',
                              {},
                              context_instance = RequestContext(request))

# Authentication views
def logout_view(request):
    logout(request)
    # Redirect to home page for now. Later, maybe stay on same page.
    return redirect('/')

def profile(request):
    return render_to_response('registration/profile.html',
                              {},
                              context_instance = RequestContext(request))

def password_change_form(request):
    if request.method == 'POST':
        return password_change(request, post_change_redirect='/password_change_successful')
    else:
        return render_to_response('registration/password_change_form.html',
                                  {},
                                  context_instance = RequestContext(request))

def password_change_successful(request):
    return render_to_response('registration/password_change_successful.html',
                              {},
                              context_instance = RequestContext(request))

# --- Authorization views ---
def no_edit_permission(request, school_id):
    """Displays message that user does not have permission to make requested edits."""
    school = get_school(school_id)
    return render_to_response('competencies/no_edit_permission.html',
                              {'school': school},
                              context_instance = RequestContext(request))

# --- Simple views, for exploring system without changing it: ---
def schools(request):
    schools = School.objects.all()
    return render_to_response('competencies/schools.html', {'schools': schools}, context_instance=RequestContext(request))

def school(request, school_id):
    """Displays subject areas and subdiscipline areas for a given school."""
    school = get_school(school_id)
    kwargs = get_visibility_filter(request.user, school)
    # all subject areas for a school
    sas = get_subjectareas(school, kwargs)
    # all subdiscipline areas for each subject area
    sa_sdas = get_sa_sdas(sas, kwargs)
    return render_to_response('competencies/school.html',
                              {'school': school, 'subject_areas': sas,
                               'sa_sdas': sa_sdas},
                              context_instance = RequestContext(request))

def subject_area(request, subject_area_id):
    """Shows a subject area's subdiscipline areas, and competency areas."""
    subject_area = SubjectArea.objects.get(id=subject_area_id)
    school = subject_area.school
    kwargs = get_visibility_filter(request.user, school)
    # Get subdiscipline areas for this subject area:
    sa_subdiscipline_areas = subject_area.subdisciplinearea_set.filter(**kwargs)
    # Get competencies for the general subject area (no associated sda):
    sa_general_competency_areas = subject_area.competencyarea_set.filter(subdiscipline_area=None).filter(**kwargs)
    # Get competencies for each subdiscipline area:
    sda_competency_areas = {sda: sda.competencyarea_set.filter(**kwargs) for sda in sa_subdiscipline_areas}
    return render_to_response('competencies/subject_area.html',
                              {'subject_area': subject_area, 'school': school,
                               'sa_subdiscipline_areas': sa_subdiscipline_areas,
                               'sa_general_competency_areas': sa_general_competency_areas,
                               'sda_competency_areas': sda_competency_areas},
                              context_instance = RequestContext(request))

def sa_summary(request, sa_id):
    """Shows a GSP-style summary for a subject area."""
    sa = SubjectArea.objects.get(id=sa_id)
    school = sa.school
    kwargs = get_visibility_filter(request.user, school)

    # Get competencies for the general subject area (no associated sda):
    sa_general_competency_areas = sa.competencyarea_set.filter(subdiscipline_area=None).filter(**kwargs)
    
    # Get eus for each competency area.
    ca_eus = {}
    for ca in sa_general_competency_areas:
        ca_eus[ca] = ca.essentialunderstanding_set.filter(**kwargs)
        
    # Get sdas, sda cas, sda eus
    sdas = sa.subdisciplinearea_set.filter(**kwargs)
    sda_cas = {}
    for sda in sdas:
        sda_cas[sda] = sda.competencyarea_set.filter(**kwargs)
    sda_ca_eus = {}
    for sda in sdas:
        for ca in sda_cas[sda]:
            sda_ca_eus[ca] = ca.essentialunderstanding_set.filter(**kwargs)

    return render_to_response('competencies/sa_summary.html',
                              {'subject_area': sa, 'school': school,
                               'sa_general_competency_areas': sa_general_competency_areas,
                               'ca_eus': ca_eus,
                               'sda_cas': sda_cas, 'sda_ca_eus': sda_ca_eus},
                              context_instance = RequestContext(request))
    
@login_required
def edit_sa_summary(request, sa_id):
    """Edit a GSP-style summary for a subject area."""
    # This should work for a given sa_id, or with no sa_id.
    # Have an id, edit a subject area.
    # No id, create a new subject area.
    # Needs sda elements as well.

    subject_area = SubjectArea.objects.get(id=sa_id)
    school = subject_area.school
    kwargs = get_visibility_filter(request.user, school)

    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school, subject_area):
        redirect_url = '/no_edit_permission/' + str(school.id)
        return redirect(redirect_url)

    # Get competency areas, and build ca prefixes.
    sa_general_competency_areas = subject_area.competencyarea_set.filter(subdiscipline_area=None).filter(**kwargs)
    # Order is predictable working from the list, not from what was returned.
    ca_form_prefixes = ['ca_form_%d' % ca.id for ca in sa_general_competency_areas]

    # Get sdas.
    sdas = subject_area.subdisciplinearea_set.filter(**kwargs)

    # Respond to submitted data.
    if request.method == 'POST':
        sa_form = SubjectAreaForm(request.POST, instance=subject_area)
        if sa_form.is_valid():
            sa = sa_form.save(commit=False)
            sa.school = school
            sa.save()

        for ca_form_prefix, ca in zip(ca_form_prefixes, sa_general_competency_areas):
            ca_form = CompetencyAreaForm(request.POST, prefix=ca_form_prefix, instance=ca)
            if ca_form.is_valid():
                instance = ca_form.save(commit=False)
                ca.subject_area = subject_area
                ca.save()

            # Deal with this ca's eus here?
            eus = ca.essentialunderstanding_set.filter(**kwargs)
            for eu in eus:
                eu_form_prefix = 'eu_form_%d' % eu.id
                eu_form = EssentialUnderstandingForm(request.POST,
                                                         prefix=eu_form_prefix, instance=eu)
                if eu_form.is_valid():
                    instance = eu_form.save(commit=False)
                    eu.competency_area = ca
                    eu.save()

    # Get elements, and build forms.
    sa_form = SubjectAreaForm(instance=subject_area)

    sda_forms = []
    for sda in sdas:
        sda_form_prefix = 'sda_form_%d' % sda.id
        sda_form = SubdisciplineAreaForm(prefix=sda_form_prefix, instance=sda)
        sda_forms.append(sda_form)

    ca_eu_forms = {}
    # Get eus for each competency area.
    for ca in sa_general_competency_areas:
        ca_form_prefix = 'ca_form_%d' % ca.id
        ca_form = CompetencyAreaForm(prefix=ca_form_prefix, instance=ca)

        eus = ca.essentialunderstanding_set.filter(**kwargs)
        eu_forms = []
        for eu in eus:
            eu_form_prefix = 'eu_form_%d' % eu.id
            eu_form = EssentialUnderstandingForm(prefix=eu_form_prefix, instance=eu)
            eu_forms.append(eu_form)
        ca_eu_forms[ca_form] = eu_forms

    return render_to_response('competencies/edit_sa_summary.html',
                              {'subject_area': subject_area, 'school': school,
                               'sa_form': sa_form, 'sda_forms': sda_forms,
                               'ca_eu_forms': ca_eu_forms,
                               },
                              context_instance = RequestContext(request))

def subdiscipline_area(request, subdiscipline_area_id):
    """Shows all of the competency areas for a given subdiscipline area."""
    subdiscipline_area = SubdisciplineArea.objects.get(id=subdiscipline_area_id)
    subject_area = subdiscipline_area.subject_area
    school = subject_area.school
    kwargs = get_visibility_filter(request.user, school)
    competency_areas = subdiscipline_area.competencyarea_set.filter(**kwargs)
    ca_levels = {}
    for ca in competency_areas:
        ca_levels[ca] = get_levels(request, ca)
    return render_to_response('competencies/subdiscipline_area.html',
                              {'subdiscipline_area': subdiscipline_area, 'subject_area': subject_area,
                               'school': school, 'competency_areas': competency_areas,
                               'ca_levels': ca_levels},
                              context_instance = RequestContext(request))

def competency_area(request, competency_area_id):
    """Shows all of the essential understandings and learning targets for a given competency area."""
    competency_area = CompetencyArea.objects.get(id=competency_area_id)
    subject_area = competency_area.subject_area
    school = subject_area.school
    kwargs = get_visibility_filter(request.user, school)
    essential_understandings = competency_area.essentialunderstanding_set.filter(**kwargs)
    ca_levels = get_levels(request, competency_area)
    return render_to_response('competencies/competency_area.html',
                              {'school': school, 'subject_area': subject_area, 'competency_area': competency_area,
                               'essential_understandings': essential_understandings,
                               'ca_levels': ca_levels},
                              context_instance = RequestContext(request))

def essential_understanding(request, essential_understanding_id):
    """Shows all learning targets for a given essential understanding."""
    essential_understanding = EssentialUnderstanding.objects.get(id=essential_understanding_id)
    competency_area = essential_understanding.competency_area
    ca_levels = get_levels(request, competency_area)
    subject_area = competency_area.subject_area
    school = subject_area.school
    kwargs = get_visibility_filter(request.user, school)
    learning_targets = essential_understanding.learningtarget_set.filter(**kwargs)
    return render_to_response('competencies/essential_understanding.html',
                              {'school': school, 'subject_area': subject_area, 'competency_area': competency_area,
                               'essential_understanding': essential_understanding, 'learning_targets': learning_targets,
                               'ca_levels': ca_levels},
                              context_instance = RequestContext(request))

def entire_system(request, school_id):
    """Shows the entire system for a given school."""
    school = get_school(school_id)
    kwargs = get_visibility_filter(request.user, school)
    # Get all subject areas for a school
    sas = get_subjectareas(school, kwargs)
    # Get all subdiscipline areas for each subject area
    sa_sdas = get_sa_sdas(sas, kwargs)
    # Get all general competency areas for a subject
    sa_cas = get_sa_cas(sas, kwargs)
    # Get all competency areas for each subdiscipline area
    sda_cas = get_sda_cas(sas, sa_sdas, kwargs)
    # Get all essential understandings for each competency area
    # Get all level descriptions for each competency area
    ca_eus, ca_levels = get_ca_eus_ca_levels(request, sda_cas, sa_cas, kwargs)
    # Get all learning targets for each essential understanding
    eu_lts = get_eu_lts(ca_eus, kwargs)

    return render_to_response('competencies/entire_system.html', 
                              {'school': school, 'subject_areas': sas,
                               'sa_sdas': sa_sdas, 'sa_cas': sa_cas,
                               'sda_cas': sda_cas, 'ca_eus': ca_eus,
                               'ca_levels': ca_levels, 'eu_lts': eu_lts},
                              context_instance = RequestContext(request))

# helper methods to get elements of the system.

def get_school(school_id):
    """Returns school for given id."""
    return School.objects.get(id=school_id)

def get_subjectareas(school, kwargs):
    """Returns subject areas for a given school."""
    return school.subjectarea_set.filter(**kwargs)

def get_sa_sdas(subject_areas, kwargs):
    """ Returns all subdiscipline areas for each subject area.
    Uses OrderedDict to preserve order of subject areas.
    """
    sa_sdas = OrderedDict()
    for sa in subject_areas:
        sa_sdas[sa] = sa.subdisciplinearea_set.filter(**kwargs)
    return sa_sdas

def get_sa_cas(subject_areas, kwargs):
    """Returns all general competency areas for each subject.
    Need to preserve the order of subject areas, so use OrderedDict.
    """
    sa_cas = OrderedDict()
    for sa in subject_areas:
        sa_cas[sa] = sa.competencyarea_set.filter(subdiscipline_area=None).filter(**kwargs)
    return sa_cas

def get_sda_cas(subject_areas, sa_sdas, kwargs):
    """Returns all competency areas for each subdiscipline area."""
    sda_cas = {}
    for sa in subject_areas:
        for sda in sa_sdas[sa]:
            sda_cas[sda] = sda.competencyarea_set.filter(**kwargs)
    return sda_cas

def get_ca_eus_ca_levels(request, sda_cas, sa_cas, kwargs):
    """Returns all essential understandings for each competency area.
    Loops through all sa_cas, sda_cas.
    Also grabs level descriptions for each competency area.
    """
    ca_eus = {}
    ca_levels = {}
    for cas in sda_cas.values():
        for ca in cas:
            ca_eus[ca] = ca.essentialunderstanding_set.filter(**kwargs)
            ca_levels[ca] = get_levels(request, ca)
    for cas in sa_cas.values():
        for ca in cas:
            ca_eus[ca] = ca.essentialunderstanding_set.filter(**kwargs)
            ca_levels[ca] = get_levels(request, ca)
    return (ca_eus, ca_levels)

def get_levels(request, competency_area):
    """Returns levels for a given competency area, respecting visibility privileges."""
    levels = []
    for level_pk in competency_area.get_level_order():
        level = Level.objects.get(pk=level_pk)
        if request.user.is_authenticated() or level.public:
            levels.append(level)
    return levels

def get_eu_lts(ca_eus, kwargs):
    """Returns all learning targets for each essential understanding."""
    eu_lts = {}
    for eus in ca_eus.values():
        for eu in eus:
            eu_lts[eu] = eu.learningtarget_set.filter(**kwargs)
    return eu_lts

def get_visibility_filter(user, school):
    # Get filter for visibility, based on logged-in status.
    if user.is_authenticated() and school in user.userprofile.schools.all():
        kwargs = {}
    elif user.is_authenticated() and school in get_user_sa_schools(user):
        kwargs = {}
    else:
        kwargs = {'{0}'.format('public'): True}
    return kwargs

def get_user_sa_schools(user):
    """Return a list of schools associated with the subject areas this user can edit.
    Needed because if a user can edit one subject area, that user needs to be able
    to see all elements of that school's system. Can only edit some sa's, but can see everything.
    """
    # This is ugly implementation; should probably be in models.py
    schools = [sa.school for sa in user.userprofile.subject_areas.all()]
    return schools

# --- Edit views, for editing parts of the system ---
def has_edit_permission(user, school, subject_area=None):
    """Checks whether given user has permission to edit given object.
    """
    # Returns True if allowed to edit, False if not allowed to edit
    # If school is in userprofile, user can edit anything
    if school in user.userprofile.schools.all():
        return True
    # User can not edit entire school system; check if user has permission to edit this subject area.
    # Will throw error if user has no subject_areas defined? (public, guest)
    #  Default sa is None, and None not in empty list, but this makes sure a subject_area
    #   was actually passed in.
    if subject_area and (subject_area in user.userprofile.subject_areas.all()):
        return True
    else:
        return False


@login_required
def edit_school(request, school_id):
    """Allows user to edit a school's subject areas.
    """
    school = School.objects.get(id=school_id)
    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school):
        redirect_url = '/no_edit_permission/' + str(school.id)
        return redirect(redirect_url)

    # fields arg not working, but exclude works???
    SubjectAreaFormSet = modelformset_factory(SubjectArea, form=SubjectAreaForm)

    if request.method == 'POST':
        sa_formset = SubjectAreaFormSet(request.POST)
        if sa_formset.is_valid():
            instances = sa_formset.save(commit=False)
            for instance in instances:
                instance.school = school
                instance.save()
    # Create formset for unbound and bound forms
    #  This allows continuing to add more items after saving.
    sa_formset = SubjectAreaFormSet(queryset=SubjectArea.objects.all().filter(school_id=school_id))

    return render_to_response('competencies/edit_school.html', 
                              {'school': school,
                               'sa_formset': sa_formset
                               },
                              context_instance = RequestContext(request))

@login_required
def edit_subject_area(request, subject_area_id):
    """Allows user to edit a subject_area's subdiscipline areas.
    """
    subject_area = SubjectArea.objects.get(id=subject_area_id)
    school = subject_area.school
    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school, subject_area):
        redirect_url = '/no_edit_permission/' + str(school.id)
        return redirect(redirect_url)

    # fields arg not working, but exclude works???
    SubdisciplineAreaFormSet = modelformset_factory(SubdisciplineArea, form=SubdisciplineAreaForm)

    if request.method == 'POST':
        sda_formset = SubdisciplineAreaFormSet(request.POST)
        if sda_formset.is_valid():
            instances = sda_formset.save(commit=False)
            for instance in instances:
                instance.subject_area = subject_area
                instance.save()
    # Create formset for unbound and bound forms
    #  This allows continuing to add more items after saving.
    sda_formset = SubdisciplineAreaFormSet(queryset=SubdisciplineArea.objects.all().filter(subject_area_id=subject_area_id))

    return render_to_response('competencies/edit_subject_area.html',
                              {'school': school, 'subject_area': subject_area, 'sda_formset': sda_formset},
                              context_instance = RequestContext(request))

@login_required
def edit_sa_competency_areas(request, subject_area_id):
    """Allows user to edit the competencies for a general subject area."""
    subject_area = SubjectArea.objects.get(id=subject_area_id)
    school = subject_area.school
    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school, subject_area):
        redirect_url = '/no_edit_permission/' + str(school.id)
        return redirect(redirect_url)

    sa_comps = subject_area.competencyarea_set.all()

    # Build the sa_comp_area formset by using queryset to exclude all
    #  competency areas with a defined sda. Need general ca_formset to do this.
    CompetencyAreaFormSet = modelformset_factory(CompetencyArea, form=CompetencyAreaForm)

    if request.method == 'POST':
        # Process general sa competency areas:
        sa_ca_formset = CompetencyAreaFormSet(request.POST)
        if sa_ca_formset.is_valid():
            instances = sa_ca_formset.save(commit=False)
            for instance in instances:
                instance.subject_area = subject_area
                instance.save()

    # Create formsets for unbound and bound forms, to allow editing after saving.
    sa_ca_formset = CompetencyAreaFormSet(queryset=CompetencyArea.objects.all().filter(subject_area=subject_area).filter(subdiscipline_area=None))

    return render_to_response('competencies/edit_sa_competency_areas.html',
                              {'school': school, 'subject_area': subject_area, 'sa_ca_formset': sa_ca_formset},
                              context_instance = RequestContext(request))

@login_required
def edit_sda_competency_areas(request, subdiscipline_area_id):
    """Allows user to edit the competencies for a specific subdiscipline area."""
    subdiscipline_area = SubdisciplineArea.objects.get(id=subdiscipline_area_id)
    subject_area = subdiscipline_area.subject_area
    school = subject_area.school
    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school, subject_area):
        redirect_url = '/no_edit_permission/' + str(school.id)
        return redirect(redirect_url)

    sda_comps = subdiscipline_area.competencyarea_set.all()

    # Build the sda_comp_area formset by using queryset 
    CompetencyAreaFormSet = modelformset_factory(CompetencyArea, form=CompetencyAreaForm)

    if request.method == 'POST':
        # Process sda competency areas:
        sda_ca_formset = CompetencyAreaFormSet(request.POST)
        if sda_ca_formset.is_valid():
            instances = sda_ca_formset.save(commit=False)
            for instance in instances:
                instance.subject_area = subject_area
                instance.subdiscipline_area = subdiscipline_area
                instance.save()

    # Create formsets for unbound and bound forms, to allow editing after saving.
    sda_ca_formset = CompetencyAreaFormSet(queryset=CompetencyArea.objects.all().filter(subdiscipline_area=subdiscipline_area))

    return render_to_response('competencies/edit_sda_competency_areas.html',
                              {'school': school, 'subject_area': subject_area,
                               'subdiscipline_area': subdiscipline_area, 'sda_ca_formset': sda_ca_formset},
                              context_instance = RequestContext(request))

@login_required
def edit_competency_area(request, competency_area_id):
    """Allows user to edit the essential understandings for a given competency area."""
    ca = CompetencyArea.objects.get(id=competency_area_id)
    sa = ca.subject_area
    sda = ca.subdiscipline_area
    school = sa.school
    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school, sa):
        redirect_url = '/no_edit_permission/' + str(school.id)
        return redirect(redirect_url)

    EssentialUnderstandingFormSet = modelformset_factory(EssentialUnderstanding, form=EssentialUnderstandingForm)

    if request.method == 'POST':
        eu_formset = EssentialUnderstandingFormSet(request.POST)
        if eu_formset.is_valid():
            instances = eu_formset.save(commit=False)
            for instance in instances:
                instance.competency_area = ca
                instance.save()

    eu_formset = EssentialUnderstandingFormSet(queryset=ca.essentialunderstanding_set.all())

    return render_to_response('competencies/edit_competency_area.html',
                              {'school': school, 'subject_area': sa,
                               'subdiscipline_area': sda, 'competency_area': ca,
                               'eu_formset': eu_formset},
                              context_instance = RequestContext(request))

@login_required
def edit_levels(request, competency_area_id):
    """Allows user to edit levels for a given competency area."""
    ca = CompetencyArea.objects.get(id=competency_area_id)
    ca_levels = [Level.objects.get(pk=level_pk) for level_pk in ca.get_level_order()]
    sa = ca.subject_area
    sda = ca.subdiscipline_area
    school = sa.school
    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school, sa):
        redirect_url = '/no_edit_permission/' + str(school.id)
        return redirect(redirect_url)

    LevelFormSet = modelformset_factory(Level, form=LevelForm)
    #LevelFormSet = modelformset_factory(Level)

    if request.method == 'POST':
        level_formset = LevelFormSet(request.POST)
        if level_formset.is_valid():
            instances = level_formset.save(commit=False)
            for instance in instances:
                instance.competency_area = ca
                instance.save()
                # Ensure that ordering is correct
                #  (apprentice - technician - master - professional
                correct_order = []
                for type in [Level.APPRENTICE, Level.TECHNICIAN,
                             Level.MASTER, Level.PROFESSIONAL]:
                    try:
                        correct_order.append(Level.objects.get(competency_area=ca, level_type=type).pk)
                    except:
                        pass
                if ca.get_level_order() != correct_order:
                    ca.set_level_order(correct_order)

    level_formset = LevelFormSet(queryset=ca.level_set.all())

    return render_to_response('competencies/edit_levels.html',
                              {'school': school, 'subject_area': sa,
                               'subdiscipline_area': sda, 'competency_area': ca,
                               'level_formset': level_formset},
                              context_instance = RequestContext(request))


@login_required
def edit_essential_understanding(request, essential_understanding_id):
    """Allows user to edit the learning targets associated with an essential understanding."""
    eu = EssentialUnderstanding.objects.get(id=essential_understanding_id)
    ca = eu.competency_area
    sa = ca.subject_area
    sda = ca.subdiscipline_area
    school = sa.school
    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school, sa):
        redirect_url = '/no_edit_permission/' + str(school.id)
        return redirect(redirect_url)

    LearningTargetFormSet = modelformset_factory(LearningTarget, form=LearningTargetForm, extra=3)

    if request.method == 'POST':
        lt_formset = LearningTargetFormSet(request.POST)
        if lt_formset.is_valid():
            instances = lt_formset.save(commit=False)
            for instance in instances:
                instance.essential_understanding = eu
                instance.save()

    lt_formset = LearningTargetFormSet(queryset=eu.learningtarget_set.all())

    return render_to_response('competencies/edit_essential_understanding.html',
                              {'school': school, 'subject_area': sa,
                               'subdiscipline_area': sda, 'competency_area': ca,
                               'essential_understanding': eu, 'lt_formset': lt_formset},
                              context_instance = RequestContext(request))

@login_required
def edit_order(request, school_id):
    """Shows the entire system for a given school,
    with links to change the order of any child element.
    """
    school = School.objects.get(id=school_id)
    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school):
        if school not in get_user_sa_schools(request.user):
            redirect_url = '/no_edit_permission/' + str(school.id)
            return redirect(redirect_url)

    # all subject areas for a school
    sas = school.subjectarea_set.all()
    # all subdiscipline areas for each subject area
    #  using OrderedDict to preserve order of subject areas
    sa_sdas = OrderedDict()
    for sa in sas:
        sa_sdas[sa] = sa.subdisciplinearea_set.all()
    # all general competency areas for a subject
    #  need to preserve order for these as well
    sa_cas = OrderedDict()
    for sa in sas:
        sa_cas[sa] = sa.competencyarea_set.all().filter(subdiscipline_area=None)
    # all competency areas for each subdiscipline area
    sda_cas = {}
    for sa in sas:
        for sda in sa_sdas[sa]:
            sda_cas[sda] = sda.competencyarea_set.all()
    # all essential understandings for each competency area
    #  loop through all sa_cas, sda_cas
    # also grab level descriptions for each competency area
    ca_eus = {}
    ca_levels = {}
    for cas in sda_cas.values():
        for ca in cas:
            ca_eus[ca] = ca.essentialunderstanding_set.all()
            ca_levels[ca] = [Level.objects.get(pk=level_pk) for level_pk in ca.get_level_order()]
    for cas in sa_cas.values():
        for ca in cas:
            ca_eus[ca] = ca.essentialunderstanding_set.all()
            ca_levels[ca] = [Level.objects.get(pk=level_pk) for level_pk in ca.get_level_order()]
    # all learning targets for each essential understanding
    eu_lts = {}
    for eus in ca_eus.values():
        for eu in eus:
            eu_lts[eu] = eu.learningtarget_set.all()

    return render_to_response('competencies/edit_order.html', 
                              {'school': school, 'subject_areas': sas,
                               'sa_sdas': sa_sdas, 'sa_cas': sa_cas,
                               'sda_cas': sda_cas, 'ca_eus': ca_eus,
                               'ca_levels': ca_levels, 'eu_lts': eu_lts},
                              context_instance = RequestContext(request))

@login_required
def change_order(request, school_id, parent_type, parent_id, child_type, child_id, direction):
    """Changes the order of the child element passed in, and redirects to edit_order.
    Requires parent_type to be a ModelName, and child_type to be a modelname.
    """
    # Get subject_area, to help determine if user has permission to edit
    # Will need parent_object anyways.
    school = School.objects.get(id=school_id)
    parent_object = get_model('competencies', parent_type).objects.get(id=parent_id)
    sa = get_subjectarea_from_object(parent_object)
    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school, sa):
        redirect_url = '/no_edit_permission/' + str(school.id)
        return redirect(redirect_url)

    # Get order of children
    get_order_method = 'get_' + child_type + '_order'
    order = getattr(parent_object, get_order_method)()

    # Set new order.
    child_index = order.index(int(child_id))
    set_order_method = 'set_' + child_type + '_order'
    if direction == 'up' and child_index != 0:
        if child_type == 'competencyarea':
            # Need to move before previous ca in given sda, or in general sa
            #  Get pks of all cas in this sda
            #  Get order, find prev element
            ca = CompetencyArea.objects.get(id=child_id)
            sda = ca.subdiscipline_area
            if sda:
                # pks for cas in this sda only
                ca_sda_pks = [ca.pk for ca in sda.competencyarea_set.all()]
            else:
                # sda None, this is a ca for a general sa
                # pks for cas in this general sa
                sa = ca.subject_area
                ca_sda_pks = [ca.pk for ca in sa.competencyarea_set.filter(subdiscipline_area=None)]
            current_ca_index = ca_sda_pks.index(int(child_id))
            if current_ca_index != 0:
                # move ca up in the subset
                # find pk of ca to switch with, then find index of that ca in order
                #  then switch the two indices
                target_ca_pk = ca_sda_pks[current_ca_index-1]
                target_ca_order_index = order.index(target_ca_pk)
                current_ca_order_index = order.index(int(child_id))
                order[current_ca_order_index], order[target_ca_order_index] = order[target_ca_order_index], order[current_ca_order_index]
                getattr(parent_object, set_order_method)(order)
        else:
            # Swap child id with element before it
            order[child_index], order[child_index-1] = order[child_index-1], order[child_index]
            getattr(parent_object, set_order_method)(order)
    if direction == 'down' and child_index != (len(order)-1):
        if child_type == 'competencyarea':
            # Need to move after next ca in given sda, or in general sa
            #  Get pks of all cas in this sda
            #  Get order, find next element
            ca = CompetencyArea.objects.get(id=child_id)
            sda = ca.subdiscipline_area
            if sda:
                # pks for cas in this sda only
                ca_sda_pks = [ca.pk for ca in sda.competencyarea_set.all()]
            else:
                # sda None, this is a ca for a general sa
                # pks for cas in this general sa
                sa = ca.subject_area
                ca_sda_pks = [ca.pk for ca in sa.competencyarea_set.filter(subdiscipline_area=None)]
            current_ca_index = ca_sda_pks.index(int(child_id))
            if current_ca_index != (len(ca_sda_pks)-1):
                # move ca down in the subset
                # find pk of ca to switch with, then find index of that ca in order
                #  then switch the two indices
                target_ca_pk = ca_sda_pks[current_ca_index+1]
                target_ca_order_index = order.index(target_ca_pk)
                current_ca_order_index = order.index(int(child_id))
                order[current_ca_order_index], order[target_ca_order_index] = order[target_ca_order_index], order[current_ca_order_index]
                getattr(parent_object, set_order_method)(order)
        else:
            # Swap child id with element after it
            order[child_index], order[child_index+1] = order[child_index+1], order[child_index]
            getattr(parent_object, set_order_method)(order)

    redirect_url = '/edit_order/' + school_id
    return redirect(redirect_url)

def get_subjectarea_from_object(object_in):
    """Returns the subject_area of the given object, and none if the
    given object is above the level of a subject_area.
    """
    class_name = object_in.__class__.__name__
    if class_name == 'School':
        return None
    elif class_name == 'SubjectArea':
        return object_in
    elif class_name in ['SubdisciplineArea', 'CompetencyArea']:
        return object_in.subject_area
    elif class_name == 'EssentialUnderstanding':
        return object_in.competency_area.subject_area
    elif class_name == 'LearningTarget':
        return object_in.essential_understanding.competency_area.subject_area

@login_required
def edit_visibility(request, school_id):
    """Allows user to set the visibility of any item in the school's system."""
    school = School.objects.get(id=school_id)
    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school):
        if school not in get_user_sa_schools(request.user):
            redirect_url = '/no_edit_permission/' + str(school.id)
            return redirect(redirect_url)

    # all subject areas for a school
    sas = school.subjectarea_set.all()
    # all subdiscipline areas for each subject area
    #  using OrderedDict to preserve order of subject areas
    sa_sdas = OrderedDict()
    for sa in sas:
        sa_sdas[sa] = sa.subdisciplinearea_set.all()
    # all general competency areas for a subject
    #  need to preserve order for these as well
    sa_cas = OrderedDict()
    for sa in sas:
        sa_cas[sa] = sa.competencyarea_set.all().filter(subdiscipline_area=None)
    # all competency areas for each subdiscipline area
    sda_cas = {}
    for sa in sas:
        for sda in sa_sdas[sa]:
            sda_cas[sda] = sda.competencyarea_set.all()
    # all essential understandings for each competency area
    #  loop through all sa_cas, sda_cas
    # also grab level descriptions for each competency area
    ca_eus = {}
    ca_levels = {}
    for cas in sda_cas.values():
        for ca in cas:
            ca_eus[ca] = ca.essentialunderstanding_set.all()
            ca_levels[ca] = [Level.objects.get(pk=level_pk) for level_pk in ca.get_level_order()]
    for cas in sa_cas.values():
        for ca in cas:
            ca_eus[ca] = ca.essentialunderstanding_set.all()
            ca_levels[ca] = [Level.objects.get(pk=level_pk) for level_pk in ca.get_level_order()]
    # all learning targets for each essential understanding
    eu_lts = {}
    for eus in ca_eus.values():
        for eu in eus:
            if request.user.is_authenticated():
                eu_lts[eu] = eu.learningtarget_set.all()
            else:
                eu_lts[eu] = eu.learningtarget_set.filter(public=True)

    return render_to_response('competencies/edit_visibility.html', 
                              {'school': school, 'subject_areas': sas,
                               'sa_sdas': sa_sdas, 'sa_cas': sa_cas,
                               'sda_cas': sda_cas, 'ca_eus': ca_eus,
                               'ca_levels': ca_levels, 'eu_lts': eu_lts},
                              context_instance = RequestContext(request))

@login_required    
def change_visibility(request, school_id, object_type, object_pk, visibility_mode):
    # Get object, and toggle attribute 'public'
    current_object = get_model('competencies', object_type).objects.get(pk=object_pk)
    # Hack to deal with bug around ordering
    #  Saving an object after toggling 'public' attribute can affect _order
    #  Probably need a custom migration that stops db from setting _order=0 on every save
    old_order = get_parent_order(current_object)
    if visibility_mode == 'public':
        # Need to check that parent is public
        if current_object.is_parent_public():
            current_object.public = True
            current_object.save()
            check_parent_order(current_object, old_order)
    elif visibility_mode == 'cascade_public':
        if current_object.is_parent_public():
            current_object.public = True
            current_object.save()
            check_parent_order(current_object, old_order)
            set_related_visibility(current_object, 'public')
    else:  # visibility mode == 'private'
        # Setting an object private implies all the elements under it should be private.
        current_object.public = False
        current_object.save()
        check_parent_order(current_object, old_order)
        set_related_visibility(current_object, 'private')

    redirect_url = '/edit_visibility/' + school_id
    return redirect(redirect_url)

def set_related_visibility(object_in, visibility_mode):
    """Finds all related objects, and sets them all to the appropriate visibility mode."""
    links = [rel.get_accessor_name() for rel in object_in._meta.get_all_related_objects()]
    for link in links:
        objects = getattr(object_in, link).all()
        for object in objects:
            try:
                # Hack to deal with ordering issue
                old_order = get_parent_order(object)
                if visibility_mode == 'public':
                    object.public = True
                    object.save()
                else:
                    object.public = False
                    object.save()
                check_parent_order(object, old_order)
            except:
                # Must not be a public/ private object
                pass
            # Check if this object has related objects, if so use recursion
            if object._meta.get_all_related_objects():
                set_related_visibility(object, visibility_mode)

# Methods to deal with ordering issue around order_with_respect_to
def check_parent_order(child_object, correct_order):
    """Hack to address ordering issue around order_with_respect_to."""
    if get_parent_order(child_object) != correct_order:
        set_parent_order(child_object, correct_order)

def get_parent_order(child_object):
    parent_object = child_object.get_parent()
    order_method = 'get_' + child_object.__class__.__name__.lower() + '_order'
    parent_order = getattr(parent_object, order_method)()
    return parent_order

def set_parent_order(child_object, order):
    parent_object = child_object.get_parent()
    order_method = 'set_' + child_object.__class__.__name__.lower() + '_order'
    getattr(parent_object, order_method)(order)

@login_required
def new_school(request):
    """Creates a new school."""
    # Will need validation.
    new_school_name = request.POST['new_school_name']
    new_school_created = False
    new_school = None
    if new_school_name:
        # Create new school
        new_school = School(name=new_school_name)
        new_school.save()
        new_school_created = True
        # Now need to associate current user with this school
        associate_user_school(request.user, new_school)

    return render_to_response('competencies/new_school.html',
                              {'new_school_name': new_school_name, 'new_school_created': new_school_created,
                               'new_school': new_school }, context_instance=RequestContext(request))

def associate_user_school(user, school):
    # Associates a given school with a given user
    try:
        user.userprofile.schools.add(school)
    except: # User probably does not have a profile yet
        up = UserProfile()
        up.user = user
        up.save()
        up.schools.add(school)
