from django.contrib import admin

from apps.catalog.models import (
    AgeCategory,
    BatteryItem,
    District,
    Exercise,
    Organization,
    Region,
    SportType,
    TestBattery,
)


class DistrictInline(admin.TabularInline):
    model = District
    extra = 0


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")
    inlines = [DistrictInline]


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "region")
    list_filter = ("region",)
    search_fields = ("name",)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "region", "district")
    list_filter = ("type", "region")
    search_fields = ("name",)


@admin.register(SportType)
class SportTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(AgeCategory)
class AgeCategoryAdmin(admin.ModelAdmin):
    list_display = ("ordinal", "name", "age_min", "age_max")


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "value_type", "direction", "order", "is_active")
    list_filter = ("value_type", "direction", "is_active")
    search_fields = ("name",)


class BatteryItemInline(admin.TabularInline):
    model = BatteryItem
    extra = 0
    # The battery is the ordered 5-exercise selection per (age_category, gender).
    ordering = ("order",)


@admin.register(TestBattery)
class TestBatteryAdmin(admin.ModelAdmin):
    list_display = ("age_category", "gender", "is_active")
    list_filter = ("age_category", "gender", "is_active")
    inlines = [BatteryItemInline]
