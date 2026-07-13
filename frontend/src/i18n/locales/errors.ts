// Error / placeholder view chrome (403, 404, stub sections). kk omitted → falls back to uz.
export default {
  uz: {
    forbidden: { message: 'Ushbu boʻlimga kirish uchun ruxsatingiz yoʻq.' },
    notFound: { message: 'Sahifa topilmadi.' },
    placeholder: {
      title: 'Boʻlim',
      subtitle: 'Ushbu boʻlim keyingi bloklarda toʻldiriladi.',
    },
  },
  ru: {
    forbidden: { message: 'У вас нет прав для доступа к этому разделу.' },
    notFound: { message: 'Страница не найдена.' },
    placeholder: {
      title: 'Раздел',
      subtitle: 'Этот раздел будет заполнен в следующих блоках.',
    },
  },
  en: {
    forbidden: { message: 'You do not have permission to access this section.' },
    notFound: { message: 'Page not found.' },
    placeholder: {
      title: 'Section',
      subtitle: 'This section will be added in later blocks.',
    },
  },
}
