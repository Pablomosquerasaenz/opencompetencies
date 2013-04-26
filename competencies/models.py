from django.db import models
from django.forms import ModelForm, Textarea

# --- Competency System Hierarchy ---

class School(models.Model):
    name = models.CharField(max_length=500)

    def __unicode__(self):
        return self.name

class SubjectArea(models.Model):
    subject_area = models.CharField(max_length=500)
    school = models.ForeignKey(School)

    def __unicode__(self):
        return self.subject_area

class SubdisciplineArea(models.Model):
    subdiscipline_area = models.CharField(max_length=500)
    subject_area = models.ForeignKey(SubjectArea)

    def __unicode__(self):
        return self.subdiscipline_area

class CompetencyArea(models.Model):
    competency_area = models.CharField(max_length=500)
    subject_area = models.ForeignKey(SubjectArea)
    subdiscipline_area = models.ForeignKey(SubdisciplineArea, blank=True, null=True)

    def __unicode__(self):
        return self.competency_area

class EssentialUnderstanding(models.Model):
    essential_understanding = models.CharField(max_length=2000)
    competency_area = models.ForeignKey(CompetencyArea)

    def __unicode__(self):
        return self.essential_understanding

class LearningTarget(models.Model):
    learning_target = models.CharField(max_length=2000)
    essential_understanding = models.ForeignKey(EssentialUnderstanding)

    def __unicode__(self):
        return self.learning_target


# --- Pathways ---
from django.db.models import Q
class Pathway(models.Model):
    name = models.CharField(max_length=500)
    school = models.ForeignKey(School)
    subject_areas = models.ManyToManyField(SubjectArea)
    subdiscipline_areas = models.ManyToManyField(SubdisciplineArea)

    def __unicode__(self):
        return self.name


# --- ModelForms ---
class EssentialUnderstandingForm(ModelForm):
    class Meta:
        model = EssentialUnderstanding
        fields = ('essential_understanding',)
        # Bootstrap controls width of Textarea, ignoring the 'cols' setting. Can also use 'class': 'input-block-level'
        widgets = {'essential_understanding': Textarea(attrs={'rows': 3, 'class': 'span8'}) }

class LearningTargetForm(ModelForm):
    class Meta:
        model = LearningTarget
        fields = ('learning_target', )
        # Bootstrap controls width of Textarea, ignoring the 'cols' setting. Can also use 'class': 'input-block-level'
        widgets = {'learning_target': Textarea(attrs={'rows': 3, 'class': 'span8'}) }

class PathwayForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(PathwayForm, self).__init__(*args, **kwargs)
        pathway = self.instance

        # sas
        self.fields['subject_areas'].queryset = pathway.school.subjectarea_set.all()

        # sdas
        sda_queryset = None
        
        for sa in pathway.subject_areas.all():
            if sda_queryset:
                sda_queryset = sda_queryset | sa.subdisciplinearea_set.all()
            else:
                sda_queryset = sa.subdisciplinearea_set.all()
        self.fields['subdiscipline_areas'].queryset = sda_queryset

    class Meta:
        model = Pathway
