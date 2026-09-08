import { useEffect, useState } from 'react';
import { Activity, ArrowLeft, Download, FileBarChart2, FileSpreadsheet, Loader2, ScanLine, Sprout, Waves } from 'lucide-react';
import { downloadReport, getReport, getReports } from '../services/api';
import { usePreferences } from '../context/PreferencesContext';

const ICONS = { 'farm-overview': Sprout, 'field-analysis': FileBarChart2, 'irrigation-history': Waves, 'disease-screening': ScanLine, 'activity-history': Activity };
const REPORT_TEXT = {
  'farm-overview': ['farmOverviewTitle', 'farmOverviewDesc'],
  'field-analysis': ['fieldAnalysisTitle', 'fieldAnalysisDesc'],
  'irrigation-history': ['irrigationHistoryTitle', 'irrigationHistoryDesc'],
  'disease-screening': ['diseaseScreeningTitle', 'diseaseScreeningDesc'],
  'activity-history': ['activityHistoryTitle', 'activityHistoryDesc'],
};

export default function ReportsPage() {
  const { t } = usePreferences();
  const [reports, setReports] = useState([]);
  const [selected, setSelected] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    getReports().then((data) => setReports(data.reports || [])).catch((err) => setError(err.message || 'Could not load reports.')).finally(() => setIsLoading(false));
  }, []);

  const view = async (key) => {
    setBusy(`view-${key}`); setError('');
    try { setSelected(await getReport(key)); }
    catch (err) { setError(err.message || 'Could not open report.'); }
    finally { setBusy(''); }
  };

  const download = async (key, format) => {
    setBusy(`${format}-${key}`); setError('');
    try {
      const result = await downloadReport(key, format);
      const url = URL.createObjectURL(result.blob);
      const anchor = document.createElement('a'); anchor.href = url; anchor.download = result.filename; anchor.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) { setError(err.message || 'Could not download report.'); }
    finally { setBusy(''); }
  };

  if (selected) {
    return <div className="page-shell utility-page">
      <header className="utility-header"><div><button type="button" className="text-back" onClick={() => setSelected(null)}><ArrowLeft size={16} />{t('backToReports')}</button><h1><FileBarChart2 size={26} />{t(REPORT_TEXT[selected.key]?.[0])}</h1><p>{t(REPORT_TEXT[selected.key]?.[1])} · {selected.record_count} {t('records')}</p></div><div className="report-download-actions"><button type="button" className="btn-secondary" onClick={() => download(selected.key, 'csv')}><FileSpreadsheet size={16} />{t('downloadCsv')}</button><button type="button" className="btn-primary" onClick={() => download(selected.key, 'pdf')}><Download size={16} />{t('downloadPdf')}</button></div></header>
      {error && <div className="status-banner error">{error}</div>}
      <section className="analytic-card report-table-card">
        {selected.rows.length === 0 ? <div className="empty-utility"><FileBarChart2 size={34} /><h3>{t('noRecords')}</h3></div> : <div className="data-table-wrap"><table className="harvesta-data-table"><thead><tr>{selected.columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr></thead><tbody>{selected.rows.map((row, index) => <tr key={index}>{selected.columns.map((column) => <td key={column.key}>{row[column.key] ?? '—'}</td>)}</tr>)}</tbody></table></div>}
      </section>
    </div>;
  }

  return <div className="page-shell utility-page">
    <header className="utility-header"><div><span className="eyebrow-text">{t('privateFarmerData')}</span><h1><FileBarChart2 size={26} />{t('reportsTitle')}</h1><p>{t('reportsIntro')}</p></div></header>
    {error && <div className="status-banner error">{error}</div>}
    {isLoading ? <div className="analytic-card utility-loading"><Loader2 className="animate-spin" />{t('loadingReports')}</div> : <div className="reports-grid">{reports.map((report) => { const Icon = ICONS[report.key] || FileBarChart2; return <article className="analytic-card report-card" key={report.key}><span className="report-icon"><Icon size={22} /></span><div><h2>{t(REPORT_TEXT[report.key]?.[0])}</h2><p>{t(REPORT_TEXT[report.key]?.[1])}</p></div><div className="report-count"><strong>{report.record_count}</strong><span>{t('records')}</span></div><div className="report-card-actions"><button type="button" className="btn-secondary" onClick={() => view(report.key)} disabled={Boolean(busy)}>{busy === `view-${report.key}` ? <Loader2 size={15} className="animate-spin" /> : null}{t('viewReport')}</button><button type="button" className="icon-download" onClick={() => download(report.key, 'pdf')} disabled={Boolean(busy)} title={t('downloadPdf')}><Download size={17} /></button></div></article>; })}</div>}
  </div>;
}
