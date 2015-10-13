from django.db import models
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
import datetime

# Create your models here.

#===========================================================================

def next_matriculation_year():
    today = datetime.date.today()
    return (today.year + (today.month > 8))

def present_interview_year():
    return next_matriculation_year() - 1

#===========================================================================

class Weights(models.Model):
  pat_maths = models.FloatField(default=0)
  pat_physics = models.FloatField(default=0)
  interview1 = models.FloatField(default=0) # for i1 and i2
  interview2 = models.FloatField(default=0) # for i1 and i2

#===========================================================================

class OverallStateManager(models.Manager):
  def current(self):
    """Get current overall state"""
    return self.latest('time').state
  def current_ranking_phase(self):
    return self.latest('time').ranking_phase

class OverallState(models.Model):
  """Database flags to describe overall state of admissions process."""
  DEVELOPMENT = "D"
  PRELIMINARY = "P"
  LONGLIST = "L"
  SHORTLIST = "S"
  OFFERS = "O"
  CLOSED = "C"
  FINAL = "F"
  CODES = (
    (DEVELOPMENT, "Development:  everything's c--p"),
    (PRELIMINARY, "Preliminary:  data unstable"),
    (LONGLIST, "Longlist:  rescue, reserve, reallocate candidates"),
    (SHORTLIST, "Shortlist:  enter marks, which remain invisible"),
    (OFFERS, "Offers:  marks visible, enter offers"),
    (CLOSED, "Closed:  offers made only by superusers"),
    (FINAL, "Final:  data finalized and closed"),
  )
  state = models.CharField(
    max_length=1,
    choices=CODES,
    default=PRELIMINARY)
  ranking_phase = models.IntegerField(
    default=0)

  time = models.DateTimeField(auto_now=True, editable=False)

  objects = OverallStateManager()

  def __str__(self):
    return "Overall state:  {0}({2}) from {1}".format(self.state, self.time, self.ranking_phase)

  def offerable(self, rank):
    """Given the ranking_phase, can one offer on this candidate?"""
    if self.ranking_phase == 1:
      return rank <= 100
    elif self.ranking_phase == 2:
      return rank <= 150
    elif self.ranking_phase == 3:
      return rank <= 150 or (rank >= 200 and rank <= 300)
    elif self.ranking_phase == 4:
      return True
    else:
      return False

#===========================================================================

class CandidateManager(models.Manager):
  def get_by_natural_key(self, uid):
    return self.get(ucas_id=uid)

  def ranking(self):
    """Returns a dict() containing student rankings, indexed by candidate
    primary key"""
    # check cache for results
    cache_key = "ranking"
    ranks = cache.get(cache_key)
    if ranks is None:
      # Generate rankings and cache.  Python and Django are single-
      # threaded so little need to worry about duplicated effort
      #logger.info("Generating ranks")
      students = self.ranked_order()
      ranks = {x[1].pk:x[0] for x in students}
      cache.set(cache_key, ranks, 60) # 60 seconds of caching should be enough
    return ranks

  def ranked_order(self):
    """Property containing all students for the given year, ranked by
    JellScore"""
    all_students = self.order_by('-stored_jell_score').all()
    return [x for x in enumerate(all_students, 1)]

class Candidate(models.Model):
  """Model containing candidate data relevant to the application process.
  This is the main class from which to hang information.
  Primary key reference is generally to this class."""

  ucas_id = models.CharField(
    max_length=10,
    db_index=True,
    unique=True,
    validators=[RegexValidator('^\d{10}$')],
    help_text="Ten-digit applicant ID from UCAS and ADSS")

  STATE_APPLIED = "A"
  STATE_WITHDRAWN = "W"
  STATE_DESUMMONED = "D"
  STATE_SUMMONED = "I"
  STATE_CODES = (
    (STATE_APPLIED, "Applied"),
    (STATE_WITHDRAWN, "Withdrawn"),
    (STATE_DESUMMONED, "Desummoned"),
    (STATE_SUMMONED, "Summoned")
    )
  state = models.CharField(
    max_length=1,
    choices=STATE_CODES, 
    default=STATE_APPLIED
    )

  COURSE_CODE_MPHYS = "F303"
  COURSE_CODE_BAPHYS = "F300"
  COURSE_CODE_PHYSPHIL = "VF53"
  COURSE_CODES = (
    (COURSE_CODE_MPHYS, "MPhys Physics (4 years)"),
    (COURSE_CODE_BAPHYS, "BA Physics (3 years)"),
    (COURSE_CODE_PHYSPHIL, "Physics and Philosophy (4 years)"),
    )
  COURSE_THREEYEAR = '3'
  COURSE_FOURYEAR = '4'
  COURSE_PHYSPHIL_ONLY = 'P'
  COURSE_PHYSPHIL_WITH_FALLBACK = 'Q'
  COURSE_TYPES = (
    (COURSE_FOURYEAR, '4 years (Physics MPhys)'),
    (COURSE_THREEYEAR, '3 years (Physics BA)'),
    (COURSE_PHYSPHIL_ONLY, 'Physics and Philosophy only'),
    (COURSE_PHYSPHIL_WITH_FALLBACK, 'Physics and Philosophy (or Physics)'),
    )
  course_type = models.CharField(
    max_length=1,
    choices=COURSE_TYPES,
    default=COURSE_FOURYEAR,
    help_text="Desired Physics course"
    )

  rescued = models.BooleanField(
    default=False,
    help_text="True if rescued from possible desummoning.")
  reserved = models.BooleanField(
    default=False,
    help_text="True if student can be reallocated.")

  college_selected = models.ForeignKey(
    'College',
    blank=True,
    null=True,
    related_name="college_selected",
    help_text="Specified first-choice college (null or blank if open)"
    )

  college1 = models.ForeignKey('College', null=True, related_name="college1",
    help_text="First interviewing college")
  college2 = models.ForeignKey('College', null=True, related_name="college2",
    help_text="Second interviewing college")
  college3 = models.ForeignKey('College', null=True, related_name="college3",
    help_text="Third college")
  college4 = models.ForeignKey('College', null=True, related_name="college4",
    help_text="Fourth college")
  college5 = models.ForeignKey('College', null=True, related_name="college5",
    help_text="Fifth college")
  college6 = models.ForeignKey('College', null=True, related_name="college6",
    help_text="Sixth college")

  pat_physics = models.DecimalField(
    max_digits=4,
    decimal_places=2,
    default=0,
    validators=[MinValueValidator(0), MaxValueValidator(50)]
    )
  pat_maths = models.DecimalField(
    max_digits=4,
    decimal_places=2,
    default=0,
    validators=[MinValueValidator(0), MaxValueValidator(50)]
    )
  pat_time = models.DateTimeField(null=True, blank=True)

  interview1 = models.DecimalField(
    max_digits=5,
    decimal_places=3,
    default=0,
    validators=[MinValueValidator(0), MaxValueValidator(10)],
    help_text="First college interview score 1")
  interview2 = models.DecimalField(
    max_digits=5,
    decimal_places=3,
    default=0,
    validators=[MinValueValidator(0), MaxValueValidator(10)],
    help_text="First college interview score 2")
  interview3 = models.DecimalField(
    max_digits=5,
    decimal_places=3,
    default=0,
    validators=[MinValueValidator(0), MaxValueValidator(10)],
    help_text="Second college interview score")
  interview4 = models.DecimalField(
    max_digits=5,
    decimal_places=3,
    default=0,
    validators=[MinValueValidator(0), MaxValueValidator(10)],
    help_text="First college philosophy interview score")
  interview5 = models.DecimalField(
    max_digits=5,
    decimal_places=3,
    default=0,
    validators=[MinValueValidator(0), MaxValueValidator(10)],
    help_text="Second college philosophy interview score")

  stored_jell_score = models.DecimalField(
    max_digits=5,
    decimal_places=3,
    default=0)
  stored_rank = models.IntegerField(
    default=0)

  modification_timestamp = models.DateTimeField(auto_now=True,
                                                editable=False)

  def calc_jell_score(self):
    """Property calculating the Jelley score"""
    return WPATP * pat_physics + \
           WPATM * pat_maths + \
           WINT1 * (self.interview1 + self.interview2) + \
           WINT2 * self.interview3

  objects = CandidateManager()

  def __str__(self):
    return "Application: {0}".format(self.info)

  def natural_key(self):
    return self.ucas_id

  class Meta:
    verbose_name = "Candidate"
    verbose_name_plural = "Candidates"

class CandidateInfo(models.Model):
  """Model containing immutable information about a student (or, more correctly,
  candidate)"""
  MALE = 'M'
  FEMALE = 'F'
  TRANSGENDER = 'T'
  UNKNOWN = 'U'
  GENDERS = (
    (MALE, 'Male'),
    (FEMALE, 'Female'),
    (TRANSGENDER, 'Transgender'),
    (UNKNOWN, 'Unspecified/Unknown'),
    )

  candidate = models.OneToOneField("Candidate", primary_key=True, related_name="info")

  surname = models.CharField(max_length=255, db_index=True)
  forenames = models.CharField(max_length=255)
  preferred_name = models.CharField(
    max_length=255,
    blank=True,
    help_text="Preferred first name (if any)"
    )
  title = models.CharField(
    max_length=255,
    blank=True,
    help_text="Title (Mr/Miss/Mrs/Ms/etc.)"
    )
  gender = models.CharField(max_length=2, choices=GENDERS, default=UNKNOWN)
  birth_date = models.DateField(null=True, help_text="Birth date")
  telephone = models.CharField(
    max_length=255,
    blank=True,
    help_text="Home phone number"
    )
  mobile = models.CharField(
    max_length=255,
    blank=True,
    help_text="Mobile phone number"
    )
  current_passport_country = models.CharField(
    max_length=255,
    blank=True,
    help_text=("Country that issued their current passport (blank for "
               "home/EU students)")
    )
  email = models.EmailField(blank=True)

  interview_year = models.IntegerField(
    validators=[MinValueValidator(2000)],
    db_index=True,
    default=present_interview_year,
    help_text=("Admissions and interview cycle that the student applied."  
               "This will be the same as the year in which the student "
               "will matriculate unless the student defers entry.")
    )
  deferred_entry = models.BooleanField(
    default=False,
    help_text=("True if applicant is applying for a year past the normal "
               "matriculation year")
    )

  overseas = models.BooleanField(
    default=False,
    help_text="True if the applicant is from outside the UK and EU."
    )
  declared_in_care = models.NullBooleanField(
    verbose_name="Declared In Care",
    help_text=("True if the applicant has stated on their application form "
               "that they have been in care for > 3 months.")
    )
  offa = models.NullBooleanField(
    verbose_name="OFFA",
    help_text=("True if the applicant is from a statistically "
               "under-represented school (based on admissions vs. results).")
    )
  acorn = models.NullBooleanField(
    verbose_name="ACORN",
    help_text=("True if the applicant's postcode is within ACORN groups "
               "4 or 5.")
    )
  polar = models.NullBooleanField(
    verbose_name="POLAR2",
    help_text=("True if the applicant's home postcode lies within the "
               "bottom 2 quintiles of the POLAR2 dataset.")
    )
  gcse = models.NullBooleanField(
    verbose_name="School GCSE performance",
    help_text=("True if the applicant's school performance at GCSE falls "
               "below the national average.")
    )
  a_level = models.NullBooleanField(
    verbose_name="School A-level performance",
    help_text=("True if the applicant's school performance at A-Level "
               "falls below the national average.")
    )
  access = models.NullBooleanField(
    verbose_name="Access flag",
    help_text="Access flag"
    )
  overall = models.NullBooleanField(
    verbose_name="Overall access flag",
    help_text="Overall access flag"
    )

  gcse_school_id = models.CharField(
    max_length=10,
    blank=True,
    help_text="School code for place where candidate took GCSEs"
    )
  a_level_school_id = models.CharField(
    max_length=10,
    blank=True,
    help_text="School code for place where candidate took A-levels"
    )
  school_pre16_performance = models.FloatField(
    blank=True,
    null=True,
    help_text=("Relative school performance at GCSE (numeric value).")
    )
  school_pre16_gold_performance = models.FloatField(
    blank=True,
    null=True,
    help_text=("Relative school gold performance at GCSE (numeric value).")
    )
  school_post16_performance = models.FloatField(
    blank=True,
    null=True,
    help_text=("Relative school performance at A-Level (numeric value).")
    )
  verified_in_care = models.NullBooleanField(
    verbose_name="In Care",
    help_text=("If true, the applicant has been in care for > 3 months and "
               "this has been verified by the University.")
    )
  disability_code = models.CharField(
    max_length=1,
    blank=True,
    help_text="Disability code"
    )
  disability_notes = models.TextField(
    blank=True,
    help_text="Notes on any special arrangements due to disability."
    )
  has_special_needs = models.BooleanField(
    help_text="True if applicant has special needs",
    default=False
    )

  def overall_widening_access(self):
    # ADSS rules are that the following applicants should be flagged
    if self.declared_in_care:
      return True

    if self.acorn or self.polar:
      # Post code check is valid
      return self.gcse or self.a_level or self.offa
    return False

  def normal_matriculation_year(self):
    """Obtain the year that the student will matriculate, ignoring
     deferred entry"""
    return self.interview_year + 1

  def matriculation_year(self):
    """Obtain the year that the student will matriculate, accounting for
     deferred entry"""
    if self.deferred_entry:
      return self.normal_matriculation_year() + 1
    else:
      return self.normal_matriculation_year()

  def __str__(self):
    return ', '.join([self.surname, self.forenames])

  class Meta:
    ordering = ['-interview_year', 'surname', 'forenames']

class Comment(models.Model):
  """Model representing comments about students/applicants"""

  candidate = models.ForeignKey('Candidate', related_name="comments")
  commenter = models.ForeignKey(
    'auth.User',
    help_text="The user making the comment."
    )
  time = models.DateTimeField(
    auto_now_add=True,
    help_text="Date/time of comment"
    )
  text = models.TextField(help_text="Comment text")

  def __str__(self):
    return "{0} at {1} regarding {2}".format(
      self.commenter,
      self.time,
      self.candidate)

#===========================================================================

class QualificationManager(models.Manager):
  COURSETYPE_ALEVEL = "A-level"
  COURSETYPE_ASLEVEL = "AS-level"
  COURSETYPE_GCSE = "GCSE"

  def predicted_results(self):
    return [x for x in self.all() if x.predicted_grade == True]

  def obtained_results(self):
    return [x for x in self.all() if x.predicted_grade == False]

  def gcses(self):
    """Get list of GCSEs"""
    return [x for x in self.all() if x.qualification_type.exam_type == self.COURSETYPE_GCSE]

  def as_levels(self):
    """Get list of AS-levels"""
    return [x for x in self.all() if x.qualification_type.exam_type == self.COURSETYPE_ASLEVEL]

  def a_levels(self):
    """Get list of A-levels"""
    return [x for x in self.all() if x.qualification_type.exam_type == self.COURSETYPE_ALEVEL]

  def a_and_as(self):
    return self.a_levels() + self.as_levels()

  def gcse_a_stars(self):
    """Get list of A* results"""
    return len([x for x in self.gcses() if x.result == "A*"])

class Qualification(models.Model):
  student = models.ForeignKey("CandidateInfo", related_name="qualifications")
  application_scheme = models.CharField(
    max_length=5,
    verbose_name="UCAS Application Scheme Code",
    help_text=("UCAS Application Scheme code, currently of the form UC0x. "
               "The value of x increments with each new UCAS application.")
    )
  timestamp = models.DateTimeField(auto_now=True)
  # qualid - primary key for ADSS database (could be useful for updates)
  qualification_date = models.DateField(
    help_text="Year and month of qualification"
    )
  qualification_type = models.ForeignKey('QualificationType')
  award_body = models.CharField(
    max_length=255,
    blank=True,
    help_text="Examination board"
    )
  title = models.CharField(
    max_length=255,
    db_index=True,
    help_text="Title of qualification."
    )
  result = models.CharField(
    max_length=255,
    db_index=True,
    blank=True,
    help_text="Examination result awarded or expected."
    )
  grade = models.CharField(
    max_length=255,
    blank=True,
    help_text=("Grade awarded/expected for qualifications that separate "
               "results and grades. Examples of such qualifications "
               "include OCR Advanced Mathematics, Duke of Edinburgh awards "
               "and music examinations. Not used for GCSE/A-level results.")
    )
  predicted_grade = models.BooleanField(
    help_text="True if grade not awarded yet."
    )
  test_centre = models.CharField(
    max_length=255,
    blank=True,
    help_text="UCAS Centre Number ID (numerical)"
    )
  unit_grades = models.TextField(
    blank=True,
    help_text="Extended text field for storing unit grade data."
    )
  objects = QualificationManager()

  def __str__(self):
    return "Qualification: {0} - {1} {2} on {3} - {4}".format(
      self.student,
      self.qualification_type,
      self.title,
      self.qualification_date,
      self.result)

  class Meta:
    verbose_name = "ADSS qualification"
    verbose_name_plural = "ADSS qualifications"

class QualificationType(models.Model):
  """Acts as a lookup table for qualification types and short forms"""
  name = models.CharField(
    max_length=255,
    help_text="Qualification long name"
    )
  exam_type = models.CharField(
    max_length=32,
    help_text="Qualification type for statistics"
    )
  short_name = models.CharField(
    max_length=32,
    help_text="Qualification short name"
    )
  dual_award = models.BooleanField(
    verbose_name="Dual award",
    help_text="If true, worth two qualifications"
    )
  short_course = models.BooleanField(
    verbose_name="Short course",
    help_text="If true, this was a short course"
    )

  def __str__(self):
    return self.name

#===========================================================================

class School(models.Model):
  ATTENDANCE_FULLTIME = "FT"
  ATTENDANCE_PARTTIME = "PT"
  ATTENDANCE_SANDWICH = "SW"
  ATTENDANCE_TYPES = (
    (ATTENDANCE_FULLTIME, "Full-time course"),
    (ATTENDANCE_PARTTIME, "Part-time course"),
    (ATTENDANCE_SANDWICH, "Sandwich course")
    )
    
  student = models.ForeignKey("CandidateInfo", related_name="schools")
  application_scheme = models.CharField(
    max_length=5,
    verbose_name="UCAS Application Scheme Code",
    help_text=("UCAS Application Scheme code, currently of the form UC0x. "
               "The value of x increments with each new UCAS application.")
    )
  timestamp = models.DateTimeField(auto_now=True)
  # educationid - primary key for ADSS database (could be useful for updates)
  start_date = models.DateField(
    help_text="Start date (year and month)"
    )
  end_date = models.DateField(
    help_text="End date (year and month)"
    )
  school_details = models.CharField(
    max_length=255,
    help_text="Details/title of school/establishment."
    )
  ucas_school_id = models.CharField(
    max_length=255,
    blank=True,
    help_text="UCAS School ID, if any (currently numerical)."
    )
  attendance = models.CharField(
    max_length=2,
    default=ATTENDANCE_FULLTIME,
    help_text=("Attendance type (Full-time/part-time/sandwich course). "
               "The default assumption is that courses are full-time.")
    )
  school_type = models.ForeignKey('PhysicsSchoolType', null=True)

  def __str__(self):
    return "School: {0} - {1}-{2} at {3}".format(
      self.student,
      self.start_date,
      self.end_date,
      self.school_details)

  class Meta:
    verbose_name = "ADSS school information"
    verbose_name_plural = "ADSS school information"

class PhysicsSchoolType(models.Model):
  """Acts as a lookup table mapping ADSS school codes to Physics school types"""
  UNKNOWN = 'U'
  COLLEGE = 'S'
  COMPREHENSIVE = 'C'
  INDEPENDENT = 'I'
  GRANT_MAINTAINED = 'M'
  GRAMMAR = 'G'
  OVERSEAS = 'O'
  PHYSICS_CODES = (
    (COMPREHENSIVE, 'Comprehensive (C)'),
    (GRAMMAR, 'Grammar School (G)'),
    (INDEPENDENT, 'Independent (I)'),
    (GRANT_MAINTAINED, 'Grant Maintained School (M)'),
    (OVERSEAS, 'Overseas School (O)'),
    (COLLEGE, 'Sixth-Form College (S)'),
    (UNKNOWN, 'Unknown/Other (U)'),
    )
  adss_type = models.CharField(
    max_length=1,
    primary_key=True,
    help_text="ADSS type code",
    )
  adss_description = models.CharField(
    max_length=255,
    help_text="ADSS description",
    )
  physics_type = models.CharField(
    max_length=1,
    choices=PHYSICS_CODES,
    default=UNKNOWN,
    help_text="Physics type code",
    )

  def __str__(self):
    return "{0}: {1} => {2}".format(
      self.adss_type,
      self.adss_description,
      self.physics_type
      )

#===========================================================================

class CollegeManager(models.Manager):
  def get_by_natural_key(self, code):
    return self.get(adss_code=code)

class College(models.Model):
  """Model representing colleges.  Contains college names and ADSS codes."""
  name = models.CharField(max_length=255, db_index=True)
  adss_code = models.CharField(max_length=3, db_index=True, unique=True)
  total_places = models.IntegerField(
    default=6,
    help_text=("Total number of offers, including PhysPhil, the college"
               " expects to make.  Not an ironclad commitment."),
    )
  physphil_places = models.IntegerField(
    default=1,
    help_text=("Number of PhysPhil places the college expects to make.")
    )
  key = models.CharField(max_length=16)

  objects = CollegeManager()

  def __str__(self):
    return self.name

  def natural_key(self):
    return self.adss_code

  class Meta:
    ordering = ['name']

#===========================================================================

class Offer(models.Model):
  """A possible offer from a college (or open) to a student"""
  college = models.ForeignKey('College', null=True)
  candidate = models.ForeignKey('Candidate', related_name="offer")
  deferred_entry = models.BooleanField(default=False)
  course_type = models.CharField(
    max_length=1,
    choices=Candidate.COURSE_TYPES,
    default=Candidate.COURSE_FOURYEAR,
    help_text="Offered physics course"
    )
  time = models.DateTimeField(
    auto_now_add=True,
    help_text="Date/time of offer in case needed to sort out priority")
  final = models.BooleanField(default=False)
  promoted = models.BooleanField(default=False)
  underwritten = models.BooleanField(default=False)

  def __str__(self):
    return "{0}, {1} ({2} for {3}{4}){5} [{6}]".format(
         self.candidate.info.surname,
         self.candidate.info.forenames,
         self.college.adss_code,
         self.course_type,
         ' deferred' if self.deferred_entry else '',
         ' FINAL' if self.final else '',
         ' promoted' if self.promoted else '',
         ' open/underwritten' if self.underwritten else '',
         self.time)

#===========================================================================

