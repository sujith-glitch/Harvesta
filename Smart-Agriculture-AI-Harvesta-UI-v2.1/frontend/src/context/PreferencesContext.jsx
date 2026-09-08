import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

const STORAGE_KEY = 'harvesta_app_preferences';

export const LANGUAGES = [
  { code: 'en', label: 'English', nativeLabel: 'English', speechLocale: 'en-IN' },
  { code: 'ta', label: 'Tamil', nativeLabel: 'தமிழ்', speechLocale: 'ta-IN' },
  { code: 'hi', label: 'Hindi', nativeLabel: 'हिन्दी', speechLocale: 'hi-IN' },
  { code: 'te', label: 'Telugu', nativeLabel: 'తెలుగు', speechLocale: 'te-IN' },
  { code: 'kn', label: 'Kannada', nativeLabel: 'ಕನ್ನಡ', speechLocale: 'kn-IN' },
  { code: 'ml', label: 'Malayalam', nativeLabel: 'മലയാളം', speechLocale: 'ml-IN' },
];

const DEFAULTS = {
  language: 'en',
  theme: 'light',
  compact_mode: false,
  reduce_motion: false,
  voice_enabled: true,
  voice_auto_speak: true,
};

const en = {
  dashboard: 'Dashboard', fields: 'Fields', diseaseScan: 'Disease Scan', equipment: 'Equipment',
  climate: 'Climate', alerts: 'Alerts', inventory: 'Inventory', reports: 'Reports', help: 'Help',
  settings: 'Settings', adminPortal: 'Admin Portal', farmer: 'Farmer', admin: 'Admin', profile: 'Profile',
  saveChanges: 'Save changes', saving: 'Saving…', saved: 'Saved successfully', cancel: 'Cancel',
  language: 'Language', appearance: 'Appearance', voiceAssistant: 'Voice assistant', preferences: 'Preferences',
  light: 'Light', dark: 'Dark', system: 'System', compactLayout: 'Compact layout', reduceMotion: 'Reduce motion',
  enableVoice: 'Enable voice conversations', autoSpeak: 'Read AI replies aloud', notificationSettings: 'Alert & email settings',
  settingsIntro: 'Choose how Harvesta looks, speaks, and responds. Your choices are saved to your account.',
  askPlaceholder: 'How can I help you?', preparingAnswer: 'Preparing a local answer…',
  voiceListening: 'Listening…', voiceSpeaking: 'Harvesta is speaking…', endVoice: 'End voice chat', startVoice: 'Start live voice chat',
  aiDisclaimer: 'AI screening and guidance are not a confirmed agronomic diagnosis.',
  inventoryTitle: 'Farm Inventory', inventoryIntro: 'Track seeds, fertilizers, tools, equipment, and other farm supplies.',
  addItem: 'Add item', editItem: 'Edit item', itemName: 'Item name', category: 'Category', quantity: 'Quantity',
  unit: 'Unit', threshold: 'Low-stock alert at', supplier: 'Supplier', notes: 'Notes', lowStock: 'Low stock',
  allItems: 'All items', noInventory: 'No inventory items yet. Add your first farm supply.', delete: 'Delete', edit: 'Edit',
  reportsTitle: 'Reports Centre', reportsIntro: 'Open your five private farmer reports and download them as PDF or CSV.',
  viewReport: 'View report', downloadPdf: 'Download PDF', downloadCsv: 'Download CSV', records: 'records',
  noRecords: 'No saved records are available for this report yet.', backToReports: 'Back to reports',
  helpTitle: 'Harvesta Help Centre', helpIntro: 'A simple guide for using every important part of your smart farming workspace.',
  profileTitle: 'Farmer Profile', profileIntro: 'Manage the personal and farm details connected to your account.',
  fullName: 'Full name', email: 'Email address', phone: 'Phone number', address: 'Address', district: 'District',
  state: 'State', country: 'Country', bio: 'About you', primaryCrop: 'Primary crop', experience: 'Farming experience (years)',
  memberSince: 'Member since', verified: 'Verified account', accountRole: 'Account role',
  languageDesc: 'Changes navigation, settings, reports, inventory, profile, and assistant controls.',
  appearanceDesc: 'Select a comfortable display theme.', voiceDesc: 'Control Siri-style conversation in Harvesta AI.',
  compactDesc: 'Shows more information on laptop screens.', reduceMotionDesc: 'Limits animations and moving effects.',
  alertEmailDesc: 'Choose which farm and security alerts are sent to Gmail.', accountProfile: 'Account profile',
  accountProfileDesc: 'Update your name, farm experience, address, and personal details.', openNotificationSettings: 'Open notification settings',
  loadingSettings: 'Loading settings…', loadingProfile: 'Loading profile…', profileColour: 'Profile colour', profileBioHint: 'Tell Harvesta about your farm and goals.',
  stockControl: 'Stock control', totalQuantity: 'Total quantity', searchInventory: 'Search inventory', allCategories: 'All categories', alertLevel: 'Alert level', inventoryLabel: 'Inventory',
  privateFarmerData: 'Private farmer data', loadingReports: 'Loading reports…',
  farmOverviewTitle: 'Farm Overview', farmOverviewDesc: 'Registered fields, crops, land size, soil type, and farming method.',
  fieldAnalysisTitle: 'Field Analysis', fieldAnalysisDesc: 'Saved soil, crop, weather, recommendation, and priority readings.',
  irrigationHistoryTitle: 'Irrigation History', irrigationHistoryDesc: 'Field analyses where irrigation action was recommended.',
  diseaseScreeningTitle: 'Disease Screening', diseaseScreeningDesc: 'Crop image screening results and preliminary guidance.',
  activityHistoryTitle: 'Activity History', activityHistoryDesc: 'A privacy-safe record of features used in your Harvesta account.',
  gettingStarted: 'Getting started', startSixSteps: 'Start with these six steps', privateDataHelp: 'Your account data is private. Other farmers can only see and manage their own farms, inventory, scans, reports, and chat history. Only the Harvesta admin can open the separate Admin Portal.',
  guide1Title: '1. Add your farm and crops', guide1Text: 'Open Fields, add your farm location and size, then add each crop and its growth stage. This information improves AI guidance.',
  guide2Title: '2. Ask Harvesta AI', guide2Text: 'Type a question or tap the microphone for a live voice conversation. Speak naturally in your selected language. Tap End voice chat when finished.',
  guide3Title: '3. Screen a crop leaf', guide3Text: 'Open Disease Scan and upload a clear daylight photo. Treat the result as preliminary guidance and consult an agronomist for serious symptoms.',
  guide4Title: '4. Track supplies', guide4Text: 'Use Inventory to add seeds, fertilizer, tools and equipment. Set a low-stock level so Harvesta can highlight items that need attention.',
  guide5Title: '5. View and download reports', guide5Text: 'Reports contains five private summaries. Open any report to inspect the data, then download a PDF or CSV copy.',
  guide6Title: '6. Manage alerts', guide6Text: 'Open Alerts for farm and account notifications. Use Settings → Alert & email settings to choose which messages are sent to Gmail.',
  important: 'Important', helpDisclaimer: 'Harvesta AI and Disease Scan assist decision-making; they do not replace an on-site agronomist, laboratory test, or emergency advice.',
  loading: 'Loading…', notAvailable: 'Not available', plantedArea: 'Planted area', currentNpk: 'Current NPK', humidity: 'Humidity', forCultivation: 'for cultivation', soilMonitoring: 'Soil Monitoring', location: 'Location', loadingCrops: 'Loading crops…', noCropsAdded: 'No crops added', addCrop: 'Add crop',
  aiWorkspace: 'AI Analysis Workspace', aiWorkspaceIntro: 'run a field analysis or irrigation recommendation with real-time weather integration.', liveWeather: 'Live Weather', manual: 'Manual',
  yourFarm: 'Your Farm', myFarm: 'My Farm', manageCrops: 'Manage crops, growth stages and harvest projections.', farmOverview: 'Farm Overview', editFarm: 'Edit Farm', farmSize: 'Farm Size', soilType: 'Soil Type', farmingMethod: 'Farming Method', totalCrops: 'Total Crops', myCrops: 'My Crops', noCropsYet: 'No crops yet', noCropsHint: 'Add your first crop to start tracking its growth and health.', viewCrop: 'View Crop', variety: 'Variety', growthStage: 'Growth Stage', plantingDate: 'Planting Date', expectedHarvest: 'Expected Harvest', backDashboard: 'Back to Dashboard',
};

const ta = {
  dashboard: 'முகப்பு', fields: 'வயல்கள்', diseaseScan: 'பயிர் நோய் சோதனை', equipment: 'உபகரணங்கள்',
  climate: 'காலநிலை', alerts: 'எச்சரிக்கைகள்', inventory: 'இருப்புப் பொருட்கள்', reports: 'அறிக்கைகள்', help: 'உதவி',
  settings: 'அமைப்புகள்', adminPortal: 'நிர்வாகப் பகுதி', farmer: 'விவசாயி', admin: 'நிர்வாகி', profile: 'சுயவிவரம்',
  saveChanges: 'மாற்றங்களை சேமி', saving: 'சேமிக்கிறது…', saved: 'வெற்றிகரமாக சேமிக்கப்பட்டது', cancel: 'ரத்து செய்',
  language: 'மொழி', appearance: 'தோற்றம்', voiceAssistant: 'குரல் உதவியாளர்', preferences: 'விருப்பங்கள்',
  light: 'வெளிச்சம்', dark: 'இருள்', system: 'சாதன அமைப்பு', compactLayout: 'சுருக்கமான அமைப்பு', reduceMotion: 'அசைவைக் குறை',
  enableVoice: 'குரல் உரையாடலை இயக்கு', autoSpeak: 'AI பதில்களை குரலில் வாசி', notificationSettings: 'எச்சரிக்கை மற்றும் மின்னஞ்சல் அமைப்புகள்',
  settingsIntro: 'Harvesta எப்படி தோன்ற வேண்டும், பேச வேண்டும் என்பதைத் தேர்ந்தெடுக்கவும். இவை உங்கள் கணக்கில் சேமிக்கப்படும்.',
  askPlaceholder: 'நான் எப்படி உதவலாம்?', preparingAnswer: 'பதிலைத் தயாரிக்கிறது…',
  voiceListening: 'கேட்கிறது…', voiceSpeaking: 'Harvesta பேசுகிறது…', endVoice: 'குரல் உரையாடலை முடி', startVoice: 'நேரடி குரல் உரையாடலை தொடங்கு',
  aiDisclaimer: 'AI வழிகாட்டுதல் உறுதிப்படுத்தப்பட்ட வேளாண் நோயறிதல் அல்ல.',
  inventoryTitle: 'பண்ணை இருப்புப் பொருட்கள்', inventoryIntro: 'விதைகள், உரங்கள், கருவிகள் மற்றும் பண்ணைப் பொருட்களை நிர்வகிக்கவும்.',
  addItem: 'பொருள் சேர்', editItem: 'பொருளைத் திருத்து', itemName: 'பொருளின் பெயர்', category: 'வகை', quantity: 'அளவு',
  unit: 'அலகு', threshold: 'குறைந்த இருப்பு எச்சரிக்கை', supplier: 'விநியோகஸ்தர்', notes: 'குறிப்புகள்', lowStock: 'இருப்பு குறைவு',
  allItems: 'அனைத்தும்', noInventory: 'இன்னும் பொருட்கள் இல்லை. முதல் பொருளைச் சேர்க்கவும்.', delete: 'நீக்கு', edit: 'திருத்து',
  reportsTitle: 'அறிக்கை மையம்', reportsIntro: 'உங்கள் ஐந்து தனிப்பட்ட அறிக்கைகளைப் பார்த்து PDF அல்லது CSV ஆக பதிவிறக்கவும்.',
  viewReport: 'அறிக்கையைப் பார்', downloadPdf: 'PDF பதிவிறக்கம்', downloadCsv: 'CSV பதிவிறக்கம்', records: 'பதிவுகள்',
  noRecords: 'இந்த அறிக்கைக்கான சேமித்த பதிவுகள் இன்னும் இல்லை.', backToReports: 'அறிக்கைகளுக்குத் திரும்பு',
  helpTitle: 'Harvesta உதவி மையம்', helpIntro: 'உங்கள் ஸ்மார்ட் விவசாய பணியிடத்தின் முக்கிய அம்சங்களைப் பயன்படுத்த எளிய வழிகாட்டி.',
  profileTitle: 'விவசாயி சுயவிவரம்', profileIntro: 'உங்கள் கணக்குடன் இணைக்கப்பட்ட தனிப்பட்ட மற்றும் பண்ணை விவரங்களை நிர்வகிக்கவும்.',
  fullName: 'முழுப் பெயர்', email: 'மின்னஞ்சல்', phone: 'தொலைபேசி எண்', address: 'முகவரி', district: 'மாவட்டம்',
  state: 'மாநிலம்', country: 'நாடு', bio: 'உங்களைப் பற்றி', primaryCrop: 'முதன்மைப் பயிர்', experience: 'விவசாய அனுபவம் (ஆண்டுகள்)',
  memberSince: 'உறுப்பினரான நாள்', verified: 'சரிபார்க்கப்பட்ட கணக்கு', accountRole: 'கணக்கு வகை',
  languageDesc: 'வழிசெலுத்தல், அமைப்புகள், அறிக்கைகள், இருப்புப் பொருட்கள், சுயவிவரம் மற்றும் AI கட்டுப்பாடுகளின் மொழியை மாற்றும்.',
  appearanceDesc: 'உங்களுக்கு வசதியான காட்சி தோற்றத்தைத் தேர்ந்தெடுக்கவும்.', voiceDesc: 'Harvesta AI-யின் Siri போன்ற உரையாடலைக் கட்டுப்படுத்தவும்.',
  compactDesc: 'மடிக்கணினியில் அதிக தகவலைக் காட்டும்.', reduceMotionDesc: 'அசைவுகள் மற்றும் அனிமேஷன்களைக் குறைக்கும்.',
  alertEmailDesc: 'எந்த பண்ணை மற்றும் பாதுகாப்பு எச்சரிக்கைகள் Gmail-க்கு வர வேண்டும் என்பதைத் தேர்ந்தெடுக்கவும்.', accountProfile: 'கணக்கு சுயவிவரம்',
  accountProfileDesc: 'பெயர், அனுபவம், முகவரி மற்றும் தனிப்பட்ட விவரங்களைப் புதுப்பிக்கவும்.', openNotificationSettings: 'அறிவிப்பு அமைப்புகளைத் திற',
  loadingSettings: 'அமைப்புகள் ஏற்றப்படுகின்றன…', loadingProfile: 'சுயவிவரம் ஏற்றப்படுகிறது…', profileColour: 'சுயவிவர நிறம்', profileBioHint: 'உங்கள் பண்ணை மற்றும் இலக்குகளைப் பற்றி சொல்லுங்கள்.',
  stockControl: 'இருப்புக் கட்டுப்பாடு', totalQuantity: 'மொத்த அளவு', searchInventory: 'பொருட்களைத் தேடு', allCategories: 'அனைத்து வகைகள்', alertLevel: 'எச்சரிக்கை அளவு', inventoryLabel: 'இருப்புப் பொருட்கள்',
  privateFarmerData: 'தனிப்பட்ட விவசாயி தரவு', loadingReports: 'அறிக்கைகள் ஏற்றப்படுகின்றன…',
  farmOverviewTitle: 'பண்ணை மேலோட்டம்', farmOverviewDesc: 'பதிவு செய்த வயல்கள், பயிர்கள், நில அளவு, மண் வகை மற்றும் விவசாய முறை.',
  fieldAnalysisTitle: 'வயல் பகுப்பாய்வு', fieldAnalysisDesc: 'சேமித்த மண், பயிர், வானிலை, பரிந்துரை மற்றும் முன்னுரிமை பதிவுகள்.',
  irrigationHistoryTitle: 'நீர்ப்பாசன வரலாறு', irrigationHistoryDesc: 'நீர்ப்பாசனம் பரிந்துரைக்கப்பட்ட வயல் பகுப்பாய்வுகள்.',
  diseaseScreeningTitle: 'நோய் பரிசோதனை', diseaseScreeningDesc: 'பயிர் பட பரிசோதனை முடிவுகள் மற்றும் முதற்கட்ட வழிகாட்டுதல்.',
  activityHistoryTitle: 'செயல்பாட்டு வரலாறு', activityHistoryDesc: 'உங்கள் Harvesta கணக்கில் பயன்படுத்திய அம்சங்களின் தனியுரிமை பாதுகாப்பான பதிவு.',
  gettingStarted: 'தொடங்குவது எப்படி', startSixSteps: 'இந்த ஆறு படிகளுடன் தொடங்குங்கள்', privateDataHelp: 'உங்கள் கணக்கு தரவு தனிப்பட்டது. மற்ற விவசாயிகள் தங்கள் பண்ணைகள், பொருட்கள், சோதனைகள், அறிக்கைகள் மற்றும் அரட்டை வரலாற்றை மட்டுமே பார்க்க முடியும். Harvesta நிர்வாகி மட்டுமே நிர்வாகப் பகுதியைத் திறக்க முடியும்.',
  guide1Title: '1. பண்ணை மற்றும் பயிர்களைச் சேர்க்கவும்', guide1Text: 'வயல்கள் பகுதியைத் திறந்து பண்ணையின் இடம் மற்றும் அளவைச் சேர்க்கவும். பின்னர் ஒவ்வொரு பயிரையும் வளர்ச்சி நிலையுடன் சேர்க்கவும்.',
  guide2Title: '2. Harvesta AI-யிடம் கேளுங்கள்', guide2Text: 'கேள்வியைத் தட்டச்சு செய்யவும் அல்லது நேரடி குரல் உரையாடலுக்கு மைக்கைத் தட்டவும். தேர்ந்தெடுத்த மொழியில் இயல்பாகப் பேசுங்கள்.',
  guide3Title: '3. பயிர் இலையைச் சோதிக்கவும்', guide3Text: 'நோய் சோதனையைத் திறந்து பகல் வெளிச்சத்தில் எடுத்த தெளிவான படத்தை பதிவேற்றவும். கடுமையான அறிகுறிகளுக்கு வேளாண் நிபுணரை அணுகவும்.',
  guide4Title: '4. பொருட்களைக் கண்காணிக்கவும்', guide4Text: 'விதைகள், உரங்கள், கருவிகள் மற்றும் உபகரணங்களை இருப்புப் பகுதியில் சேர்க்கவும். குறைந்த இருப்பு எச்சரிக்கை அளவை அமைக்கவும்.',
  guide5Title: '5. அறிக்கைகளைப் பார்த்து பதிவிறக்கவும்', guide5Text: 'அறிக்கைகள் பகுதியில் ஐந்து தனிப்பட்ட சுருக்கங்கள் உள்ளன. அவற்றைத் திறந்து PDF அல்லது CSV ஆக பதிவிறக்கலாம்.',
  guide6Title: '6. எச்சரிக்கைகளை நிர்வகிக்கவும்', guide6Text: 'பண்ணை மற்றும் கணக்கு அறிவிப்புகளுக்கு எச்சரிக்கைகளைத் திறக்கவும். Gmail அமைப்புகளை Settings-ல் மாற்றலாம்.',
  important: 'முக்கியம்', helpDisclaimer: 'Harvesta AI மற்றும் நோய் சோதனை முடிவெடுக்க உதவும்; அவை நேரடி வேளாண் நிபுணர் அல்லது ஆய்வக சோதனைக்கு மாற்றாகாது.',
  loading: 'ஏற்றப்படுகிறது…', notAvailable: 'தகவல் இல்லை', plantedArea: 'பயிரிட்ட பரப்பு', currentNpk: 'தற்போதைய NPK', humidity: 'ஈரப்பதம்', forCultivation: 'சாகுபடிக்கு', soilMonitoring: 'மண் கண்காணிப்பு', location: 'இடம்', loadingCrops: 'பயிர்கள் ஏற்றப்படுகின்றன…', noCropsAdded: 'பயிர்கள் சேர்க்கப்படவில்லை', addCrop: 'பயிர் சேர்',
  aiWorkspace: 'AI பகுப்பாய்வு பணியிடம்', aiWorkspaceIntro: 'நேரடி வானிலையுடன் வயல் பகுப்பாய்வு அல்லது நீர்ப்பாசன பரிந்துரையை இயக்கவும்.', liveWeather: 'நேரடி வானிலை', manual: 'கைமுறை',
  yourFarm: 'உங்கள் பண்ணை', myFarm: 'என் பண்ணை', manageCrops: 'பயிர்கள், வளர்ச்சி நிலைகள் மற்றும் அறுவடைக் கணிப்புகளை நிர்வகிக்கவும்.', farmOverview: 'பண்ணை மேலோட்டம்', editFarm: 'பண்ணையைத் திருத்து', farmSize: 'பண்ணை அளவு', soilType: 'மண் வகை', farmingMethod: 'விவசாய முறை', totalCrops: 'மொத்த பயிர்கள்', myCrops: 'என் பயிர்கள்', noCropsYet: 'இன்னும் பயிர்கள் இல்லை', noCropsHint: 'வளர்ச்சி மற்றும் ஆரோக்கியத்தைக் கண்காணிக்க உங்கள் முதல் பயிரைச் சேர்க்கவும்.', viewCrop: 'பயிரைப் பார்', variety: 'ரகம்', growthStage: 'வளர்ச்சி நிலை', plantingDate: 'நடவு தேதி', expectedHarvest: 'எதிர்பார்க்கும் அறுவடை', backDashboard: 'முகப்பிற்குத் திரும்பு',
};

const hi = {
  dashboard: 'डैशबोर्ड', fields: 'खेत', diseaseScan: 'रोग स्कैन', equipment: 'उपकरण', climate: 'मौसम', alerts: 'अलर्ट',
  inventory: 'भंडार', reports: 'रिपोर्ट', help: 'सहायता', settings: 'सेटिंग्स', adminPortal: 'एडमिन पोर्टल',
  farmer: 'किसान', admin: 'एडमिन', profile: 'प्रोफ़ाइल', saveChanges: 'बदलाव सहेजें', saving: 'सहेज रहे हैं…', saved: 'सफलतापूर्वक सहेजा गया',
  language: 'भाषा', appearance: 'दिखावट', voiceAssistant: 'वॉइस सहायक', light: 'लाइट', dark: 'डार्क', system: 'सिस्टम',
  compactLayout: 'कॉम्पैक्ट लेआउट', reduceMotion: 'मोशन कम करें', enableVoice: 'वॉइस बातचीत चालू करें', autoSpeak: 'AI उत्तर बोलकर सुनाए',
  settingsIntro: 'Harvesta की भाषा, रूप और आवाज चुनें। आपकी पसंद खाते में सुरक्षित रहेगी।', askPlaceholder: 'मैं आपकी कैसे मदद कर सकता हूँ?',
  preparingAnswer: 'उत्तर तैयार हो रहा है…', voiceListening: 'सुन रहा हूँ…', voiceSpeaking: 'Harvesta बोल रहा है…', endVoice: 'वॉइस चैट बंद करें', startVoice: 'लाइव वॉइस चैट शुरू करें',
  inventoryTitle: 'फार्म इन्वेंटरी', inventoryIntro: 'बीज, खाद, औजार और अन्य सामान संभालें।', addItem: 'सामान जोड़ें', editItem: 'सामान बदलें',
  reportsTitle: 'रिपोर्ट केंद्र', reportsIntro: 'अपनी पाँच निजी रिपोर्ट देखें और PDF या CSV डाउनलोड करें।', viewReport: 'रिपोर्ट देखें',
  downloadPdf: 'PDF डाउनलोड', downloadCsv: 'CSV डाउनलोड', helpTitle: 'Harvesta सहायता केंद्र', profileTitle: 'किसान प्रोफ़ाइल',
};

const translations = { en, ta, hi };
const PreferencesContext = createContext(null);

export function PreferencesProvider({ children }) {
  const [preferences, setPreferences] = useState(() => {
    try {
      return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') };
    } catch {
      return DEFAULTS;
    }
  });

  const updateLocalPreferences = useCallback((updates) => {
    setPreferences((current) => ({ ...current, ...updates }));
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const applyTheme = () => {
      const theme = preferences.theme === 'system' ? (media.matches ? 'dark' : 'light') : preferences.theme;
      document.documentElement.dataset.theme = theme;
    };
    applyTheme();
    document.documentElement.lang = preferences.language;
    document.documentElement.dataset.density = preferences.compact_mode ? 'compact' : 'comfortable';
    document.documentElement.dataset.reduceMotion = preferences.reduce_motion ? 'true' : 'false';
    media.addEventListener?.('change', applyTheme);
    return () => media.removeEventListener?.('change', applyTheme);
  }, [preferences]);

  const dictionary = translations[preferences.language] || en;
  const t = useCallback((key) => dictionary[key] || en[key] || key, [dictionary]);
  const speechLocale = LANGUAGES.find((item) => item.code === preferences.language)?.speechLocale || 'en-IN';
  const value = useMemo(() => ({ preferences, updateLocalPreferences, t, speechLocale }), [preferences, updateLocalPreferences, t, speechLocale]);

  return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>;
}

export function usePreferences() {
  const context = useContext(PreferencesContext);
  if (!context) throw new Error('usePreferences must be used inside PreferencesProvider.');
  return context;
}
