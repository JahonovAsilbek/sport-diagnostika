// Period-selector chrome (FRNTND-26). The type names (Chorak/Yarim yil/Yil) live in
// enums.periodType; this covers the "no period" option + the quarter/half index labels. kk omitted
// → falls back to uz.
export default {
  uz: {
    label: 'Davr',
    all: 'Butun davr',
    quarterN: '{n}-chorak',
    halfN: '{n}-yarim yil',
  },
  ru: {
    label: 'Период',
    all: 'Весь период',
    quarterN: '{n}-й квартал',
    halfN: '{n}-е полугодие',
  },
  en: {
    label: 'Period',
    all: 'All time',
    quarterN: 'Q{n}',
    halfN: 'H{n}',
  },
}
