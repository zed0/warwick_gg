import json
from functools import reduce

from django.conf import settings
from django.db import models
from django.utils import timezone
from multiselectfield import MultiSelectField


class SeatingRoom(models.Model):
    name = models.CharField(max_length=100)
    seating_plan_svg = models.FileField(upload_to='seating/')
    """
    This field will contain a literal array of integers in JSON list notation ([2, 3, 4, 5]). Each position
    corresponds to a table, and the value is the total seats on that table. For example: [20, 20, 20, 10] would
    be the standard LIB2 set up.
    """
    tables_raw = models.TextField(
        help_text='This field will contain a literal array of integers in JSON list notation ([2, 3, 4, 5]). Each position corresponds to a table, and the value is the total seats on that table. For example: [20, 20, 20, 10] would be the standard LIB2 set up.')

    @property
    def tables(self):
        tables = json.loads(self.tables_raw)
        return {k: v for k, v in enumerate(tables)}

    @property
    def tables_pretty(self):
        return ',\n'.join(map(lambda i: 'Table {k}: {v} seats'.format(k=(i[0] + 1), v=i[1]), self.tables.items()))

    @property
    def max_capacity(self):
        return reduce(lambda x, y: x + y, self.tables.values())

    def save_tables(self, tables):
        self.tables_raw = json.dumps(tables)

    def __str__(self):
        return self.name


class Event(models.Model):
    SOCIETY_CHOICES = (
        ('UWCS', 'Uni of Warwick Computing Society'),
        ('WE', 'Warwick Esports'),
    )

    id = models.IntegerField(primary_key=True)

    # Event display information
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(default=timezone.now)

    # Signup information
    signup_start = models.DateTimeField(default=timezone.now)
    signup_end = models.DateTimeField(default=timezone.now)
    signup_start_fresher = models.DateTimeField(blank=True)
    signup_limit = models.IntegerField(default=70)

    # Society eligibility criteria
    event_for = MultiSelectField(blank=True, choices=SOCIETY_CHOICES, max_choices=2)
    cost_member = models.DecimalField(default=0, decimal_places=2, max_digits=3)
    cost_nonmember = models.DecimalField(default=5, decimal_places=2, max_digits=3)

    # Seating plan
    has_seating = models.BooleanField(default=True)
    seating_location = models.ForeignKey(SeatingRoom, on_delete=models.PROTECT, blank=True, null=True)

    @property
    def signups(self):
        signups = EventSignup.objects.filter(event=self).all().order_by('-signup_created')

        return signups

    @property
    def signup_count(self):
        return len(self.signups)

    @property
    def is_ongoing(self):
        if self.start < timezone.now() <= self.end:
            return True
        else:
            return False


class EventSignup(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    comment = models.TextField(blank=True, max_length=1024)

    class Meta:
        ordering = ['created_at']
        unique_together = ('user', 'event')