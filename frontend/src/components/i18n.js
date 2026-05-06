import React, { useState, useEffect } from 'react';

/**
 * Internationalization (i18n) module
 * Supports Hindi, Bengali, Telugu, Odia, and English
 */

const translations = {
  en: {
    // Navigation
    dashboard: '📊 Dashboard',
    detection: '🔬 Image Detection',
    prediction: '🧠 Risk Prediction',
    alerts: '🚨 Alerts',
    heatmap: '🗺️ Heatmap',
    data_entry: '📝 Data Entry',
    resources: '📦 Resources',
    
    // Data Entry Form
    report_symptoms: 'Report Symptoms',
    patient_name: 'Patient Name',
    patient_age: 'Age',
    patient_gender: 'Gender',
    male: 'Male',
    female: 'Female',
    other: 'Other',
    village: 'Village',
    district: 'District',
    symptoms: 'Symptoms',
    severity: 'Severity',
    mild: 'Mild',
    moderate: 'Moderate',
    severe: 'Severe',
    critical: 'Critical',
    water_source: 'Water Source',
    suspected_disease: 'Suspected Disease',
    onset_date: 'Symptom Onset Date',
    notes: 'Additional Notes',
    submit: 'Submit Report',
    submitting: 'Submitting...',
    success: 'Report submitted successfully!',
    
    // Symptoms checklist
    fever: 'Fever',
    diarrhea: 'Diarrhea',
    vomiting: 'Vomiting',
    abdominal_pain: 'Abdominal Pain',
    dehydration: 'Dehydration',
    blood_in_stool: 'Blood in Stool',
    skin_rash: 'Skin Rash',
    jaundice: 'Jaundice',
    
    // Diseases
    cholera: 'Cholera',
    typhoid: 'Typhoid',
    diarrheal: 'Diarrheal Disease',
    hepatitis_a: 'Hepatitis A',
    leptospirosis: 'Leptospirosis',
    dysentery: 'Dysentery',
    
    // Dashboard
    total_patients: 'Total Patients',
    reports_today: 'Reports Today',
    active_alerts: 'Active Alerts',
    water_quality: 'Water Quality',
    
    // Resources
    medical_team: 'Medical Team',
    ors_packets: 'ORS Packets',
    water_purifier: 'Water Purifier',
    chlorine_tablets: 'Chlorine Tablets',
    iv_fluids: 'IV Fluids',
    ambulance: 'Ambulance',
    testing_kit: 'Testing Kit',
    
    // General
    loading: 'Loading...',
    error: 'Error',
    save_offline: 'Save Offline',
    sync_data: 'Sync Data',
    offline_mode: 'Offline Mode',
    language: 'Language',
    data_collection: 'Health Data Collection',
    reporter_info: 'Reporter Information',
    reporter_type: 'Reporter Type',
    asha_worker: 'ASHA Worker',
    clinic: 'Clinic',
    volunteer: 'Volunteer',
    self_report: 'Self Report',
    patient_details: 'Patient Details',
    additional_symptoms: 'Additional Symptoms',
    sms_fallback: 'SMS Fallback',
  },
  
  hi: {
    dashboard: '📊 डैशबोर्ड',
    detection: '🔬 छवि जांच',
    prediction: '🧠 जोखिम भविष्यवाणी',
    alerts: '🚨 चेतावनी',
    heatmap: '🗺️ हीटमैप',
    data_entry: '📝 डेटा प्रविष्टि',
    resources: '📦 संसाधन',
    report_symptoms: 'लक्षण रिपोर्ट करें',
    patient_name: 'रोगी का नाम',
    patient_age: 'उम्र',
    patient_gender: 'लिंग',
    male: 'पुरुष',
    female: 'महिला',
    other: 'अन्य',
    village: 'गाँव',
    district: 'जिला',
    symptoms: 'लक्षण',
    severity: 'गंभीरता',
    mild: 'हल्का',
    moderate: 'मध्यम',
    severe: 'गंभीर',
    critical: 'अत्यंत गंभीर',
    water_source: 'जल स्रोत',
    suspected_disease: 'संदिग्ध बीमारी',
    onset_date: 'लक्षण शुरू होने की तारीख',
    notes: 'अतिरिक्त नोट्स',
    submit: 'रिपोर्ट जमा करें',
    submitting: 'जमा हो रहा है...',
    success: 'रिपोर्ट सफलतापूर्वक जमा हो गई!',
    fever: 'बुखार',
    diarrhea: 'दस्त',
    vomiting: 'उल्टी',
    abdominal_pain: 'पेट दर्द',
    dehydration: 'निर्जलीकरण',
    blood_in_stool: 'मल में खून',
    skin_rash: 'त्वचा पर चकत्ते',
    jaundice: 'पीलिया',
    cholera: 'हैजा',
    typhoid: 'टाइफाइड',
    diarrheal: 'दस्त रोग',
    hepatitis_a: 'हेपेटाइटिस ए',
    leptospirosis: 'लेप्टोस्पायरोसिस',
    dysentery: 'पेचिश',
    total_patients: 'कुल रोगी',
    reports_today: 'आज की रिपोर्ट',
    active_alerts: 'सक्रिय चेतावनियां',
    water_quality: 'जल गुणवत्ता',
    medical_team: 'चिकित्सा दल',
    ors_packets: 'ओआरएस पैकेट',
    water_purifier: 'जल शोधक',
    chlorine_tablets: 'क्लोरीन गोलियां',
    iv_fluids: 'IV तरल पदार्थ',
    ambulance: 'एम्बुलेंस',
    testing_kit: 'परीक्षण किट',
    loading: 'लोड हो रहा है...',
    error: 'त्रुटि',
    save_offline: 'ऑफलाइन सेव करें',
    sync_data: 'डेटा सिंक करें',
    offline_mode: 'ऑफलाइन मोड',
    language: 'भाषा',
    data_collection: 'स्वास्थ्य डेटा संग्रह',
    reporter_info: 'रिपोर्टर जानकारी',
    reporter_type: 'रिपोर्टर प्रकार',
    asha_worker: 'आशा कार्यकर्ता',
    clinic: 'क्लिनिक',
    volunteer: 'स्वयंसेवक',
    self_report: 'स्वयं',
    patient_details: 'रोगी विवरण',
    additional_symptoms: 'अतिरिक्त लक्षण',
    sms_fallback: 'एसएमएस फ़ॉलबैक',
  },
  
  bn: {
    dashboard: '📊 ড্যাশবোর্ড',
    detection: '🔬 ছবি সনাক্তকরণ',
    prediction: '🧠 ঝুঁকি পূর্বাভাস',
    alerts: '🚨 সতর্কতা',
    heatmap: '🗺️ হিটম্যাপ',
    data_entry: '📝 ডেটা এন্ট্রি',
    resources: '📦 সম্পদ',
    report_symptoms: 'উপসর্গ রিপোর্ট করুন',
    patient_name: 'রোগীর নাম',
    patient_age: 'বয়স',
    patient_gender: 'লিঙ্গ',
    male: 'পুরুষ',
    female: 'মহিলা',
    other: 'অন্যান্য',
    village: 'গ্রাম',
    district: 'জেলা',
    symptoms: 'উপসর্গ',
    severity: 'তীব্রতা',
    mild: 'হালকা',
    moderate: 'মাঝারি',
    severe: 'গুরুতর',
    critical: 'জটিল',
    water_source: 'জলের উৎস',
    suspected_disease: 'সন্দেহজনক রোগ',
    onset_date: 'উপসর্গ শুরুর তারিখ',
    notes: 'অতিরিক্ত নোট',
    submit: 'রিপোর্ট জমা দিন',
    submitting: 'জমা দেওয়া হচ্ছে...',
    success: 'রিপোর্ট সফলভাবে জমা দেওয়া হয়েছে!',
    fever: 'জ্বর',
    diarrhea: 'ডায়রিয়া',
    vomiting: 'বমি',
    abdominal_pain: 'পেটে ব্যথা',
    dehydration: 'পানিশূন্যতা',
    blood_in_stool: 'মলে রক্ত',
    skin_rash: 'ত্বকে ফুসকুড়ি',
    jaundice: 'জন্ডিস',
    cholera: 'কলেরা',
    typhoid: 'টাইফয়েড',
    diarrheal: 'ডায়রিয়াজনিত রোগ',
    hepatitis_a: 'হেপাটাইটিস এ',
    loading: 'লোড হচ্ছে...',
    language: 'ভাষা',
  },
  
  te: {
    dashboard: '📊 డ్యాష్‌బోర్డ్',
    detection: '🔬 చిత్ర గుర్తింపు',
    prediction: '🧠 ప్రమాద అంచనా',
    alerts: '🚨 హెచ్చరికలు',
    heatmap: '🗺️ హీట్‌మ్యాప్',
    data_entry: '📝 డేటా ఎంట్రీ',
    resources: '📦 వనరులు',
    report_symptoms: 'లక్షణాలను నివేదించండి',
    patient_name: 'రోగి పేరు',
    patient_age: 'వయస్సు',
    village: 'గ్రామం',
    district: 'జిల్లా',
    symptoms: 'లక్షణాలు',
    severity: 'తీవ్రత',
    submit: 'నివేదిక సమర్పించండి',
    fever: 'జ్వరం',
    diarrhea: 'అతిసారం',
    vomiting: 'వాంతి',
    cholera: 'కలరా',
    typhoid: 'టైఫాయిడ్',
    loading: 'లోడ్ అవుతోంది...',
    language: 'భాష',
  },
  
  or: {
    dashboard: '📊 ଡ୍ୟାସବୋର୍ଡ',
    detection: '🔬 ଚିତ୍ର ଚିହ୍ନଟ',
    prediction: '🧠 ବିପଦ ଆକଳନ',
    alerts: '🚨 ସତର୍କତା',
    heatmap: '🗺️ ହିଟମ୍ୟାପ',
    data_entry: '📝 ତଥ୍ୟ ପ୍ରବେଶ',
    resources: '📦 ସମ୍ପଦ',
    report_symptoms: 'ଲକ୍ଷଣ ରିପୋର୍ଟ କରନ୍ତୁ',
    patient_name: 'ରୋଗୀଙ୍କ ନାମ',
    village: 'ଗ୍ରାମ',
    district: 'ଜିଲ୍ଲା',
    symptoms: 'ଲକ୍ଷଣ',
    severity: 'ଗମ୍ଭୀରତା',
    submit: 'ରିପୋର୍ଟ ଦାଖଲ',
    fever: 'ଜ୍ୱର',
    diarrhea: 'ଡାଇରିଆ',
    vomiting: 'ବାନ୍ତି',
    cholera: 'କଲେରା',
    typhoid: 'ଟାଇଫଏଡ',
    loading: 'ଲୋଡ ହେଉଛି...',
    language: 'ଭାଷା',
  },
};

const langNames = {
  en: 'English',
  hi: 'हिन्दी',
  bn: 'বাংলা',
  te: 'తెలుగు',
  or: 'ଓଡ଼ିଆ',
};

// i18n context
const I18nContext = React.createContext();

export const I18nProvider = ({ children }) => {
  const [lang, setLang] = useState(() => {
    return localStorage.getItem('aquaguard_lang') || 'en';
  });

  useEffect(() => {
    localStorage.setItem('aquaguard_lang', lang);
  }, [lang]);

  const t = (key, defaultText) => {
    return translations[lang]?.[key] || translations.en?.[key] || defaultText || key;
  };

  return (
    <I18nContext.Provider value={{ lang, setLang, t, langNames, translations }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = () => React.useContext(I18nContext);

/**
 * Language Selector Component
 */
export const LanguageSelector = () => {
  const { lang, setLang, langNames } = useI18n();

  return (
    <select
      value={lang}
      onChange={(e) => setLang(e.target.value)}
      style={{
        background: 'var(--bg-input)',
        color: 'var(--text-primary)',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-sm)',
        padding: '6px 12px',
        fontSize: '0.8rem',
        fontFamily: 'var(--font-primary)',
        cursor: 'pointer',
      }}
      id="language-selector"
    >
      {Object.entries(langNames).map(([code, name]) => (
        <option key={code} value={code}>{name}</option>
      ))}
    </select>
  );
};

export default translations;
