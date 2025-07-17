from django.test import TransactionTestCase, Client as TestClient
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from main.models import Car, CarType, CarModel, Client, Rental

class TestViews(TransactionTestCase):
    def setUp(self):
        # Create test user with unique username
        self.user = User.objects.create_user(
            username='testuser_views',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create client
        self.client_obj = Client.objects.create(
            user=self.user,
            phone='+375 (29) 123-45-67',
            birth_date='1990-01-01',
            address='Test Address'
        )
        
        # Create car objects
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

        # Create test client
        self.test_client = TestClient()

    def test_home_view(self):
        url = reverse('main:home')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/home.html')

    def test_car_list_view(self):
        url = reverse('main:car_list')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/car_list_new.html')
        self.assertIn(self.car, response.context['cars'])

    def test_car_detail_view(self):
        url = reverse('main:car_detail', kwargs={'pk': self.car.pk})
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/car_detail.html')
        self.assertEqual(response.context['car'], self.car)

    def test_rental_list_view_unauthorized(self):
        url = reverse('main:rental_list')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/login/', response.url)

    def test_rental_list_view_authorized(self):
        self.test_client.login(username='testuser_views', password='testpass123')
        url = reverse('main:rental_list')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/rental_list.html')

    def test_profile_view_unauthorized(self):
        url = reverse('main:profile')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_profile_view_authorized(self):
        self.test_client.login(username='testuser_views', password='testpass123')
        url = reverse('main:profile')
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main/profile.html')
        self.assertEqual(response.context['client'], self.client_obj) 