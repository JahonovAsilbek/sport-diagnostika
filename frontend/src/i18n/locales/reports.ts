// Reports view — the request form (type/format/scope filters) and the status table. Report TYPE and
// STATUS enum labels live in enums.ts (via @/i18n/labels helpers); formats (PDF/Word/Excel) stay
// proper nouns in @/api/reports. Scope-filter field labels reuse common.fields.*. kk omitted →
// falls back to uz.
export default {
  uz: {
    subtitle: 'Hisobot soʻrang va tayyor boʻlganda yuklab oling',
    type: 'Turi',
    format: 'Format',
    request: 'Soʻrash',
    params: 'Parametrlar',
    empty: 'Hali hisobot soʻralmagan.',
    selectAthlete: 'Sportchi tanlang',
    requestAccepted: 'Soʻrov qabul qilindi',
    downloadFailed: 'Yuklab boʻlmadi',
    athleteRef: 'Sportchi #{id}',
  },
  ru: {
    subtitle: 'Запросите отчёт и скачайте его, когда он будет готов',
    type: 'Тип',
    format: 'Формат',
    request: 'Запросить',
    params: 'Параметры',
    empty: 'Отчёты ещё не запрашивались.',
    selectAthlete: 'Выберите спортсмена',
    requestAccepted: 'Запрос принят',
    downloadFailed: 'Не удалось скачать',
    athleteRef: 'Спортсмен #{id}',
  },
  en: {
    subtitle: 'Request a report and download it when ready',
    type: 'Type',
    format: 'Format',
    request: 'Request',
    params: 'Parameters',
    empty: 'No reports requested yet.',
    selectAthlete: 'Select an athlete',
    requestAccepted: 'Request accepted',
    downloadFailed: 'Download failed',
    athleteRef: 'Athlete #{id}',
  },
}
