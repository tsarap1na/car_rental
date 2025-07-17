from django.contrib import admin
from .models import (
    CarType, CarModel, Car, CarPark, Client, Discount, Penalty,
    Rental, Article, CompanyInfo, FAQ, Employee, JobVacancy,
    Review, Promo
)

@admin.register(CarType)
class CarTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'manufacturer', 'car_type')
    list_filter = ('manufacturer', 'car_type')
    search_fields = ('name', 'manufacturer')

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'model', 'year', 'daily_rate', 'is_available')
    list_filter = ('is_available', 'year', 'model__manufacturer')
    search_fields = ('license_plate', 'model__name')

@admin.register(CarPark)
class CarParkAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    filter_horizontal = ('cars',)
    search_fields = ('name', 'address')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'birth_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')
    list_filter = ('birth_date',)

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'percentage')
    search_fields = ('name',)

@admin.register(Penalty)
class PenaltyAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount')
    search_fields = ('name',)

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'car', 'start_date', 'expected_return_date', 'status']
    list_filter = ['status']
    search_fields = ['client__user__username', 'car__license_plate']

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question',)
    search_fields = ('question', 'answer')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'phone', 'email')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'position')
    list_filter = ('position',)

@admin.register(JobVacancy)
class JobVacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
    search_fields = ('title', 'description')
    list_filter = ('is_active',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('client', 'rating', 'created_at')
    search_fields = ('client__user__username', 'text')
    list_filter = ('rating', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(Promo)
class PromoAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'valid_from', 'valid_until', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'description']
