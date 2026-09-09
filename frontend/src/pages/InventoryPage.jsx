import { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Boxes, Edit3, Loader2, Package, Plus, Save, Search, Trash2, X } from 'lucide-react';
import { createInventoryItem, deleteInventoryItem, getInventory, updateInventoryItem } from '../services/api';
import { usePreferences } from '../context/PreferencesContext';

const CATEGORIES = ['Seeds', 'Fertilizer', 'Crop protection', 'Tools', 'Equipment', 'Other'];
const EMPTY = { name: '', category: 'Seeds', quantity: 0, unit: 'kg', low_stock_threshold: 0, supplier: '', notes: '' };

export default function InventoryPage() {
  const { t } = usePreferences();
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [lowOnly, setLowOnly] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setIsLoading(true); setError('');
    try { const result = await getInventory(); setItems(result.items || []); }
    catch (err) { setError(err.message || 'Could not load inventory.'); }
    finally { setIsLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const visible = useMemo(() => items.filter((item) => {
    const textMatch = `${item.name} ${item.supplier || ''}`.toLowerCase().includes(query.toLowerCase());
    return textMatch && (!category || item.category === category) && (!lowOnly || item.is_low_stock);
  }), [items, query, category, lowOnly]);

  const openCreate = () => { setEditingId(null); setForm(EMPTY); setFormOpen(true); };
  const openEdit = (item) => { setEditingId(item.id); setForm({ ...EMPTY, ...item, supplier: item.supplier || '', notes: item.notes || '' }); setFormOpen(true); };
  const closeForm = () => { setFormOpen(false); setEditingId(null); setForm(EMPTY); };
  const set = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));

  const save = async (event) => {
    event.preventDefault(); setIsSaving(true); setError('');
    const payload = { ...form, quantity: Number(form.quantity), low_stock_threshold: Number(form.low_stock_threshold), supplier: form.supplier || null, notes: form.notes || null };
    try {
      if (editingId) await updateInventoryItem(editingId, payload); else await createInventoryItem(payload);
      closeForm(); await load();
    } catch (err) { setError(err.message || 'Could not save item.'); }
    finally { setIsSaving(false); }
  };

  const remove = async (item) => {
    if (!window.confirm(`Delete ${item.name} from inventory?`)) return;
    try { await deleteInventoryItem(item.id); setItems((current) => current.filter((entry) => entry.id !== item.id)); }
    catch (err) { setError(err.message || 'Could not delete item.'); }
  };

  const totalQuantity = items.reduce((sum, item) => sum + Number(item.quantity || 0), 0);
  const lowCount = items.filter((item) => item.is_low_stock).length;

  return (
    <div className="page-shell utility-page">
      <header className="utility-header">
        <div><span className="eyebrow-text">{t('stockControl')}</span><h1><Boxes size={26} /> {t('inventoryTitle')}</h1><p>{t('inventoryIntro')}</p></div>
        <button type="button" className="btn-primary" onClick={openCreate}><Plus size={17} />{t('addItem')}</button>
      </header>
      {error && <div className="status-banner error">{error}</div>}

      <div className="inventory-summary-grid">
        <div className="analytic-card inventory-stat"><Package /><span><strong>{items.length}</strong><small>{t('allItems')}</small></span></div>
        <div className="analytic-card inventory-stat"><AlertTriangle /><span><strong>{lowCount}</strong><small>{t('lowStock')}</small></span></div>
        <div className="analytic-card inventory-stat"><Boxes /><span><strong>{totalQuantity.toLocaleString()}</strong><small>{t('totalQuantity')}</small></span></div>
      </div>

      <section className="analytic-card inventory-workspace">
        <div className="inventory-toolbar">
          <div className="search-field"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t('searchInventory')} /></div>
          <select className="harvesta-input" value={category} onChange={(event) => setCategory(event.target.value)}><option value="">{t('allCategories')}</option>{CATEGORIES.map((item) => <option key={item}>{item}</option>)}</select>
          <label className="filter-checkbox"><input type="checkbox" checked={lowOnly} onChange={(event) => setLowOnly(event.target.checked)} />{t('lowStock')}</label>
        </div>
        {isLoading ? <div className="utility-loading"><Loader2 className="animate-spin" /> Loading inventory…</div> : visible.length === 0 ? (
          <div className="empty-utility"><Package size={34} /><h3>{t('noInventory')}</h3><button type="button" className="btn-secondary" onClick={openCreate}>{t('addItem')}</button></div>
        ) : (
          <div className="inventory-card-grid">
            {visible.map((item) => (
              <article key={item.id} className={`inventory-item-card ${item.is_low_stock ? 'low' : ''}`}>
                <div className="inventory-item-top"><span className="inventory-category">{item.category}</span>{item.is_low_stock && <span className="low-badge"><AlertTriangle size={12} />{t('lowStock')}</span>}</div>
                <h3>{item.name}</h3><div className="inventory-quantity"><strong>{item.quantity}</strong><span>{item.unit}</span></div>
                <dl><div><dt>{t('alertLevel')}</dt><dd>{item.low_stock_threshold} {item.unit}</dd></div><div><dt>{t('supplier')}</dt><dd>{item.supplier || '—'}</dd></div></dl>
                {item.notes && <p>{item.notes}</p>}
                <div className="inventory-actions"><button type="button" onClick={() => openEdit(item)}><Edit3 size={15} />{t('edit')}</button><button type="button" className="danger" onClick={() => remove(item)}><Trash2 size={15} />{t('delete')}</button></div>
              </article>
            ))}
          </div>
        )}
      </section>

      {formOpen && <div className="utility-modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && closeForm()}>
        <form className="utility-modal" onSubmit={save}>
          <div className="modal-heading"><div><span className="eyebrow-text">{t('inventoryLabel')}</span><h2>{editingId ? t('editItem') : t('addItem')}</h2></div><button type="button" onClick={closeForm} aria-label="Close"><X size={19} /></button></div>
          <div className="profile-form-grid">
            <label className="span-all"><span>{t('itemName')}</span><input className="harvesta-input" value={form.name} onChange={set('name')} required /></label>
            <label><span>{t('category')}</span><select className="harvesta-input" value={form.category} onChange={set('category')}>{CATEGORIES.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label><span>{t('unit')}</span><input className="harvesta-input" value={form.unit} onChange={set('unit')} required /></label>
            <label><span>{t('quantity')}</span><input className="harvesta-input" type="number" step="0.01" min="0" value={form.quantity} onChange={set('quantity')} /></label>
            <label><span>{t('threshold')}</span><input className="harvesta-input" type="number" step="0.01" min="0" value={form.low_stock_threshold} onChange={set('low_stock_threshold')} /></label>
            <label className="span-all"><span>{t('supplier')}</span><input className="harvesta-input" value={form.supplier} onChange={set('supplier')} /></label>
            <label className="span-all"><span>{t('notes')}</span><textarea className="harvesta-input" rows="3" value={form.notes} onChange={set('notes')} /></label>
          </div>
          <div className="form-actions"><button type="button" className="btn-secondary" onClick={closeForm}>{t('cancel')}</button><button type="submit" className="btn-primary" disabled={isSaving}>{isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}{t('saveChanges')}</button></div>
        </form>
      </div>}
    </div>
  );
}
