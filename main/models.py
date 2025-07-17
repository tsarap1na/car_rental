from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from datetime import date, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

class CarType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name

class CarModel(models.Model):
    name = models.CharField(max_length=50)
    manufacturer = models.CharField(max_length=50)
    car_type = models.ForeignKey(CarType, on_delete=models.CASCADE)
    description = models.TextField()

    def __str__(self):
        return f"{self.manufacturer} {self.name}"

class Car(models.Model):
    model = models.ForeignKey(CarModel, on_delete=models.CASCADE)
    license_plate = models.CharField(max_length=10)
    year = models.IntegerField()
    value = models.DecimalField(max_digits=10, decimal_places=2)
    daily_rate = models.DecimalField(max_digits=6, decimal_places=2)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='cars/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.model} ({self.license_plate})"

    def check_maintenance_status(self):
        if not self.last_maintenance:
            self.needs_maintenance = True
            self.save()
            return

        days_since_maintenance = (timezone.now().date() - self.last_maintenance).days
        if days_since_maintenance >= self.maintenance_interval:
            self.needs_maintenance = True
            self.save()

    def complete_maintenance(self):
        self.last_maintenance = timezone.now().date()
        self.needs_maintenance = False
        self.maintenance_notes += f"\nТО выполнено {timezone.now().date()}"
        self.save()

    class Meta:
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'
        ordering = ['-year']

class CarPark(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    cars = models.ManyToManyField(Car)

    def __str__(self):
        return self.name

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, validators=[
        RegexValidator(
            regex=r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$',
            message='Phone number must be in format: +375 (XX) XXX-XX-XX'
        )
    ])
    birth_date = models.DateField()
    address = models.TextField()

    def clean(self):
        if self.birth_date:
            age = (date.today() - self.birth_date).days / 365.25
            if age < 18:
                raise ValidationError('Client must be at least 18 years old.')

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

class Discount(models.Model):
    name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"

class Penalty(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.name} (${self.amount})"

class Rental(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    days = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(30)])
    expected_return_date = models.DateTimeField()
    actual_return_date = models.DateTimeField(null=True, blank=True)
    base_amount = models.DecimalField(max_digits=8, decimal_places=2)
    final_amount = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    promo_code = models.ForeignKey('Promo', on_delete=models.SET_NULL, null=True, blank=True)
    penalties = models.ManyToManyField(Penalty, blank=True)
    notes = models.TextField(blank=True, verbose_name='Заметки')

    def clean(self):
        if self.start_date and self.start_date < timezone.now():
            raise ValidationError('Start date cannot be in the past.')

    def calculate_discount_amount(self):
        if not self.promo_code:
            return Decimal('0.00')
        discount_multiplier = Decimal(str(self.promo_code.discount_percent)) / Decimal('100')
        return self.base_amount * discount_multiplier

    def calculate_penalty_amount(self):
        return sum(penalty.amount for penalty in self.penalties.all())

    def calculate_final_amount(self):
        discount_amount = self.calculate_discount_amount()
        penalty_amount = self.calculate_penalty_amount()
        return self.base_amount - discount_amount + penalty_amount

    def update_final_amount(self):
        self.final_amount = self.calculate_final_amount()
        self.save()

    def __str__(self):
        return f"{self.car} - {self.client} ({self.start_date})"

    class Meta:
        verbose_name = 'Аренда'
        verbose_name_plural = 'Аренды'

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='articles/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class CompanyInfo(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    address = models.TextField(default='', blank=True)
    phone = models.CharField(max_length=20, default='', blank=True)
    email = models.EmailField(default='info@example.com')

    def __str__(self):
        return self.name

class FAQ(models.Model):
    question = models.CharField(max_length=200)
    answer = models.TextField()

    def __str__(self):
        return self.question

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='employees/', null=True, blank=True)
    phone_regex = RegexValidator(
        regex=r'^\+375 \((?:29|33|44|25)\) [0-9]{3}-[0-9]{2}-[0-9]{2}$',
        message="Phone number must be entered in the format: '+375 (29) XXX-XX-XX'"
    )
    phone = models.CharField(validators=[phone_regex], max_length=20)
    email = models.EmailField()
    birth_date = models.DateField()

    def clean(self):
        if self.birth_date:
            age = (date.today() - self.birth_date).days / 365.25
            if age < 18:
                raise ValidationError('Employee must be at least 18 years old.')

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"

class JobVacancy(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    requirements = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Review(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client} - {self.rating}/5"

class Promo(models.Model):
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    discount_percent = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def clean(self):
        if self.valid_until <= self.valid_from:
            raise ValidationError('Valid until must be after valid from.')

    def __str__(self):
        return f"{self.code} ({self.discount_percent}% off)"
