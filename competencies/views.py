from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.forms.models import modelform_factory, modelformset_factory, inlineformset_factory
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.loading import get_model
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.views import password_change
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from copy import copy
from collections import OrderedDict

from competencies.models import *
from competencies import my_admin

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

def register(request):
    """Register a new user."""
    if request.method == 'POST':
        # Process completed form.
        form = RegisterUserForm(data=request.POST)
        
        if form.is_valid():
            user = form.save()
            my_admin.add_userprofile(user)
            
            # Log the user in, and then redirect to home page.
            user = authenticate(username=user,
                password=request.POST['password1'])
            login(request, user)
            return HttpResponseRedirect(reverse('competencies:index'))
    else:
        # Display blank registration form.        
        form = RegisterUserForm()
        
    context = {'form': form}
    return render_to_response('competencies/register.html',
                              context,
                              context_instance=RequestContext(request))


# --- Authorization views ---
def no_edit_permission(request, school_id):
    """Displays message that user does not have permission to make requested edits."""
    school = get_organization(school_id)
    return render_to_response('competencies/no_edit_permission.html',
                              {'school': school},
                              context_instance = RequestContext(request))

# --- Simple views, for exploring system without changing it: ---
def organizations(request):
    organizations = Organization.objects.all()
    return render_to_response('competencies/organizations.html', {'organizations': organizations}, context_instance=RequestContext(request))

def organization(request, organization_id):
    """Displays subject areas and subdiscipline areas for a given organization."""
    organization = get_organization(organization_id)
    kwargs = get_visibility_filter(request.user, organization)
    # all subject areas for an organization
    sas = get_subjectareas(organization, kwargs)
    # all subdiscipline areas for each subject area
    sa_sdas = get_sa_sdas(sas, kwargs)
    return render_to_response('competencies/organization.html',
                              {'organization': organization, 'subject_areas': sas,
                               'sa_sdas': sa_sdas},
                              context_instance = RequestContext(request))

def sa_summary(request, sa_id):
    """Shows a simple summary for a subject area."""
    sa = SubjectArea.objects.get(id=sa_id)
    organization = sa.organization
    kwargs = get_visibility_filter(request.user, organization)

    sdas, cas, eus = get_sda_ca_eu_elements(sa, kwargs)
    
    return render_to_response('competencies/sa_summary.html',
                              {'subject_area': sa, 'organization': organization,
                               'sdas': sdas, 'cas': cas, 'eus': eus,},
                              context_instance = RequestContext(request))

@login_required
def edit_sa_summary(request, sa_id):
    """Edit the elements in sa_summary."""
    # This should work for a given sa_id, or with no sa_id.
    # Have an id, edit a subject area.
    # No id, create a new subject area.

    subject_area = SubjectArea.objects.get(id=sa_id)
    organization = subject_area.organization
    kwargs = get_visibility_filter(request.user, organization)

    # Test if user allowed to edit this organization.
    if not has_edit_permission(request.user, organization, subject_area):
        redirect_url = '/no_edit_permission/' + str(organization.id)
        return redirect(redirect_url)

    sdas, cas, eus = get_sda_ca_eu_elements(subject_area, kwargs)

    # Respond to submitted data.
    if request.method == 'POST':
        process_form(request, subject_area, 'sa')
        for sda in sdas:
            process_form(request, sda, 'sda')
        for ca in cas:
            process_form(request, ca, 'ca')
        for eu in eus:
            process_form(request, eu, 'eu')

    # Build forms.
    sa_form = generate_form(subject_area, 'sa')
    sda_forms = []
    for sda in sdas:
        sda_form = generate_form(sda, 'sda')
        sda_form.my_id = sda.id
        sda_forms.append(sda_form)
    zipped_sda_forms = list(zip(sdas, sda_forms))
        
    ca_forms = []
    for ca in cas:
        ca_form = generate_form(ca, 'ca')
        ca_form.my_id = ca.id
        ca_forms.append(ca_form)
    zipped_ca_forms = list(zip(cas, ca_forms))

    eu_forms = []
    for eu in eus:
        eu_form = generate_form(eu, 'eu')
        eu_form.my_id = eu.id
        eu_forms.append(eu_form)
    zipped_eu_forms = list(zip(eus, eu_forms))
    

    return render_to_response('competencies/edit_sa_summary.html',
                              {'subject_area': subject_area, 'organization': organization,
                               'sdas': sdas, 'cas': cas, 'eus': eus,
                               'zipped_sda_forms': zipped_sda_forms,
                               'zipped_ca_forms': zipped_ca_forms,
                               'zipped_eu_forms': zipped_eu_forms,
                               },
                              context_instance = RequestContext(request))

def get_sda_ca_eu_elements(subject_area, kwargs):
    """Get all sdas, cas, and eus associated with a subject area."""
    sdas = subject_area.subdisciplinearea_set.filter(**kwargs)
    cas = subject_area.competencyarea_set.filter(**kwargs)
    eus = []
    for ca in cas:
        for eu in ca.essentialunderstanding_set.filter(**kwargs):
            eus.append(eu)
    return (sdas, cas, eus)

def process_form(request, instance, element_type):
    """Process a form for a single element."""
    prefix = '%s_form_%d' % (element_type, instance.id)

    if element_type == 'sa':
        form = SubjectAreaForm(request.POST, instance=instance)
    elif element_type == 'sda':
        form = SubdisciplineAreaForm(request.POST, prefix=prefix, instance=instance)
    elif element_type == 'ca':
        form = CompetencyAreaForm(request.POST, prefix=prefix, instance=instance)
    elif element_type == 'eu':
        form = EssentialUnderstandingForm(request.POST, prefix=prefix, instance=instance)

    if form.is_valid():
        form.save()

def generate_form(instance, element_type):
    """Generate a form for a single element."""
    prefix = '%s_form_%d' % (element_type, instance.id)

    if element_type == 'sa':
        return SubjectAreaForm(instance=instance)
    elif element_type == 'sda':
        return SubdisciplineAreaForm(prefix=prefix, instance=instance)
    elif element_type == 'ca':
        return CompetencyAreaForm(prefix=prefix, instance=instance)
    elif element_type == 'eu':
        return EssentialUnderstandingForm(prefix=prefix, instance=instance)

def new_sa(request, school_id):
    """Create a new subject area for a given school."""
    school = Organization.objects.get(id=school_id)
    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school):
        redirect_url = '/no_edit_permission/' + str(school.id)
        return redirect(redirect_url)

    if request.method == 'POST':
        sa_form = SubjectAreaForm(request.POST)
        if sa_form.is_valid():
            new_sa = sa_form.save(commit=False)
            new_sa.organization = school
            new_sa.save()
            return redirect('/edit_sa_summary/%d' % new_sa.id)

    sa_form = SubjectAreaForm()

    return render_to_response('competencies/new_sa.html',
                              {'school': school, 'sa_form': sa_form,},
                              context_instance = RequestContext(request))

def new_sda(request, sa_id):
    """Create a new subdiscipline area for a given subject area."""
    sa = SubjectArea.objects.get(id=sa_id)
    school = sa.organization
    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school):
        redirect_url = '/no_edit_permission/' + str(school.id)
        return redirect(redirect_url)

    if request.method == 'POST':
        sda_form = SubdisciplineAreaForm(request.POST)
        if sda_form.is_valid():
            new_sda = sda_form.save(commit=False)
            new_sda.subject_area = sa
            new_sda.save()
            return redirect('/edit_sa_summary/%d' % sa.id)

    sda_form = SubdisciplineAreaForm()

    return render_to_response('competencies/new_sda.html',
                              {'school': school, 'sa': sa,
                               'sda_form': sda_form,},
                              context_instance = RequestContext(request))

def new_ca(request, sa_id):
    """Create a new competency area for a given general subject area."""
    sa = SubjectArea.objects.get(id=sa_id)
    school = sa.organization
    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school):
        redirect_url = '/no_edit_permission/' + str(school.id)
        return redirect(redirect_url)

    if request.method == 'POST':
        ca_form = CompetencyAreaForm(request.POST)
        if ca_form.is_valid():
            new_ca = ca_form.save(commit=False)
            new_ca.subject_area = sa
            new_ca.save()
            return redirect('/edit_sa_summary/%d' % sa.id)

    ca_form = CompetencyAreaForm()

    return render_to_response('competencies/new_ca.html',
                              {'school': school, 'sa': sa, 'ca_form': ca_form,},
                              context_instance = RequestContext(request))

def new_sda_ca(request, sda_id):
    """Create a new competency area for a given subdiscipline area."""
    sda = SubdisciplineArea.objects.get(id=sda_id)
    sa = sda.subject_area
    school = sa.organization
    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school):
        redirect_url = '/no_edit_permission/' + str(school.id)
        return redirect(redirect_url)

    if request.method == 'POST':
        ca_form = CompetencyAreaForm(request.POST)
        if ca_form.is_valid():
            new_ca = ca_form.save(commit=False)
            new_ca.subject_area = sa
            new_ca.subdiscipline_area = sda
            new_ca.save()
            return redirect('/edit_sa_summary/%d' % sa.id)

    ca_form = CompetencyAreaForm()

    return render_to_response('competencies/new_sda_ca.html',
                              {'school': school, 'sa': sa, 'sda': sda,
                               'ca_form': ca_form,},
                              context_instance = RequestContext(request))

def new_eu(request, ca_id):
    """Create a new essential understanding for given ca."""
    ca = CompetencyArea.objects.get(id=ca_id)
    sa = ca.subject_area
    school = sa.organization
    # Test if user allowed to edit this school.
    if not has_edit_permission(request.user, school):
        redirect_url = '/no_edit_permission/' + str(school.id)
        return redirect(redirect_url)

    if request.method == 'POST':
        eu_form = EssentialUnderstandingForm(request.POST)
        if eu_form.is_valid():
            new_eu = eu_form.save(commit=False)
            new_eu.competency_area = ca
            new_eu.save()
            return redirect('/edit_sa_summary/%d' % sa.id)

    eu_form = EssentialUnderstandingForm()

    return render_to_response('competencies/new_eu.html',
                              {'school': school, 'sa': sa, 'ca': ca,
                               'eu_form': eu_form,},
                              context_instance = RequestContext(request))
    

# helper methods to get elements of the system.

def get_organization(school_id):
    """Returns school for given id."""
    return Organization.objects.get(id=school_id)

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

def get_eu_lts(ca_eus, kwargs):
    """Returns all learning targets for each essential understanding."""
    eu_lts = {}
    for eus in ca_eus.values():
        for eu in eus:
            eu_lts[eu] = eu.learningobjective_set.filter(**kwargs)
    return eu_lts

def get_visibility_filter(user, school):
    # Get filter for visibility, based on logged-in status.
    if user.is_authenticated() and school in user.userprofile.organizations.all():
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
    schools = [sa.organization for sa in user.userprofile.subject_areas.all()]
    return schools

# --- Edit views, for editing parts of the system ---
def has_edit_permission(user, school, subject_area=None):
    """Checks whether given user has permission to edit given object.
    """
    # Returns True if allowed to edit, False if not allowed to edit
    # If school is in userprofile, user can edit anything
    if school in user.userprofile.organizations.all():
        return True
    # User can not edit entire school system; check if user has permission to edit this subject area.
    # Will throw error if user has no subject_areas defined? (public, guest)
    #  Default sa is None, and None not in empty list, but this makes sure a subject_area
    #   was actually passed in.
    if subject_area and (subject_area in user.userprofile.subject_areas.all()):
        return True
    else:
        return False

def get_subjectarea_from_object(object_in):
    """Returns the subject_area of the given object, and none if the
    given object is above the level of a subject_area.
    """
    class_name = object_in.__class__.__name__
    if class_name == 'Organization':
        return None
    elif class_name == 'SubjectArea':
        return object_in
    elif class_name in ['SubdisciplineArea', 'CompetencyArea']:
        return object_in.subject_area
    elif class_name == 'EssentialUnderstanding':
        return object_in.competency_area.subject_area
    elif class_name == 'LearningObjective':
        return object_in.essential_understanding.competency_area.subject_area

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
def new_organization(request):
    """Creates a new organization."""

    if request.method == 'POST':
        new_organization_form = OrganizationForm(request.POST)
        if new_organization_form.is_valid():
            new_organization = new_organization_form.save(commit=False)
            new_organization.owner = request.user
            new_organization.save()
            associate_user_organization(request.user, new_organization)
            return redirect(reverse('competencies:organizations'))

    new_organization_form = OrganizationForm()

    return render_to_response('competencies/new_organization.html',
                              {'new_organization_form': new_organization_form,},
                              context_instance = RequestContext(request))

def associate_user_organization(user, organization):
    # Associates a given organization with a given user
    try:
        user.userprofile.organizations.add(organization)
    except ObjectDoesNotExist: # User probably does not have a profile yet
        up = UserProfile()
        up.user = user
        up.save()
        up.organizations.add(organization)
