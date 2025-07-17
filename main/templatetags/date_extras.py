from django import template
from django.utils import timezone
import calendar
from datetime import datetime, date
import pytz

register = template.Library()

@register.simple_tag
def get_calendar(year=None, month=None):
    if year is None:
        year = timezone.now().year
    if month is None:
        month = timezone.now().month
    
    cal = calendar.TextCalendar(calendar.MONDAY)
    return cal.formatmonth(year, month)

@register.filter
def format_datetime(dt, tz=None):
    if not dt:
        return ''
    if tz and isinstance(dt, datetime):
        dt = dt.astimezone(pytz.timezone(tz))
    return dt.strftime('%d/%m/%Y %H:%M:%S')

@register.filter
def format_date(dt, tz=None):
    if not dt:
        return ''
    if isinstance(dt, datetime):
        if tz:
            dt = dt.astimezone(pytz.timezone(tz))
        return dt.strftime('%d/%m/%Y')
    elif isinstance(dt, date):
        return dt.strftime('%d/%m/%Y') 