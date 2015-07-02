from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from competencies.models import *
from competencies.views import school

"""DEV NOTES
  - Maybe instead of using indices to store schools, use separate lists:
    - test_schools_has_perm
    - test_schools_no_perm
    - test_schools_all_private
    - test_schools_all_public

"""

class CompetencyViewTests(TestCase):
    """Needed tests:
    - queryset tests for all pages
    - no-data tests
    """

    def setUp(self):
        # Build a school, down to the performance indicator level.
        #  These should be a few loops, making a number of elements at each level.

        self.client = Client()

        # Create 2 test users.
        self.test_user_0 = User.objects.create_user(username='testuser0', password='pw')
        new_up = UserProfile(user=self.test_user_0)
        new_up.save()

        self.test_user_1 = User.objects.create_user(username='testuser1', password='pw')
        new_up = UserProfile(user=self.test_user_1)
        new_up.save()

        # Build 3 test schools that user 0 is associated with,
        #  3 the user 1 is associated with.
        self.test_schools, self.test_sas = [], []
        for school_num in range(6):
            name = "Test School %d" % school_num
            if school_num < 3:
                new_school = School.objects.create(name=name, owner=self.test_user_0)
                self.test_user_0.userprofile.schools.add(new_school)
            else:
                new_school = School.objects.create(name=name, owner=self.test_user_1)
                self.test_user_1.userprofile.schools.add(new_school)
            self.test_schools.append(new_school)

            # Create 3 subject areas for each school.
            for sa_num in range(3):
                sa_name = "Test SA %d-%d" % (school_num, sa_num)
                new_sa = SubjectArea.objects.create(subject_area=sa_name,
                                                    school=new_school)
                self.test_sas.append(new_sa)

                # Create 3 grad standards for each subject area.
                for gs_num in range(3):
                    gs_body = "Test GS %d-%d-%d" % (school_num, sa_num, gs_num)
                    new_gs = GraduationStandard.objects.create(subject_area=new_sa,
                                                               graduation_standard=gs_body)

                # Create 3 sdas for each sa.
                for sda_num in range(3):
                    sda_name = "Test SDA %d-%d-%d" % (school_num, sa_num, sda_num)
                    new_sda = SubdisciplineArea.objects.create(subject_area=new_sa,
                                                               subdiscipline_area=sda_name)


    def test_index_view(self):
        """Index page is a static page for now, so just check status."""
        response = self.client.get(reverse('competencies:index'))
        self.assertEqual(response.status_code, 200)

    def test_schools_view(self):
        """Schools page lists all schools, links to detail view of that school."""
        response = self.client.get(reverse('competencies:schools'))
        self.assertEqual(response.status_code, 200)

        # Make sure list of schools appears in context, and that test_school
        #  is in that list.
        self.assertTrue('schools' in response.context)
        for school in self.test_schools:
            self.assertTrue(school in response.context['schools'])


    def test_school_view_logged_in(self):
        """School page lists subject areas and subdiscipline areas for that school."""
        self.client.login(username='testuser0', password='pw')

        for school_num, school in enumerate(self.test_schools):
            test_url = reverse('competencies:school', args=(school.id,))
            response = self.client.get(test_url)
            self.assertEqual(response.status_code, 200)

            # For now, all users can see the names of all schools.
            self.assertEqual(school, response.context['school'])

            if school_num < 3:
                # User should see sa and sdas for school they have permissions on.
                for sa in school.subjectarea_set.all():
                    self.assertTrue(sa in response.context['subject_areas'])
                    for sda in sa.subdisciplinearea_set.all():
                        self.assertTrue(sda in response.context['sa_sdas'][sa])
            else:
                # All elements are private by default, so user should not see sas
                #  or sdas for this school.
                for sa in school.subjectarea_set.all():
                    self.assertFalse(sa in response.context['subject_areas'])
                    self.assertFalse(sa in response.context['sa_sdas'].keys())

    def test_new_school(self):
        """New school allows uer to create a new school."""
        test_url = reverse('competencies:new_school')
        self.generic_test_blank_form(test_url)

        # Test user can create a new school, current user is owner,
        #  and user can modify school.
        response = self.client.post(test_url, {'name': 'my new school'})
        self.assertEqual(response.status_code, 302)
        school_names = [school.name for school in School.objects.all()]
        self.assertTrue('my new school' in school_names)

        for school in School.objects.all():
            if school.name == 'my new school':
                self.assertTrue(school.owner, self.test_user_0)
                self.assertTrue(school in self.test_user_0.userprofile.schools.all())

        # Test that user can't create a second school of the same name.
        # DEV: DB error causes test to fail. How test this properly?
        #  Start by creating server error page.
        # response = self.client.post(test_url, {'name': 'my new school'})
        # self.assertEqual(response.status_code, 500)

        # But another user can create a school of that same name.
        self.client.login(username='testuser1', password='pw')
        response = self.client.post(test_url, {'name': 'my new school'})
        self.assertEqual(response.status_code, 302)
        school_names = [school.name for school in School.objects.all()]
        # DEV: Verify name 'my new school' appears twice in list.
        self.assertTrue('my new school' in school_names)

        owner_correct = False
        for school in School.objects.all():
            if school.name == 'my new school' and school.owner == self.test_user_1:
                owner_correct = True
        self.assertTrue(owner_correct)



    def test_new_sa_view(self):
        """Lets user create a new subject area."""
        test_url = reverse('competencies:new_sa', args=(self.test_schools[0].id,))
        self.generic_test_blank_form(test_url)
        
        # Test user can create a new subject area, and it's stored in db.
        response = self.client.post(test_url, {'subject_area': 'english', 'description': ''})
        self.assertEqual(response.status_code, 302)
        sa_names = [sa.subject_area for sa in self.test_schools[0].subjectarea_set.all()]
        self.assertTrue('english' in sa_names)
        
    def test_new_sda_view(self):
        """Lets user create a new subdiscipline area."""
        test_url = reverse('competencies:new_sda', args=(self.test_sas[0].id,))
        self.generic_test_blank_form(test_url)

        # Test user can create a new subdiscipline area, and it's stored in db.
        response = self.client.post(test_url, {'subdiscipline_area': 'life science', 'description': ''})
        self.assertEqual(response.status_code, 302)
        sda_names = [sda.subdiscipline_area for sda in self.test_sas[0].subdisciplinearea_set.all()]
        self.assertTrue('life science' in sda_names)

    def test_new_gs_view(self):
        """Lets user create a new graduation standard for a general subject area."""
        test_url = reverse('competencies:new_gs', args=(self.test_sas[0].id,))
        self.generic_test_blank_form(test_url)

        # Test user can create a new gs, and it's stored in db.
        data = {'graduation_standard': 'knows science',
                'student_friendly': '', 'description': '', 'phrase': '',
                }
        response = self.client.post(test_url, data)
        self.assertEqual(response.status_code, 302)
        gs_titles = [gs.graduation_standard for gs in self.test_sas[0].graduationstandard_set.all()]
        self.assertTrue('knows science' in gs_titles)

    def test_new_sda_gs_view(self):
        """Lets user create a new graduation standard for a subdiscipline area."""
        test_sdas = [sda for sda in self.test_sas[0].subdisciplinearea_set.all()]
        test_url = reverse('competencies:new_sda_gs', args=(test_sdas[0].id,))
        self.generic_test_blank_form(test_url)

        # Test user can create a new gs for the sda, and it's stored in db.
        data = {'graduation_standard': 'knows Newtons Laws',
                'student_friendly': '', 'description': '', 'phrase': '',
                }
        response = self.client.post(test_url, data)
        self.assertEqual(response.status_code, 302)
        gs_titles = [gs.graduation_standard for gs in test_sdas[0].graduationstandard_set.all()]
        self.assertTrue('knows Newtons Laws' in gs_titles)

    def test_new_pi_view(self):
        """Lets user create a new performance indicator for a graduation standard."""
        test_gstds = GraduationStandard.objects.all()
        test_url = reverse('competencies:new_pi', args=(test_gstds[0].id,))
        self.generic_test_blank_form(test_url)

        # Test user can create a new pi for the gs, and it's stored in db.
        data = {'performance_indicator': 'can state first law',
                'student_friendly': '', 'description': '',
                }
        response = self.client.post(test_url, data)
        self.assertEqual(response.status_code, 302)
        pi_bodies = [pi.performance_indicator for pi in test_gstds[0].performanceindicator_set.all()]
        self.assertTrue('can state first law' in pi_bodies)

    def generic_test_blank_form(self, test_url):
        """A helper method to test that a form-based page returns a blank form properly."""
        # Test that a logged in user can get a blank form properly.
        self.client.login(username='testuser0', password='pw')
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)

class FormTests(TestCase):
    """Test the custom forms in OC."""

    def test_registeruserform(self):
        """Test that the registration form works."""
        form = RegisterUserForm()
        # finish!


class ModelTests(TestCase):
    """Test aspects of models."""

    def test_userprofile(self):
        """Test that a userprofile connects properly to a user."""
        new_user = User()
        new_user.username = 'new_user'
        new_user.password = 'new_user_pw'
        new_user.save()

        new_up = UserProfile()
        new_up.user = new_user
        new_up.save()

        self.assertEqual(new_user.userprofile, new_up)
