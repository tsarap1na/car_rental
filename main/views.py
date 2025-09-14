from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.views import LoginView as AuthLoginView, LogoutView as AuthLogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Avg, Count, Sum, Q, Min, Max
from django.utils import timezone
from .models import (
    Car, CarModel, CarType, Client, Rental, Article, CompanyInfo,
    FAQ, Employee, JobVacancy, Review, Promo
)
from .forms import (
    RegistrationForm, EmployeeRegistrationForm, RentalForm, ClientForm,
    CarForm, CarModelForm, CarTypeForm, RentalCompleteForm
)
from django.contrib import messages
from django.views import View
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.db import transaction
from django.contrib.auth.models import User, Group
import logging
from django.core.exceptions import PermissionDenied
import requests
from django.core.cache import cache
from datetime import datetime, timedelta
import re
import pytz
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import base64
from decimal import Decimal

logger = logging.getLogger(__name__)

# Create your views here.

class HomeView(TemplateView):
    template_name = 'main/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_article'] = Article.objects.order_by('-created_at').first()
        
        # Get cat fact from cache or API
        today = datetime.now().date().isoformat()
        cat_cache_key = f'cat_fact_{today}'
        cat_fact = cache.get(cat_cache_key)
        
        if not cat_fact:
            try:
                response = requests.get('https://catfact.ninja/fact')
                if response.status_code == 200:
                    cat_fact = response.json()['fact']
                    # Cache the fact for 24 hours
                    cache.set(cat_cache_key, cat_fact, 60 * 60 * 24)
                else:
                    cat_fact = "Did you know? Cats are amazing!"
            except Exception as e:
                cat_fact = "Did you know? Cats are amazing!"
        
        context['cat_fact'] = cat_fact

        # Get programming joke from cache or API
        joke_cache_key = 'programming_joke'
        joke_data = cache.get(joke_cache_key)
        
        if not joke_data:
            try:
                response = requests.get('https://official-joke-api.appspot.com/jokes/programming/random')
                if response.status_code == 200:
                    joke = response.json()[0]  # API returns array with one joke
                    joke_data = {
                        'setup': joke['setup'],
                        'punchline': joke['punchline'],
                        'updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    # Cache the joke for 1 hour
                    cache.set(joke_cache_key, joke_data, 60 * 60)
                else:
                    joke_data = None
            except Exception as e:
                print(f"Exception occurred: {str(e)}")
                joke_data = None
        
        context['joke_data'] = joke_data
        return context

class AboutView(TemplateView):
    template_name = 'main/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company_info'] = CompanyInfo.objects.first()
        return context

class ArticleListView(ListView):
    model = Article
    template_name = 'main/news.html'
    context_object_name = 'articles'
    ordering = ['-created_at']
    paginate_by = 10

class ArticleDetailView(DetailView):
    model = Article
    template_name = 'main/article_detail.html'
    context_object_name = 'article'

class FAQListView(ListView):
    model = FAQ
    template_name = 'main/faq.html'
    context_object_name = 'faqs'

class ContactsView(TemplateView):
    template_name = 'main/contacts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем всех сотрудников, отсортированных по позиции
        context['employees'] = Employee.objects.select_related('user').all().order_by('position')
        return context

class PrivacyPolicyView(TemplateView):
    template_name = 'main/privacy.html'

class JobVacancyListView(ListView):
    model = JobVacancy
    template_name = 'main/jobs.html'
    context_object_name = 'vacancies'
    queryset = JobVacancy.objects.filter(is_active=True)

class ReviewListView(ListView):
    model = Review
    template_name = 'main/reviews.html'
    context_object_name = 'reviews'
    ordering = ['-created_at']
    paginate_by = 10

class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    template_name = 'main/review_form.html'
    fields = ['rating', 'text']
    success_url = reverse_lazy('main:reviews')

    def form_valid(self, form):
        form.instance.client = self.request.user.client
        return super().form_valid(form)

class PromoListView(ListView):
    model = Promo
    template_name = 'main/promos.html'
    context_object_name = 'promos'

    def get_queryset(self):
        now = timezone.now()
        return Promo.objects.filter(
            valid_from__lte=now,
            valid_until__gte=now,
            is_active=True
        )

class StaffEmployeeRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.is_staff or (hasattr(self.request.user, 'employee') and self.request.user.employee)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("У вас нет прав для выполнения этого действия.")

class CarCreateView(LoginRequiredMixin, StaffEmployeeRequiredMixin, CreateView): #CREATE
    model = Car
    form_class = CarForm
    template_name = 'main/car_form.html'
    success_url = reverse_lazy('main:car_list')

    def form_valid(self, form):
        messages.success(self.request, 'Автомобиль успешно добавлен!')
        return super().form_valid(form)

class CarUpdateView(LoginRequiredMixin, StaffEmployeeRequiredMixin, UpdateView): #UPDATE
    model = Car
    form_class = CarForm
    template_name = 'main/car_form.html'
    success_url = reverse_lazy('main:car_list')

    def form_valid(self, form):
        messages.success(self.request, 'Информация об автомобиле обновлена!')
        return super().form_valid(form)

class CarDeleteView(LoginRequiredMixin, StaffEmployeeRequiredMixin, DeleteView):
    model = Car
    template_name = 'main/car_confirm_delete.html'
    success_url = reverse_lazy('main:car_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Автомобиль успешно удален!')
        return super().delete(request, *args, **kwargs)

class CarModelCreateView(LoginRequiredMixin, StaffEmployeeRequiredMixin, CreateView):
    model = CarModel
    form_class = CarModelForm
    template_name = 'main/car_model_form.html'
    success_url = reverse_lazy('main:car_list')

    def form_valid(self, form):
        messages.success(self.request, 'Модель автомобиля успешно добавлена!')
        return super().form_valid(form)

class CarModelUpdateView(LoginRequiredMixin, StaffEmployeeRequiredMixin, UpdateView):
    model = CarModel
    form_class = CarModelForm
    template_name = 'main/car_model_form.html'
    success_url = reverse_lazy('main:car_list')

    def form_valid(self, form):
        messages.success(self.request, 'Модель автомобиля обновлена!')
        return super().form_valid(form)

class CarTypeCreateView(LoginRequiredMixin, StaffEmployeeRequiredMixin, CreateView):
    model = CarType
    form_class = CarTypeForm
    template_name = 'main/car_type_form.html'
    success_url = reverse_lazy('main:car_list')

    def form_valid(self, form):
        messages.success(self.request, 'Тип автомобиля успешно добавлен!')
        return super().form_valid(form)

class CarTypeUpdateView(LoginRequiredMixin, StaffEmployeeRequiredMixin, UpdateView):
    model = CarType
    form_class = CarTypeForm
    template_name = 'main/car_type_form.html'
    success_url = reverse_lazy('main:car_list')

    def form_valid(self, form):
        messages.success(self.request, 'Тип автомобиля обновлен!')
        return super().form_valid(form)

class CarListView(ListView):
    model = Car
    template_name = 'main/car_list_new.html'
    context_object_name = 'cars'
    paginate_by = 12

    def get_queryset(self):
        queryset = Car.objects.all()
        
        # Фильтрация по типу автомобиля
        car_type = self.request.GET.get('type')
        if car_type:
            queryset = queryset.filter(model__car_type__id=car_type)
        
        # Сортировка по цене
        sort = self.request.GET.get('sort')
        if sort == 'price_asc':
            queryset = queryset.order_by('daily_rate')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-daily_rate')
        else:
            queryset = queryset.order_by('model__name')  # По умолчанию сортируем по названию модели
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['car_types'] = CarType.objects.all()
        context['manufacturers'] = CarModel.objects.values_list('manufacturer', flat=True).distinct()
        context['min_price'] = Car.objects.aggregate(Min('daily_rate'))['daily_rate__min']
        context['max_price'] = Car.objects.aggregate(Max('daily_rate'))['daily_rate__max']
        
        if self.request.user.is_authenticated:
            context['active_promos'] = Promo.objects.filter(
                valid_from__lte=timezone.now(),
                valid_until__gte=timezone.now(),
                is_active=True
            )
        
        return context

class CarManagementView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'main/car_management.html'
    
    def test_func(self):
        return self.request.user.is_staff or (hasattr(self.request.user, 'employee') and self.request.user.employee)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cars'] = Car.objects.all()
        context['car_types'] = CarType.objects.all()
        context['car_models'] = CarModel.objects.all()
        context['total_rentals'] = Rental.objects.count()
        context['active_rentals'] = Rental.objects.filter(status='active').count()
        context['maintenance_cars'] = Car.objects.filter(needs_maintenance=True)
        return context

class PromoManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Promo
    template_name = 'main/promo_management.html'
    context_object_name = 'promos'
    
    def test_func(self):
        return self.request.user.is_staff or (hasattr(self.request.user, 'employee') and self.request.user.employee)
    
    def get_queryset(self):
        return Promo.objects.all().order_by('-valid_until')

class ClientPromoListView(LoginRequiredMixin, ListView):
    model = Promo
    template_name = 'main/client_promos.html'
    context_object_name = 'promos'
    
    def get_queryset(self):
        return Promo.objects.filter(
            valid_from__lte=timezone.now(),
            valid_until__gte=timezone.now(),
            is_active=True
        ).order_by('-discount_percent')

class CarDetailView(DetailView):
    model = Car
    template_name = 'main/car_detail.html'
    context_object_name = 'car'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # По умолчанию скрываем управление
        context['show_management'] = False
        
        # Проверяем права доступа
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                context['show_management'] = True
            
            context['active_promos'] = Promo.objects.filter(
                valid_from__lte=timezone.now(),
                valid_until__gte=timezone.now(),
                is_active=True
            )
        
        # Добавляем отладочную информацию
        context['debug'] = {
            'is_authenticated': self.request.user.is_authenticated,
            'is_staff': self.request.user.is_staff,
            'is_employee': hasattr(self.request.user, 'employee') and self.request.user.employee,
            'show_management': context['show_management']
        }
        
        return context

class RentalListView(LoginRequiredMixin, ListView):
    model = Rental
    template_name = 'main/rental_list.html'
    context_object_name = 'rentals'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_staff:
            return Rental.objects.all().order_by('-start_date')
        return Rental.objects.filter(client=self.request.user.client).order_by('-start_date')

class RentalCreateView(LoginRequiredMixin, CreateView):
    model = Rental
    form_class = RentalForm
    template_name = 'main/rental_form.html'
    success_url = reverse_lazy('main:rental_list')

    def get_initial(self):
        initial = super().get_initial()
        car_id = self.request.GET.get('car')
        if car_id:
            try:
                car = Car.objects.get(pk=car_id)
                initial['car'] = car
            except Car.DoesNotExist:
                pass
        initial['start_date'] = timezone.now().date()
        return initial

    def form_valid(self, form):
        rental = form.save(commit=False)
        rental.client = self.request.user.client
        
        # Устанавливаем даты и количество дней
        rental.start_date = form.cleaned_data['start_date']
        rental.expected_return_date = form.cleaned_data['end_date']
        rental.days = form.cleaned_data['days']
        
        # Рассчитываем базовую стоимость
        rental.base_amount = rental.car.daily_rate * rental.days
        rental.final_amount = rental.base_amount

        # Применяем промокод, если он есть и валиден
        promo_code = form.cleaned_data.get('promo_code')
        if promo_code:
            try:
                promo = Promo.objects.get(code=promo_code)
                if promo.is_active and timezone.now() >= promo.valid_from and timezone.now() <= promo.valid_until:
                    rental.promo_code = promo
                    discount_multiplier = Decimal('1') - (Decimal(str(promo.discount_percent)) / Decimal('100'))
                    rental.final_amount = rental.base_amount * discount_multiplier
                    messages.success(
                        self.request, 
                        f'Promo code applied! You saved {promo.discount_percent}% ' +
                        f'(${rental.base_amount - rental.final_amount:.2f})'
                    )
            except Promo.DoesNotExist:
                messages.warning(self.request, 'Invalid promo code.')
        
        rental.status = 'active'
        rental.save()
        
        messages.success(self.request, 'Rental successfully created!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error creating rental. Please check the entered data.')
        return super().form_invalid(form)

class RentalDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Rental
    template_name = 'main/rental_detail.html'
    context_object_name = 'rental'

    def test_func(self):
        rental = self.get_object()
        return self.request.user.is_staff or rental.client.user == self.request.user

class ProfileView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Get rentals through the client relationship
        rentals = Rental.objects.filter(client=request.user.client).order_by('-start_date')
        
        # Get timezone info
        user_timezone = request.COOKIES.get('user_timezone', 'UTC')
        current_time = timezone.now()
        utc_time = current_time.astimezone(pytz.UTC)
        user_time = current_time.astimezone(pytz.timezone(user_timezone))
        
        context = {
            'rentals': rentals,
            'client': request.user.client,
            'user_timezone': user_timezone,
            'current_time': current_time,
            'utc_time': utc_time,
            'user_time': user_time,
            'available_timezones': pytz.common_timezones,
        }
        
        return render(request, 'main/profile.html', context)

class ProfileEditView(LoginRequiredMixin, View):
    template_name = 'main/profile_edit.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'user': request.user,
            'client': request.user.client
        })

    def post(self, request, *args, **kwargs):
        user = request.user
        client = user.client

        # Update User model
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()

        # Update Client model
        client.phone = request.POST.get('phone', '')
        client.address = request.POST.get('address', '')
        client.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('main:profile')

class CustomLoginView(AuthLoginView):
    template_name = 'main/login.html'
    redirect_authenticated_user = True

class RegisterView(CreateView):
    template_name = 'main/register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('main:login')

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        email = form.cleaned_data.get('email')
        birth_date = form.cleaned_data.get('birth_date')
        phone = form.cleaned_data.get('phone')
        address = form.cleaned_data.get('address')
        
        logger.info(f"Form data received - Username: {username}, Email: {email}")
        logger.info(f"Birth date: {birth_date} (type: {type(birth_date)})")
        logger.info(f"Phone: {phone}")
        logger.info(f"Address: {address}")

        try:
            with transaction.atomic():
                # First check if user exists
                if User.objects.filter(username=username).exists():
                    messages.error(self.request, 'Username already exists.')
                    return self.form_invalid(form)
                
                if User.objects.filter(email=email).exists():
                    messages.error(self.request, 'Email already registered.')
                    return self.form_invalid(form)

                # Create the user first
                user = form.save(commit=False)
                user.save()
                logger.info(f"User created with id: {user.id}")

                # Create client profile
                try:
                    client = Client.objects.create(
                        user=user,
                        birth_date=birth_date,
                        phone=phone,
                        address=address
                    )
                    logger.info(f"Client profile created with id: {client.id}")
                    
                except Exception as client_error:
                    logger.error(f"Error creating client profile: {str(client_error)}")
                    raise  # Re-raise the exception to trigger transaction rollback

                messages.success(self.request, 'Registration successful! Please log in.')
                return redirect(self.success_url)

        except Exception as e:
            logger.error(f"Error during registration: {str(e)}", exc_info=True)
            messages.error(self.request, 'Registration failed. Please try again.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        logger.warning("Form validation failed")
        for field, errors in form.errors.items():
            for error in errors:
                logger.warning(f"Form error - {field}: {error}")
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('main:home')
        return super().get(request, *args, **kwargs)

class LogoutView(View):
    def post(self, request):
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, 'You have been successfully logged out.')
        return redirect('main:home')

    def get(self, request):
        if request.user.is_authenticated:
            return render(request, 'main/logout.html')
        return redirect('main:home')

class StatisticsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'main/statistics.html'

    def test_func(self):
        return self.request.user.is_staff

    def generate_car_type_chart(self, popular_car_types):
        """Generate bar chart for car type popularity"""
        if not popular_car_types:
            return None
            
        plt.figure(figsize=(10, 6))
        names = [car_type.name for car_type in popular_car_types]
        counts = [car_type.rental_count for car_type in popular_car_types]
        
        bars = plt.bar(names, counts, color='#3498db', alpha=0.7, edgecolor='#2980b9', linewidth=1)
        plt.title('Car Type Popularity', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Car Types', fontsize=12)
        plt.ylabel('Number of Rentals', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(count), ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # Convert to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode()

    def generate_availability_chart(self, available_cars, total_cars):
        """Generate pie chart for car availability"""
        if total_cars == 0:
            return None
            
        rented_cars = total_cars - available_cars
        labels = ['Available', 'Rented']
        sizes = [available_cars, rented_cars]
        colors = ['#2ecc71', '#e74c3c']
        
        plt.figure(figsize=(8, 8))
        wedges, texts, autotexts = plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                          startangle=90, textprops={'fontsize': 12})
        
        # Customize text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(14)
        
        plt.title('Car Availability', fontsize=16, fontweight='bold', pad=20)
        plt.axis('equal')
        
        # Convert to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Rental statistics
        rentals = Rental.objects.all()
        context['total_rentals'] = rentals.count()
        context['total_revenue'] = rentals.aggregate(Sum('final_amount'))['final_amount__sum'] or 0
        context['avg_rental_duration'] = rentals.aggregate(Avg('days'))['days__avg'] or 0
        
        # Car statistics
        cars = Car.objects.all()
        context['total_cars'] = cars.count()
        context['available_cars'] = cars.filter(is_available=True).count()
        
        # Most popular car types
        popular_car_types = (
            CarType.objects.annotate(rental_count=Count('carmodel__car__rental'))
            .order_by('-rental_count')
        )
        context['popular_car_types'] = popular_car_types
        
        # Client statistics
        clients = Client.objects.all()
        context['total_clients'] = clients.count()
        context['avg_client_rentals'] = (
            rentals.count() / clients.count() if clients.count() > 0 else 0
        )
        
        # Generate charts
        context['car_type_chart'] = self.generate_car_type_chart(popular_car_types)
        context['availability_chart'] = self.generate_availability_chart(
            context['available_cars'], context['total_cars']
        )
        
        # Calculate percentages for CSS bars
        context['avg_duration_percent'] = min(100, max(0, (context['avg_rental_duration'] or 0) / 30 * 100))
        context['avg_client_rentals_percent'] = min(100, max(0, (context['avg_client_rentals'] or 0) / 10 * 100))
        
        # Calculate percentages for car type popularity bars
        if popular_car_types and popular_car_types[0].rental_count > 0:
            for car_type in popular_car_types:
                car_type.percentage = (car_type.rental_count / popular_car_types[0].rental_count) * 100
        else:
            for car_type in popular_car_types:
                car_type.percentage = 0
        
        return context

class ChangePasswordView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'main/profile.html'  # We'll handle this in the same template
    success_url = reverse_lazy('main:profile')

    def form_valid(self, form):
        messages.success(self.request, 'Your password was successfully updated!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return redirect('main:profile')

class DeleteAccountView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        password = request.POST.get('password')
        user = request.user

        if user.check_password(password):
            user.delete()
            messages.success(request, 'Your account has been successfully deleted.')
            return redirect('main:home')
        else:
            messages.error(request, 'Invalid password. Please try again.')
            return redirect('main:profile')

@login_required
@user_passes_test(lambda u: u.is_staff or (hasattr(u, 'employee') and u.employee))
def complete_rental(request, pk):
    rental = get_object_or_404(Rental, pk=pk)
    
    if request.method == 'POST':
        if rental.status == 'active':
            form = RentalCompleteForm(request.POST, instance=rental)
            if form.is_valid():
                rental = form.save(commit=False)
                rental.status = 'completed'
                rental.actual_return_date = timezone.now()
                rental.car.is_available = True
                rental.car.save()
                rental.save()
                form.save_m2m()  # Save penalties (ManyToMany field)
                rental.update_final_amount()  # Update final amount with penalties
                messages.success(request, 'Аренда успешно завершена.')
                return redirect('main:rental_detail', pk=pk)
        else:
            messages.error(request, 'Эта аренда не может быть завершена, так как она не активна.')
    else:
        form = RentalCompleteForm(instance=rental)
    
    context = {
        'form': form,
        'rental': rental,
        'base_amount': rental.base_amount,
        'discount_amount': rental.calculate_discount_amount(),
        'penalty_amount': rental.calculate_penalty_amount(),
        'final_amount': rental.calculate_final_amount(),
    }
    return render(request, 'main/rental_complete.html', context)

@login_required
def cancel_rental(request, pk):
    rental = get_object_or_404(Rental, pk=pk)
    
    if request.method == 'POST':
        if rental.status == 'active':
            if request.user.is_staff or (hasattr(request.user, 'employee') and request.user.employee):
                form = RentalCompleteForm(request.POST, instance=rental)
                if form.is_valid():
                    rental = form.save(commit=False)
                    rental.status = 'cancelled'
                    rental.actual_return_date = timezone.now()
                    rental.car.is_available = True
                    rental.car.save()
                    rental.save()
                    form.save_m2m()  # Save penalties (ManyToMany field)
                    rental.update_final_amount()  # Update final amount with penalties
                    messages.success(request, 'Аренда успешно отменена.')
                    return redirect('main:rental_detail', pk=pk)
            else:
                # For regular clients - simple cancellation without penalties
                rental.status = 'cancelled'
                rental.actual_return_date = timezone.now()
                rental.car.is_available = True
                rental.car.save()
                rental.save()
                messages.success(request, 'Аренда отменена.')
        else:
            messages.error(request, 'Эта аренда не может быть отменена, так как она не активна.')
    else:
        form = RentalCompleteForm(instance=rental)
    
    context = {
        'form': form,
        'rental': rental,
        'base_amount': rental.base_amount,
        'discount_amount': rental.calculate_discount_amount(),
        'penalty_amount': rental.calculate_penalty_amount(),
        'final_amount': rental.calculate_final_amount(),
    }
    return render(request, 'main/rental_cancel.html', context)

class EmployeeRegisterView(CreateView):
    template_name = 'main/employee_register.html'
    form_class = EmployeeRegistrationForm
    success_url = reverse_lazy('main:login')

    def form_valid(self, form):
        try:
            with transaction.atomic():
                user = form.save(commit=False)
                user.save()
                
                # Create employee profile
                Employee.objects.create(
                    user=user,
                    position=form.cleaned_data['position'],
                    phone=form.cleaned_data['phone'],
                    email=form.cleaned_data['email'],
                    birth_date=form.cleaned_data['birth_date'],
                    photo=form.cleaned_data.get('photo')
                )
                
                # Add user to Employee group
                employee_group, created = Group.objects.get_or_create(name='Employee')
                user.groups.add(employee_group)
                
                messages.success(self.request, 'Employee account created successfully!')
                return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Error creating employee account: {str(e)}')
            return self.form_invalid(form)

class EmployeeDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'main/employee_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff or (hasattr(self.request.user, 'employee') and self.request.user.employee)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.request.user.employee
        
        # Get active rentals
        context['active_rentals'] = Rental.objects.filter(status='active').order_by('-start_date')
        
        # Get recent clients
        context['recent_clients'] = Client.objects.order_by('-user__date_joined')[:10]
        
        # Get statistics
        context['total_rentals'] = Rental.objects.count()
        context['active_rentals_count'] = Rental.objects.filter(status='active').count()
        context['total_revenue'] = Rental.objects.aggregate(Sum('final_amount'))['final_amount__sum'] or 0
        
        return context

class EmployeeRentalListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Rental
    template_name = 'main/employee_rental_list.html'
    context_object_name = 'rentals'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff or (hasattr(self.request.user, 'employee') and self.request.user.employee)
    
    def get_queryset(self):
        queryset = Rental.objects.all()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-start_date')

class EmployeeClientListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Client
    template_name = 'main/employee_client_list.html'
    context_object_name = 'clients'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff or (hasattr(self.request.user, 'employee') and self.request.user.employee)
    
    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        if search_query:
            return Client.objects.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
        return Client.objects.all().order_by('-user__date_joined')

class EmployeeClientDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Client
    template_name = 'main/employee_client_detail.html'
    context_object_name = 'client'
    
    def test_func(self):
        return self.request.user.is_staff or (hasattr(self.request.user, 'employee') and self.request.user.employee)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.get_object()
        context['rentals'] = Rental.objects.filter(client=client).order_by('-start_date')
        return context

class EmployeeRentalUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Rental
    template_name = 'main/employee_rental_form.html'
    fields = ['status', 'actual_return_date', 'penalties']
    success_url = reverse_lazy('main:employee_rentals')
    
    def test_func(self):
        return self.request.user.is_staff or (hasattr(self.request.user, 'employee') and self.request.user.employee)
    
    def form_valid(self, form):
        rental = form.save(commit=False)
        if rental.status == 'completed' and not rental.actual_return_date:
            rental.actual_return_date = timezone.now()
        
        # Recalculate final amount with penalties
        rental.final_amount = rental.base_amount
        if rental.penalties.exists():
            penalty_sum = sum(penalty.amount for penalty in rental.penalties.all())
            rental.final_amount += penalty_sum
        
        rental.save()
        form.save_m2m()  # Save many-to-many relationships
        messages.success(self.request, 'Rental updated successfully!')
        return super().form_valid(form)

@login_required
@user_passes_test(lambda u: u.is_staff or (hasattr(u, 'employee') and u.employee))
def employee_rental_create(request):
    if request.method == 'POST':
        form = RentalForm(request.POST)
        client_id = request.POST.get('client')
        try:
            client = Client.objects.get(id=client_id)
            if form.is_valid():
                rental = form.save(commit=False)
                rental.client = client
                rental.start_date = timezone.now()
                rental.expected_return_date = rental.start_date + timezone.timedelta(days=rental.days)
                rental.base_amount = rental.car.daily_rate * rental.days
                rental.final_amount = rental.base_amount
                rental.status = 'active'
                rental.save()
                messages.success(request, 'Rental created successfully!')
                return redirect('main:employee_rentals')
        except Client.DoesNotExist:
            messages.error(request, 'Client not found!')
    else:
        form = RentalForm()
    
    return render(request, 'main/employee_rental_create.html', {
        'form': form,
        'clients': Client.objects.all()
    })

@login_required
@user_passes_test(lambda u: u.is_staff or (hasattr(u, 'employee') and u.employee))
def employee_client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            
            # Create user account for client
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = User.objects.make_random_password()
            
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=request.POST.get('first_name'),
                    last_name=request.POST.get('last_name')
                )
                client.user = user
                client.save()
                
                # TODO: Send email to client with their credentials
                
                messages.success(request, 'Client created successfully!')
                return redirect('main:employee_clients')
            except Exception as e:
                messages.error(request, f'Error creating client: {str(e)}')
    else:
        form = ClientForm()
    
    return render(request, 'main/employee_client_create.html', {'form': form})

@login_required
def debug_user_info(request):
    context = {
        'username': request.user.username,
        'is_staff': request.user.is_staff,
        'is_superuser': request.user.is_superuser,
        'is_authenticated': request.user.is_authenticated,
        'has_employee': hasattr(request.user, 'employee'),
        'groups': [group.name for group in request.user.groups.all()],
    }
    return render(request, 'main/debug_user_info.html', context)
