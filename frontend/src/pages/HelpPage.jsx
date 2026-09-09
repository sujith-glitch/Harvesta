import { BellRing, Bot, Camera, CircleHelp, FileBarChart2, Package, Settings, Sprout } from 'lucide-react';
import { usePreferences } from '../context/PreferencesContext';

const GUIDES = [
  { icon: Sprout, title: 'guide1Title', text: 'guide1Text' }, { icon: Bot, title: 'guide2Title', text: 'guide2Text' },
  { icon: Camera, title: 'guide3Title', text: 'guide3Text' }, { icon: Package, title: 'guide4Title', text: 'guide4Text' },
  { icon: FileBarChart2, title: 'guide5Title', text: 'guide5Text' }, { icon: BellRing, title: 'guide6Title', text: 'guide6Text' },
];

export default function HelpPage({ onNavigate }) {
  const { t } = usePreferences();
  return <div className="page-shell utility-page">
    <header className="utility-header"><div><span className="eyebrow-text">{t('gettingStarted')}</span><h1><CircleHelp size={26} />{t('helpTitle')}</h1><p>{t('helpIntro')}</p></div><button type="button" className="btn-secondary" onClick={() => onNavigate('settings')}><Settings size={16} />{t('settings')}</button></header>
    <section className="help-hero analytic-card"><div><h2>{t('startSixSteps')}</h2><p>{t('privateDataHelp')}</p></div><span>6</span></section>
    <div className="help-grid">{GUIDES.map(({ icon: Icon, title, text }) => <article className="analytic-card help-card" key={title}><span><Icon size={21} /></span><h2>{t(title)}</h2><p>{t(text)}</p></article>)}</div>
    <section className="analytic-card help-note"><strong>{t('important')}:</strong> {t('helpDisclaimer')}</section>
  </div>;
}
