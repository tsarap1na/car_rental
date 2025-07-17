from django.test import TransactionTestCase
from django.utils import timezone
from main.forms import RegistrationForm, RentalForm, ClientForm
from main.models import Car, CarType, CarModel, Client
from django.contrib.auth.models import User

class TestForms(TransactionTestCase):
    def setUp(self):
        # Create test car objects
        self.car_type = CarType.objects.create(
            name='Sedan',
            description='Family car'
        )
        
        self.car_model = CarModel.objects.create(
            name='Camry',
            manufacturer='Toyota',
            car_type=self.car_type,
            description='Reliable family sedan'
        )
        
        self.car = Car.objects.create(
            license_plate='ABC123',
            model=self.car_model,
            year=2020,
            value=25000.00,
            daily_rate=50.00
        )

    def test_registration_form_valid(self):
        form_data = {
            'username': 'testuser_reg',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'birth_date': '1990-01-01',
            'phone': '+375 (29) 123-45-67',
            'address': 'Test Address'
        }
        form = RegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_registration_form_invalid_password_mismatch(self):
        form_data = {
            'username': 'testuser_reg2',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'wrongpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'birth_date': '1990-01-01',
            'phone': '+375 (29) 123-45-67',
            'address': 'Test Address'
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_registration_form_invalid_underage(self):
        form_data = {
            'username': 'testuser_reg3',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'birth_date': timezone.now().date().isoformat(),
            'phone': '+375 (29) 123-45-67',
            'address': 'Test Address'
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('birth_date', form.errors)

    def test_rental_form_valid(self):
        # Create test user and client
        user = User.objects.create_user(
            username='testuser_rental',
            password='testpass123'
        )
        client = Client.objects.create(
            user=user,
            phone='+375 (29) 123-45-67',
            birth_date='1990-01-01',
            address='Test Address'
        )

        start_date = timezone.now().date()
        end_date = start_date + timezone.timedelta(days=3)
        
        form_data = {
            'car': self.car.id,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': 3
        }
        form = RentalForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_rental_form_invalid_past_date(self):
        start_date = timezone.now().date() - timezone.timedelta(days=1)
        end_date = start_date + timezone.timedelta(days=3)
        
        form_data = {
            'car': self.car.id,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': 3
        }
        form = RentalForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Дата начала аренды не может быть в прошлом', form.errors['__all__'][0])

    def test_client_form_valid(self):
        form_data = {
            'phone': '+375 (29) 123-45-67',
            'birth_date': '1990-01-01',
            'address': 'Test Address'
        }
        form = ClientForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_client_form_invalid_phone(self):
        form_data = {
            'phone': 'invalid-phone',
            'birth_date': '1990-01-01',
            'address': 'Test Address'
        }
        form = ClientForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors) 