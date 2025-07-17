from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import logging
from .models import Client, Employee, Rental, Car, CarModel, CarType, Promo, Penalty

logger = logging.getLogger(__name__)

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'placeholder': 'DD.MM.YYYY'
        }),
        required=True,
        input_formats=['%d.%m.%Y', '%Y-%m-%d'],  
        help_text='Must be at least 18 years old'
    )
    phone = forms.CharField(
        max_length=19,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+375 \((17|29|33|44)\) [0-9]{3}-[0-9]{2}-[0-9]{2}$',
                message='Phone number must be in the format: +375 (XX) XXX-XX-XX'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+375 (29) XXX-XX-XX'
        }),
        help_text='Format: +375 (XX) XXX-XX-XX'
    )
    address = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            if isinstance(birth_date, str):
                try:
                    if '.' in birth_date:
                        birth_date = datetime.strptime(birth_date, '%d.%m.%Y').date()
                    else:
                        birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                except ValueError:
                    raise forms.ValidationError('Invalid date format. Use DD.MM.YYYY')
            
            age = relativedelta(date.today(), birth_date).years
            if age < 18:
                raise forms.ValidationError('You must be at least 18 years old to register.')
            
            logger.info(f"Cleaned birth_date: {birth_date}")
        return birth_date

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove any extra whitespace
            phone = ' '.join(phone.split())
            logger.info(f"Cleaned phone: {phone}")
        return phone

class EmployeeRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='Must be at least 18 years old'
    )
    phone = forms.CharField(
        max_length=20,
        help_text='Format: +375 (29) XXX-XX-XX'
    )
    position = forms.CharField(max_length=100)
    photo = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name')

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            age = (date.today() - birth_date).days / 365.25
            if age < 18:
                raise forms.ValidationError('You must be at least 18 years old.')
        return birth_date

class RentalForm(forms.ModelForm):
    promo_code = forms.CharField(max_length=20, required=False, help_text='Enter promo code if you have one')
    start_date = forms.DateField(
        label='Дата начала',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': datetime.now().date().isoformat()
        }),
        help_text='Выберите дату начала аренды'
    )
    end_date = forms.DateField(
        label='Дата окончания',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': datetime.now().date().isoformat()
        }),
        help_text='Выберите дату окончания аренды'
    )
    days = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = Rental
        fields = ['car', 'start_date', 'end_date', 'days']
        widgets = {
            'car': forms.Select(
                attrs={
                    'class': 'form-control',
                    'required': True
                }
            )
        }
        labels = {
            'car': 'Автомобиль'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Показываем все машины, так как их доступность будет проверяться для конкретных дат
        self.fields['car'].queryset = Car.objects.all()
        self.fields['car'].empty_label = 'Выберите автомобиль'
        self.fields['car'].label_from_instance = lambda obj: f"{obj.model.name} ({obj.license_plate}) - ${obj.daily_rate}/день"

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        car = cleaned_data.get('car')

        if start_date and end_date and car:
            # Проверяем, что дата начала не в прошлом
            if start_date < datetime.now().date():
                raise forms.ValidationError('Дата начала аренды не может быть в прошлом')

            # Проверяем, что дата окончания позже даты начала
            if end_date <= start_date:
                raise forms.ValidationError('Дата окончания должна быть позже даты начала')

            # Вычисляем количество дней
            delta = end_date - start_date
            cleaned_data['days'] = delta.days + 1

            # Проверяем, не арендована ли машина на выбранные даты
            conflicting_rentals = Rental.objects.filter(
                car=car,
                status='active',
                start_date__lt=end_date,
                expected_return_date__gt=start_date
            )

            if conflicting_rentals.exists():
                # Получаем все занятые периоды для этой машины
                busy_periods = conflicting_rentals.values_list('start_date', 'expected_return_date')
                busy_periods_str = [
                    f"с {start.strftime('%d.%m.%Y')} по {end.strftime('%d.%m.%Y')}"
                    for start, end in busy_periods
                ]
                raise forms.ValidationError(
                    f"Автомобиль уже арендован в следующие периоды: {', '.join(busy_periods_str)}. "
                    f"Пожалуйста, выберите другие даты."
                )

        return cleaned_data

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['phone', 'birth_date', 'address']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'})
        }

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['license_plate', 'model', 'year', 'value', 'daily_rate', 'is_available', 'image']
        widgets = {
            'license_plate': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1900, 'max': datetime.now().year + 1}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'daily_rate': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={'class': 'form-control'})
        }
        labels = {
            'license_plate': 'Номерной знак',
            'model': 'Модель',
            'year': 'Год выпуска',
            'value': 'Стоимость',
            'daily_rate': 'Стоимость аренды в день',
            'is_available': 'Доступен для аренды',
            'image': 'Изображение'
        }

class CarModelForm(forms.ModelForm):
    class Meta:
        model = CarModel
        fields = ['name', 'manufacturer', 'car_type', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'car_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }
        labels = {
            'name': 'Название модели',
            'manufacturer': 'Производитель',
            'car_type': 'Тип автомобиля',
            'description': 'Описание'
        }

class CarTypeForm(forms.ModelForm):
    class Meta:
        model = CarType
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }
        labels = {
            'name': 'Название типа',
            'description': 'Описание'
        }

class RentalCompleteForm(forms.ModelForm):
    penalties = forms.ModelMultipleChoiceField(
        queryset=Penalty.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Штрафы'
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label='Заметки о состоянии автомобиля'
    )

    class Meta:
        model = Rental
        fields = ['penalties', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['base_amount'] = forms.DecimalField(
                disabled=True,
                initial=self.instance.base_amount,
                label='Базовая стоимость'
            )
            self.fields['discount_amount'] = forms.DecimalField(
                disabled=True,
                initial=self.instance.calculate_discount_amount(),
                label='Сумма скидки'
            )
            self.fields['penalty_amount'] = forms.DecimalField(
                disabled=True,
                initial=self.instance.calculate_penalty_amount(),
                label='Сумма штрафов'
            )
            self.fields['final_amount'] = forms.DecimalField(
                disabled=True,
                initial=self.instance.calculate_final_amount(),
                label='Итоговая сумма'
            ) 