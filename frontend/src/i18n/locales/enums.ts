// Backend English enum values → localized labels. Consumed via the helpers in src/i18n/labels.ts.
// OTM/OPSTTM are acronyms and report formats are proper nouns → identical across locales (kept as
// constants, not here). periodType is reserved for FRNTND-26. kk omitted → falls back to uz.
export default {
  uz: {
    role: {
      super_admin: 'Super admin',
      region_admin: 'Viloyat admin',
      coach: 'Murabbiy',
      lab_operator: 'Laboratoriya operatori',
      ministry: 'Vazirlik vakili',
    },
    daraja: {
      I: 'I daraja',
      II: 'II daraja',
      III: 'III daraja',
      none: 'Nishonsiz',
      notEvaluated: 'Baholanmagan',
    },
    gender: { male: 'Erkak', female: 'Ayol' },
    orgType: { OTM: 'OTM', OPSTTM: 'OPSTTM' },
    valueType: {
      seconds: 'Soniya',
      minsec: 'Daqiqa:soniya',
      count: 'Son',
      cm_signed: 'Santimetr (ishorali)',
    },
    direction: { higher: 'Koʻproq — yaxshiroq', lower_is_better: 'Kamroq — yaxshiroq' },
    reportType: { athlete: 'Sportchi', region: 'Viloyat', sport: 'Sport turi', republic: 'Respublika' },
    reportStatus: { pending: 'Navbatda', processing: 'Ishlanmoqda', done: 'Tayyor', failed: 'Xato' },
    periodType: { quarter: 'Chorak', half: 'Yarim yil', year: 'Yil' },
  },
  ru: {
    role: {
      super_admin: 'Супер-админ',
      region_admin: 'Админ области',
      coach: 'Тренер',
      lab_operator: 'Оператор лаборатории',
      ministry: 'Представитель министерства',
    },
    daraja: {
      I: 'I разряд',
      II: 'II разряд',
      III: 'III разряд',
      none: 'Без разряда',
      notEvaluated: 'Не оценён',
    },
    gender: { male: 'Мужской', female: 'Женский' },
    orgType: { OTM: 'OTM', OPSTTM: 'OPSTTM' },
    valueType: {
      seconds: 'Секунды',
      minsec: 'Минуты:секунды',
      count: 'Количество',
      cm_signed: 'Сантиметры (со знаком)',
    },
    direction: { higher: 'Больше — лучше', lower_is_better: 'Меньше — лучше' },
    reportType: { athlete: 'Спортсмен', region: 'Область', sport: 'Вид спорта', republic: 'Республика' },
    reportStatus: { pending: 'В очереди', processing: 'Обрабатывается', done: 'Готово', failed: 'Ошибка' },
    periodType: { quarter: 'Квартал', half: 'Полугодие', year: 'Год' },
  },
  en: {
    role: {
      super_admin: 'Super admin',
      region_admin: 'Region admin',
      coach: 'Coach',
      lab_operator: 'Lab operator',
      ministry: 'Ministry representative',
    },
    daraja: {
      I: 'Level I',
      II: 'Level II',
      III: 'Level III',
      none: 'No level',
      notEvaluated: 'Not evaluated',
    },
    gender: { male: 'Male', female: 'Female' },
    orgType: { OTM: 'OTM', OPSTTM: 'OPSTTM' },
    valueType: {
      seconds: 'Seconds',
      minsec: 'Minutes:seconds',
      count: 'Count',
      cm_signed: 'Centimeters (signed)',
    },
    direction: { higher: 'Higher is better', lower_is_better: 'Lower is better' },
    reportType: { athlete: 'Athlete', region: 'Region', sport: 'Sport', republic: 'Republic' },
    reportStatus: { pending: 'Queued', processing: 'Processing', done: 'Ready', failed: 'Failed' },
    periodType: { quarter: 'Quarter', half: 'Half-year', year: 'Year' },
  },
}
