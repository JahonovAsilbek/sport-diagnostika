import factory

from apps.recommendations.models import Recommendation, RecommendationRule
from apps.scoring.factories import EvaluationFactory


class RecommendationRuleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RecommendationRule

    exercise = None  # a total rule (physical_total) by default
    comparator = RecommendationRule.Comparator.LT
    threshold = 30
    template_text = "Umumiy jismoniy tayyorgarlikni oshirish tavsiya etiladi."
    is_active = True


class RecommendationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Recommendation

    evaluation = factory.SubFactory(EvaluationFactory)
    rule = factory.SubFactory(RecommendationRuleFactory)
    text = factory.SelfAttribute("rule.template_text")
