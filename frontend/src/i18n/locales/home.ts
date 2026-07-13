// Dashboard / home view chrome. Per-role scope subtitles keyed by role value. kk omitted → falls
// back to uz.
export default {
  uz: {
    welcome: 'Xush kelibsiz, {name}',
    scope: {
      super_admin: 'Tizim koʻrsatkichlari',
      region_admin: 'Viloyat koʻrsatkichlari',
      coach: 'Sizning sportchilaringiz',
      lab_operator: 'Laboratoriya koʻrsatkichlari',
      ministry: 'Respublika koʻrsatkichlari',
    },
    kpi: {
      activeAthletes: 'Faol sportchilar',
      recentSessions: 'Soʻnggi 30 kun sessiyalari',
      regions: 'Viloyatlar',
    },
    orgBreakdown: 'Tashkilot turi boʻyicha',
    charts: {
      darajaDistribution: 'Daraja taqsimoti',
      byRegion: 'Viloyatlar boʻyicha (I daraja)',
    },
    quickLinksTitle: 'Tezkor havolalar',
  },
  ru: {
    welcome: 'Добро пожаловать, {name}',
    scope: {
      super_admin: 'Показатели системы',
      region_admin: 'Показатели области',
      coach: 'Ваши спортсмены',
      lab_operator: 'Показатели лаборатории',
      ministry: 'Показатели республики',
    },
    kpi: {
      activeAthletes: 'Активные спортсмены',
      recentSessions: 'Сессии за последние 30 дней',
      regions: 'Области',
    },
    orgBreakdown: 'По типу организации',
    charts: {
      darajaDistribution: 'Распределение по разрядам',
      byRegion: 'По областям (I разряд)',
    },
    quickLinksTitle: 'Быстрые ссылки',
  },
  en: {
    welcome: 'Welcome, {name}',
    scope: {
      super_admin: 'System metrics',
      region_admin: 'Region metrics',
      coach: 'Your athletes',
      lab_operator: 'Laboratory metrics',
      ministry: 'Republic metrics',
    },
    kpi: {
      activeAthletes: 'Active athletes',
      recentSessions: 'Sessions in the last 30 days',
      regions: 'Regions',
    },
    orgBreakdown: 'By organization type',
    charts: {
      darajaDistribution: 'Level distribution',
      byRegion: 'By region (Level I)',
    },
    quickLinksTitle: 'Quick links',
  },
}
