from django.db import models
from django.forms import ModelForm, TextInput, Textarea, SelectMultiple, CheckboxSelectMultiple
from django.forms import EmailField
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

# --- Competency System Hierarchy ---

# Description of common attributes:
#  public: whether a non-logged in user can see this element
#  description: a public-facing narrative description of this element
#  student-friendly: Many parts of a standards system are written in 'teacher language',
#    which is not very accessible to students. This is a rephrasing of the element in
#    language that is easier for students to understand.

class School(models.Model):
    name = models.CharField(max_length=500)

    def __str__(self):
        return self.name

class SubjectArea(models.Model):
    subject_area = models.CharField(max_length=500)
    school = models.ForeignKey(School)
    public = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.subject_area

    class Meta:
        order_with_respect_to = 'school'

    def is_parent_public(self):
        return True

    def get_parent(self):
        return self.school

class SubdisciplineArea(models.Model):
    subdiscipline_area = models.CharField(max_length=500)
    subject_area = models.ForeignKey(SubjectArea)
    public = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.subdiscipline_area

    class Meta:
        order_with_respect_to = 'subject_area'

    def is_parent_public(self):
        return self.subject_area.public

    def get_parent(self):
        return self.subject_area

class GraduationStandard(models.Model):
    graduation_standard = models.CharField(max_length=500)
    subject_area = models.ForeignKey(SubjectArea)
    subdiscipline_area = models.ForeignKey(SubdisciplineArea, blank=True, null=True)
    public = models.BooleanField(default=False)
    student_friendly = models.TextField(blank=True)
    description = models.TextField(blank=True)
    alias = models.CharField(max_length=500, default="Graduation Standard")
    phrase = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.graduation_standard

    class Meta:
        order_with_respect_to = 'subject_area'

    def is_parent_public(self):
        # If no sda, then only use subject_area
        if self.subdiscipline_area:
            sda_public = self.subdiscipline_area.public
        else:
            sda_public = True

        if self.subject_area.public and sda_public:
            return True
        else:
            return False

    def get_parent(self):
        return self.subject_area

class Level(models.Model):
    APPRENTICE = 'Apprentice'
    TECHNICIAN = 'Technician'
    MASTER = 'Master'
    PROFESSIONAL = 'Professional'
    LEVEL_TYPE_CHOICES = ( (APPRENTICE, 'Apprentice'), (TECHNICIAN, 'Technician'),
                           (MASTER, 'Master'), (PROFESSIONAL, 'Professional') )
    level_type = models.CharField(max_length=500, choices=LEVEL_TYPE_CHOICES)
    level_description = models.CharField(max_length=5000)
    graduation_standard = models.ForeignKey(GraduationStandard)
    public = models.BooleanField(default=False)

    def __str__(self):
        return self.level_description

    class Meta:
        unique_together = ('graduation_standard', 'level_type',)
        order_with_respect_to = 'graduation_standard'

    def is_parent_public(self):
        return self.graduation_standard.public

    def get_parent(self):
        return self.graduation_standard

class PerformanceIndicator(models.Model):
    performance_indicator = models.CharField(max_length=2000)
    graduation_standard = models.ForeignKey(GraduationStandard)
    public = models.BooleanField(default=False)
    student_friendly = models.TextField(blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.performance_indicator

    class Meta:
        order_with_respect_to = 'graduation_standard'

    def is_parent_public(self):
        return self.graduation_standard.public

    def get_parent(self):
        return self.graduation_standard

class LearningObjective(models.Model):
    learning_objective = models.CharField(max_length=2000)
    performance_indicator = models.ForeignKey(PerformanceIndicator)
    public = models.BooleanField(default=False)
    student_friendly = models.TextField(blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.learning_objective

    class Meta:
        order_with_respect_to = 'performance_indicator'

    def is_parent_public(self):
        return self.performance_indicator.public

    def get_parent(self):
        return self.performance_indicator


# --- User Information ---

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    # User is allowed to edit any aspect of any school in this list.
    schools = models.ManyToManyField(School, blank=True)
    # User is allowed to edit any descendent of any subject_area in this list.
    subject_areas = models.ManyToManyField(SubjectArea, blank=True)

# --- ModelForms ---
class SubjectAreaForm(ModelForm):
    class Meta:
        model = SubjectArea
        fields = ('subject_area', 'description')
        widgets = {
            'subject_area': TextInput(attrs={'class': 'span4'}),
            'description': Textarea(attrs={'rows': 5, 'class': 'span8'}),
            }




class SubdisciplineAreaForm(ModelForm):
    # Hacky way to get id of instance from a form in a template (edit_sa_summary).
    my_id = None
    class Meta:
        model = SubdisciplineArea
        fields = ('subdiscipline_area', 'description')
        widgets = {
            'subdiscipline_area': TextInput(attrs={'class': 'span4'}),
            'description': Textarea(attrs={'rows': 5, 'class': 'span8'}),
            }

class GraduationStandardForm(ModelForm):
    # Hacky way to get id of instance from a form in a template (edit_sa_summary).
    my_id = None
    class Meta:
        model = GraduationStandard
        fields = ('graduation_standard', 'student_friendly', 'description', 'phrase')
        labels = {'graduation_standard': 'Graduation Standard'}
        # Bootstrap controls width of Textarea, ignoring the 'cols' setting. Can also use 'class': 'input-block-level'
        widgets = {'graduation_standard': Textarea(attrs={'rows': 5, 'class': 'span4'}),
                   'student_friendly': Textarea(attrs={'rows': 5, 'class': 'span8'}),
                   'description': Textarea(attrs={'rows': 5, 'class': 'span8'}),
                   }

class PerformanceIndicatorForm(ModelForm):
    class Meta:
        model = PerformanceIndicator
        fields = ('performance_indicator', 'student_friendly', 'description')
        labels = {'performance_indicator': 'Performance Indicator'}
        # Bootstrap controls width of Textarea, ignoring the 'cols' setting. Can also use 'class': 'input-block-level'
        widgets = {'performance_indicator': Textarea(attrs={'rows': 5, 'class': 'span7'}),
                   'student_friendly': Textarea(attrs={'rows': 5, 'class': 'span8'}),
                   'description': Textarea(attrs={'rows': 5, 'class': 'span8'}),
                   }

class LevelForm(ModelForm):
    class Meta:
        model = Level
        fields = ('level_type', 'level_description',)
        # Bootstrap controls width of Textarea, ignoring the 'cols' setting. Can also use 'class': 'input-block-level'
        widgets = {'level_description': Textarea(attrs={'rows': 5, 'class': 'span8'}) }

class LearningObjectiveForm(ModelForm):
    class Meta:
        model = LearningObjective
        fields = ('learning_objective', 'student_friendly', 'description')
        # Bootstrap controls width of Textarea, ignoring the 'cols' setting. Can also use 'class': 'input-block-level'
        widgets = {'learning_objective': Textarea(attrs={'rows': 5, 'class': 'span8'}),
                   'student_friendly': Textarea(attrs={'rows': 5, 'class': 'span8'}),
                   'description': Textarea(attrs={'rows': 5, 'class': 'span8'}),
                   }


class RegisterUserForm(UserCreationForm):
    #email = EmailField(required=False, label='Email (optional)')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        labels = {'email': 'Email (optional)'}

        widgets = {
            'username': TextInput(attrs={'class': 'span5'}),
            'email': TextInput(attrs={'class': 'span5'}),
            }

    def save(self, commit=True):
        user = super(RegisterUserForm, self).save(commit=False)
        if self.cleaned_data["email"]:
            user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
