from django.test import TransactionTestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from main.models import (
    CarType, CarModel, Car, Client, Rental, Article,
    CompanyInfo, FAQ, Employee, JobVacancy, Review, Promo
)

class TestCarType(TransactionTestCase):
    def test_create_car_type(self):
        car_type = CarType.objects.create(
            name='SUV',
            description='Sport Utility Vehicle'
        )
        self.assertEqual(car_type.name, 'SUV')
        self.assertEqual(car_type.description, 'Sport Utility Vehicle')

class TestCarModel(TransactionTestCase):
    def test_create_car_model(self):
        car_type = CarType.objects.create(name='Sedan', description='Family car')
        car_model = CarModel.objects.create(
            name='Camry',
            manufacturer='Toyota',
            car_type=car_type,
            description='Reliable family sedan'
        )
        self.assertEqual(car_model.name, 'Camry')
        self.assertEqual(car_model.manufacturer, 'Toyota')
        self.assertEqual(car_model.car_type, car_type)

class TestCar(TransactionTestCase):
    def test_create_car(self):
        car_type = CarType.objects.create(name='Sedan', description='Family car')
        car_model = CarModel.objects.create(
            name='Camry',
            manufacturer='Toyota',
            car_type=car_type,
            description='Reliable family sedan'
        )
        car = Car.objects.create(
            license_plate='ABC123',
            model=car_model,
            year=2020,
            value=25000.00,
            daily_rate=50.00
        )
        self.assertEqual(car.license_plate, 'ABC123')
        self.assertEqual(car.year, 2020)
        self.assertTrue(car.is_available)

class TestClient(TransactionTestCase):
    def test_create_client(self):
        user = User.objects.create_user(
            username='testuser_client_create',
            password='testpass123'
        )
        client = Client.objects.create(
            user=user,
            phone='+375 (29) 123-45-67',
            birth_date='1990-01-01',
            address='Test Address'
        )
        self.assertEqual(client.user, user)
        self.assertEqual(client.phone, '+375 (29) 123-45-67')

    def test_underage_client(self):
        user = User.objects.create_user(
            username='younguser_client_underage',
            password='testpass123'
        )
        with self.assertRaises(ValidationError):
            client = Client(
                user=user,
                phone='+375 (29) 123-45-67',
                birth_date=timezone.now().date(),
                address='Test Address'
            )
            client.full_clean()

class TestRental(TransactionTestCase):
    def test_create_rental(self):
        # Create necessary objects
        car_type = CarType.objects.create(name='Sedan', description='Family car')
        car_model = CarModel.objects.create(
            name='Camry',
            manufacturer='Toyota',
            car_type=car_type,
            description='Reliable family sedan'
        )
        car = Car.objects.create(
            license_plate='ABC123',
            model=car_model,
            year=2020,
            value=25000.00,
            daily_rate=50.00
        )
        user = User.objects.create_user(
            username='testuser_rental_create',
            password='testpass123'
        )
        client = Client.objects.create(
            user=user,
            phone='+375 (29) 123-45-67',
            birth_date='1990-01-01',
            address='Test Address'
        )
        
        # Create rental
        rental = Rental.objects.create(
            car=car,
            client=client,
            start_date=timezone.now(),
            days=3,
            expected_return_date=timezone.now() + timezone.timedelta(days=3),
            base_amount=150.00,
            final_amount=150.00,
            status='active'
        )
        
        self.assertEqual(rental.car, car)
        self.assertEqual(rental.client, client)
        self.assertEqual(rental.days, 3)
        self.assertEqual(rental.status, 'active')

class TestArticle(TransactionTestCase):
    def test_create_article(self):
        article = Article.objects.create(
            title='Test Article',
            content='Test content'
        )
        self.assertEqual(article.title, 'Test Article')
        self.assertEqual(article.content, 'Test content')

class TestReview(TransactionTestCase):
    def test_create_review(self):
        user = User.objects.create_user(
            username='testuser_review_create',
            password='testpass123'
        )
        client = Client.objects.create(
            user=user,
            phone='+375 (29) 123-45-67',
            birth_date='1990-01-01',
            address='Test Address'
        )
        review = Review.objects.create(
            client=client,
            rating=5,
            text='Great service!'
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.text, 'Great service!')

class TestPromo(TransactionTestCase):
    def test_create_promo(self):
        promo = Promo.objects.create(
            code='SUMMER2024',
            description='Summer discount',
            discount_percent=10,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timezone.timedelta(days=30),
            is_active=True
        )
        self.assertEqual(promo.code, 'SUMMER2024')
        self.assertEqual(promo.discount_percent, 10)
        self.assertTrue(promo.is_active) 