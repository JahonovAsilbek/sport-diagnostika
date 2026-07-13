// Rating view — the top-athletes / full-ranking / region tabs and their tables. Field labels shared
// with filters (region, sport…) come from the `common` namespace. kk omitted → falls back to uz.
export default {
  uz: {
    title: 'Reyting',
    subtitle: 'Eng kuchli sportchilar va viloyatlar reytingi',
    tabs: {
      top: 'Top sportchilar',
      full: 'Toʻliq reyting',
      regions: 'Viloyatlar',
    },
    columns: {
      rank: 'Oʻrin',
      fullName: 'F.I.O',
      score: 'Ball',
      daraja: 'Daraja',
      avgScore: 'Oʻrtacha ball',
    },
    emptyAthletes: 'Baholangan sportchi topilmadi.',
    emptyFiltered: 'Ushbu filtr uchun baholangan sportchi topilmadi.',
  },
  ru: {
    title: 'Рейтинг',
    subtitle: 'Рейтинг сильнейших спортсменов и областей',
    tabs: {
      top: 'Топ спортсмены',
      full: 'Полный рейтинг',
      regions: 'Области',
    },
    columns: {
      rank: 'Место',
      fullName: 'Ф.И.О',
      score: 'Балл',
      daraja: 'Разряд',
      avgScore: 'Средний балл',
    },
    emptyAthletes: 'Оценённых спортсменов не найдено.',
    emptyFiltered: 'Для этого фильтра оценённых спортсменов не найдено.',
  },
  en: {
    title: 'Rating',
    subtitle: 'Ranking of the strongest athletes and regions',
    tabs: {
      top: 'Top athletes',
      full: 'Full ranking',
      regions: 'Regions',
    },
    columns: {
      rank: 'Rank',
      fullName: 'Full name',
      score: 'Score',
      daraja: 'Level',
      avgScore: 'Average score',
    },
    emptyAthletes: 'No evaluated athletes found.',
    emptyFiltered: 'No evaluated athletes found for this filter.',
  },
}
