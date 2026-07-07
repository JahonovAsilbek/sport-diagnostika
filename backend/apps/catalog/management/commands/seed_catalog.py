from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import AgeCategory, District, Region, SportType

# (code, name) — codes are stable ASCII keys for idempotent get_or_create; the display
# name is the real Uzbek value (proper apostrophes oʻ/gʻ).
REGIONS = [
    ("QR", "Qoraqalpogʻiston Respublikasi"),
    ("AN", "Andijon"),
    ("BU", "Buxoro"),
    ("FA", "Fargʻona"),
    ("JI", "Jizzax"),
    ("XO", "Xorazm"),
    ("NA", "Namangan"),
    ("NV", "Navoiy"),
    ("QA", "Qashqadaryo"),
    ("SA", "Samarqand"),
    ("SI", "Sirdaryo"),
    ("SU", "Surxondaryo"),
    ("TV", "Toshkent viloyati"),
    ("TS", "Toshkent shahri"),
]

# Real tumanlar per region — a representative, extendable subset keyed by region code.
# Idempotent by (region, name), so appending more later never duplicates.
DISTRICTS = {
    "QR": [
        "Nukus", "Amudaryo", "Beruniy", "Chimboy", "Ellikqalʼa", "Kegeyli",
        "Qonlikoʻl", "Qoraoʻzak", "Moʻynoq", "Taxtakoʻpir", "Toʻrtkoʻl",
        "Xoʻjayli", "Shumanay", "Boʻzatov",
    ],
    "AN": [
        "Andijon", "Asaka", "Baliqchi", "Boʻston", "Buloqboshi", "Izboskan",
        "Jalaquduq", "Xoʻjaobod", "Qoʻrgʻontepa", "Marhamat", "Oltinkoʻl",
        "Paxtaobod", "Shahrixon", "Ulugʻnor",
    ],
    "BU": [
        "Buxoro", "Gʻijduvon", "Jondor", "Kogon", "Olot", "Peshku",
        "Qorakoʻl", "Qorovulbozor", "Romitan", "Shofirkon", "Vobkent",
    ],
    "FA": [
        "Fargʻona", "Beshariq", "Bogʻdod", "Buvayda", "Dangʻara", "Furqat",
        "Qoʻshtepa", "Oltiariq", "Rishton", "Soʻx", "Toshloq", "Uchkoʻprik",
        "Yozyovon", "Quva",
    ],
    "JI": [
        "Jizzax", "Arnasoy", "Baxmal", "Doʻstlik", "Forish", "Gʻallaorol",
        "Sharof Rashidov", "Mirzachoʻl", "Paxtakor", "Yangiobod",
        "Zafarobod", "Zarbdor", "Zomin",
    ],
    "XO": [
        "Urganch", "Bogʻot", "Gurlan", "Xazorasp", "Xonqa", "Xiva",
        "Qoʻshkoʻpir", "Shovot", "Yangiariq", "Yangibozor", "Tuproqqalʼa",
    ],
    "NA": [
        "Namangan", "Chortoq", "Chust", "Kosonsoy", "Mingbuloq", "Norin",
        "Pop", "Toʻraqoʻrgʻon", "Uchqoʻrgʻon", "Uychi", "Yangiqoʻrgʻon",
    ],
    "NV": [
        "Navoiy", "Karmana", "Konimex", "Navbahor", "Nurota", "Qiziltepa",
        "Xatirchi", "Tomdi", "Uchquduq",
    ],
    "QA": [
        "Qarshi", "Chiroqchi", "Dehqonobod", "Gʻuzor", "Kasbi", "Kitob",
        "Koson", "Mirishkor", "Muborak", "Nishon", "Qamashi", "Shahrisabz",
        "Yakkabogʻ",
    ],
    "SA": [
        "Samarqand", "Bulungʻur", "Ishtixon", "Jomboy", "Kattaqoʻrgʻon",
        "Qoʻshrabot", "Narpay", "Nurobod", "Oqdaryo", "Pastdargʻom",
        "Paxtachi", "Payariq", "Toyloq", "Urgut",
    ],
    "SI": [
        "Guliston", "Boyovut", "Xovos", "Mirzaobod", "Oqoltin", "Sardoba",
        "Sayxunobod", "Sirdaryo", "Yangiyer",
    ],
    "SU": [
        "Termiz", "Angor", "Bandixon", "Boysun", "Denov", "Jarqoʻrgʻon",
        "Qiziriq", "Qumqoʻrgʻon", "Muzrabot", "Oltinsoy", "Sariosiyo",
        "Sherobod", "Shoʻrchi", "Uzun",
    ],
    "TV": [
        "Bekobod", "Boʻka", "Boʻstonliq", "Chinoz", "Qibray", "Ohangaron",
        "Oqqoʻrgʻon", "Parkent", "Piskent", "Quyichirchiq", "Oʻrtachirchiq",
        "Yangiyoʻl", "Yuqorichirchiq", "Zangiota", "Chirchiq",
    ],
    "TS": [
        "Bektemir", "Chilonzor", "Mirobod", "Mirzo Ulugʻbek", "Sergeli",
        "Olmazor", "Uchtepa", "Yakkasaroy", "Yashnobod", "Yunusobod",
        "Shayxontohur", "Yangihayot",
    ],
}

# TOIFA age categories (ordinal 1–6). The 13–17 band is split 4:13–15 / 5:16–17 as a
# best-effort default — the exact split is an open item (SCORING.md §11), easy to adjust.
AGE_CATEGORIES = [
    (1, "7–8", 7, 8),
    (2, "9–10", 9, 10),
    (3, "11–12", 11, 12),
    (4, "13–15", 13, 15),
    (5, "16–17", 16, 17),
    (6, "18–29", 18, 29),
]

# (code, name) — base sport-type pool; extendable without touching existing rows.
SPORT_TYPES = [
    ("FUT", "Futbol"),
    ("GAN", "Gandbol"),
    ("BAS", "Basketbol"),
    ("VOL", "Voleybol"),
    ("TEN", "Tennis"),
    ("STE", "Stol tennisi"),
    ("BAD", "Badminton"),
    ("YAT", "Yengil atletika"),
    ("SUZ", "Suzish"),
    ("SGI", "Sport gimnastikasi"),
    ("BGI", "Badiiy gimnastika"),
    ("BOK", "Boks"),
    ("KUR", "Kurash"),
    ("BEL", "Belbogʻli kurash"),
    ("DZY", "Dzyudo"),
    ("SAM", "Sambo"),
    ("TKD", "Taekvondo"),
    ("KAR", "Karate"),
    ("OAT", "Ogʻir atletika"),
    ("VEL", "Velosport"),
    ("ESH", "Eshkak eshish"),
    ("SHA", "Shaxmat"),
    ("SHK", "Shashka"),
    ("QIL", "Qilichbozlik"),
    ("KAM", "Kamondan otish"),
    ("MER", "Merganlik"),
    ("XOK", "Xokkey"),
    ("REG", "Regbi"),
    ("TRI", "Triatlon"),
    ("AKR", "Sport akrobatikasi"),
    ("SIN", "Sinxron suzish"),
    ("SVS", "Suvga sakrash"),
]


class Command(BaseCommand):
    help = "Seed geography, TOIFA age categories and sport types (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        regions_created = districts_created = ages_created = sports_created = 0

        region_by_code = {}
        for code, name in REGIONS:
            region, created = Region.objects.get_or_create(code=code, defaults={"name": name})
            region_by_code[code] = region
            regions_created += created

        for code, names in DISTRICTS.items():
            region = region_by_code[code]
            for name in names:
                _, created = District.objects.get_or_create(region=region, name=name)
                districts_created += created

        for ordinal, name, age_min, age_max in AGE_CATEGORIES:
            _, created = AgeCategory.objects.get_or_create(
                ordinal=ordinal,
                defaults={"name": name, "age_min": age_min, "age_max": age_max},
            )
            ages_created += created

        for code, name in SPORT_TYPES:
            _, created = SportType.objects.get_or_create(code=code, defaults={"name": name})
            sports_created += created

        self.stdout.write(
            self.style.SUCCESS(
                f"seed_catalog: +{regions_created} regions, +{districts_created} districts, "
                f"+{ages_created} age categories, +{sports_created} sport types."
            )
        )
