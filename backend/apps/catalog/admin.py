from django.contrib import admin
from django.forms.models import BaseInlineFormSet

from apps.catalog.models import (
    AgeCategory,
    BatteryItem,
    DarajaThreshold,
    District,
    Exercise,
    Norm,
    NormBand,
    Organization,
    Region,
    SportType,
    TestBattery,
)
from apps.catalog.validators import assert_bands_no_overlap


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


class NormBandInlineFormSet(BaseInlineFormSet):
    """Reject a norm whose submitted bands overlap — surfaced as an inline form error."""

    def clean(self):
        super().clean()
        bands = []
        for form in self.forms:
            cleaned = getattr(form, "cleaned_data", None)
            if not cleaned or cleaned.get("DELETE"):
                continue
            lower, upper = cleaned.get("lower_bound"), cleaned.get("upper_bound")
            if lower is None or upper is None:
                continue
            bands.append({"lower_bound": lower, "upper_bound": upper})
        assert_bands_no_overlap(bands)


class NormBandInline(admin.TabularInline):
    model = NormBand
    formset = NormBandInlineFormSet
    extra = 0
    ordering = ("-points",)


@admin.register(Norm)
class NormAdmin(admin.ModelAdmin):
    list_display = ("exercise", "gender", "age_min", "age_max", "valid_from", "is_active")
    list_filter = ("exercise", "gender", "is_active")
    inlines = [NormBandInline]


@admin.register(DarajaThreshold)
class DarajaThresholdAdmin(admin.ModelAdmin):
    list_display = ("level", "total_min", "total_max")
